from __future__ import annotations

import os
from typing import Dict, List

import requests
from flask import current_app
from requests import RequestException, Response

from app.services.history_service import calculate_crypto_change, calculate_weather_average
from app.services.news_service import get_headlines

_HEADLINE_LIMIT = 3
_DEFAULT_WEBHOOK_ENV = "DAILY_SUMMARY_WEBHOOK_URL"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "unavailable"
    return f"{value:+.2f}%"


def _format_temperature(value: float | None) -> str:
    if value is None:
        return "unavailable"
    return f"{value:.1f}°"


def _build_headline_lines(headlines: List[Dict[str, str]]) -> List[str]:
    lines: List[str] = []
    if not headlines:
        lines.append("Top headlines: unavailable")
        return lines

    lines.append("Top headlines:")
    for idx, article in enumerate(headlines[:_HEADLINE_LIMIT], start=1):
        title = article.get("title") or "Untitled"
        source = article.get("source") or ""
        url = article.get("url") or ""

        if source:
            label = f"{title} — {source}"
        else:
            label = title

        if url:
            lines.append(f"{idx}. {label} ({url})")
        else:
            lines.append(f"{idx}. {label}")
    return lines


def compose_daily_summary() -> str:
    """Build the textual summary that will be delivered to external channels."""
    crypto_metrics = calculate_crypto_change(hours=24)
    weather_metrics = calculate_weather_average(days=1)
    headlines = get_headlines()

    lines = ["**Daily Dashboard Summary**"]
    lines.append(
        f"• Bitcoin 24h change: {_format_percent(crypto_metrics.get('bitcoin_change_pct'))}"
    )
    lines.append(
        f"• Ethereum 24h change: {_format_percent(crypto_metrics.get('ethereum_change_pct'))}"
    )
    lines.append(
        f"• Average temperature (24h): {_format_temperature(weather_metrics.get('average_temperature'))}"
    )

    lines.extend([""] + _build_headline_lines(headlines))
    return "\n".join(lines).strip()


def _resolve_webhook_url() -> str | None:
    url = os.environ.get(_DEFAULT_WEBHOOK_ENV)
    if url:
        return url.strip()

    fallback = current_app.config.get("DAILY_SUMMARY_WEBHOOK_URL")
    if isinstance(fallback, str) and fallback.strip():
        return fallback.strip()
    return None


def send_daily_summary() -> None:
    """Deliver the daily update to the configured Discord webhook."""
    app = current_app._get_current_object()
    logger = app.logger

    webhook_url = _resolve_webhook_url()
    if not webhook_url:
        logger.warning(
            "Daily summary webhook URL not configured; skipping notification."
        )
        return

    payload = compose_daily_summary()
    logger.info("Dispatching daily summary (%d characters).", len(payload))

    try:
        response: Response = requests.post(
            webhook_url, json={"content": payload}, timeout=10
        )
        if response.status_code >= 400:
            logger.error(
                "Daily summary webhook failed with status %s: %s",
                response.status_code,
                response.text[:200],
            )
        else:
            logger.info("Daily summary sent successfully.")
    except RequestException as exc:
        logger.exception("Failed to send daily summary: %s", exc)
