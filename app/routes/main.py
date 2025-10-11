from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.services.crypto_service import get_crypto_prices
from app.services.news_service import get_headlines
from app.services.settings_service import get_user_settings
from app.services.weather_service import get_weather_forecast

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    settings = get_user_settings()

    crypto_prices: Dict[str, Any] | None = None
    crypto_timestamp = None
    if settings.show_crypto:
        crypto_prices = get_crypto_prices()
        crypto_timestamp = datetime.now(timezone.utc)

    weather_data: Dict[str, Any] | None = None
    weather_timestamp = None
    if settings.show_weather:
        weather_data = get_weather_forecast(settings.default_city)
        weather_timestamp = datetime.now(timezone.utc)

    news_headlines: List[Dict[str, Any]] | None = None
    news_timestamp = None
    if settings.show_news:
        news_headlines = get_headlines()
        news_timestamp = datetime.now(timezone.utc)

    return render_template(
        "index.html",
        current_user=current_user,
        show_crypto=settings.show_crypto,
        show_weather=settings.show_weather,
        show_news=settings.show_news,
        default_city=settings.default_city,
        auto_refresh_minutes=max(settings.refresh_interval, 1),
        crypto_prices=crypto_prices,
        crypto_last_updated=crypto_timestamp,
        weather_data=weather_data,
        weather_last_updated=weather_timestamp,
        news_headlines=news_headlines,
        news_last_updated=news_timestamp,
    )


@main_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    settings = get_user_settings()

    if request.method == "POST":
        show_crypto = bool(request.form.get("show_crypto"))
        show_weather = bool(request.form.get("show_weather"))
        show_news = bool(request.form.get("show_news"))
        default_city = (request.form.get("default_city") or "").strip() or "Chicago"

        try:
            refresh_interval = int(request.form.get("auto_refresh_interval") or settings.refresh_interval)
        except (TypeError, ValueError):
            refresh_interval = settings.refresh_interval

        refresh_interval = max(refresh_interval, 1)

        settings.show_crypto = show_crypto
        settings.show_weather = show_weather
        settings.show_news = show_news
        settings.default_city = default_city
        settings.refresh_interval = refresh_interval

        db.session.commit()
        g._user_settings = settings

        flash("Settings saved successfully.", "success")
        return redirect(url_for("main.settings"))

    return render_template("settings.html", settings=settings, current_user=current_user)
