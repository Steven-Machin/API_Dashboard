from __future__ import annotations

import atexit
import os
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask

from app.services.notification_service import send_daily_summary

_scheduler: BackgroundScheduler | None = None


def _safe_int(value: str | None, default: int) -> int:
    if not value:
        return default
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _build_job(app: Flask) -> Callable[[], None]:
    def _job() -> None:
        with app.app_context():
            try:
                send_daily_summary()
            except Exception:
                app.logger.exception("Daily summary job failed.")

    return _job


def start_scheduler(app: Flask) -> None:
    """Start the APScheduler background scheduler if enabled."""
    global _scheduler

    if not app.config.get("ENABLE_DAILY_SUMMARY", True):
        app.logger.info("Daily summary scheduler disabled via configuration.")
        return

    if _scheduler and _scheduler.running:
        app.logger.debug("Daily summary scheduler already running; skipping init.")
        return

    # Avoid spawning duplicate schedulers when the reloader boots the stub process.
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        app.logger.debug("Deferring scheduler start until reloader child process.")
        return

    hour = _safe_int(os.environ.get("DAILY_SUMMARY_HOUR"), default=8)
    minute = _safe_int(os.environ.get("DAILY_SUMMARY_MINUTE"), default=0)
    timezone = app.config.get("SCHEDULER_TIMEZONE", "UTC")

    scheduler = BackgroundScheduler(timezone=timezone)
    scheduler.add_job(
        func=_build_job(app),
        trigger=CronTrigger(hour=hour, minute=minute),
        id="daily-summary",
        replace_existing=True,
    )
    scheduler.start()

    _scheduler = scheduler
    app.logger.info(
        "Daily summary scheduler started (cron=%02d:%02d %s).", hour, minute, timezone
    )


def _shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None


atexit.register(_shutdown_scheduler)
