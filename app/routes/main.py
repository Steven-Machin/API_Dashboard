"""Core dashboard views and settings APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import (
    Blueprint,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.extensions import db
from app.services.crypto_service import get_crypto_prices
from app.services.news_service import get_headlines
from app.services.settings_service import get_user_settings
from app.services.weather_service import get_weather_forecast
from app.services.history_service import get_crypto_history, get_weather_history

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
        settings=settings,
        settings_payload=settings.to_dict(),
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
            refresh_interval = int(
                request.form.get("auto_refresh_interval") or settings.refresh_interval
            )
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

    return render_template(
        "settings.html", settings=settings, current_user=current_user
    )


@main_bp.route("/insights")
@login_required
def insights():
    """Render the insights dashboard with trend placeholders."""
    return render_template("insights.html")


@main_bp.route("/api/crypto_history")
@login_required
def api_crypto_history():
    """Expose the recent crypto history entries for chart rendering."""
    payload = get_crypto_history()
    return jsonify({"data": payload, "count": len(payload)})


@main_bp.route("/api/weather_history")
@login_required
def api_weather_history():
    """Expose the recent weather history entries for chart rendering."""
    payload = get_weather_history()
    return jsonify({"data": payload, "count": len(payload)})


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "on", "yes"}
    return bool(value)


@main_bp.route("/api/settings", methods=["PATCH"])
@login_required
def update_settings_api():
    if not request.is_json:
        return jsonify({"error": "Expected JSON payload."}), 400

    settings = get_user_settings()
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload."}), 400

    updated_fields: Dict[str, Any] = {}

    if "show_crypto" in payload:
        settings.show_crypto = _coerce_bool(payload["show_crypto"])
        updated_fields["show_crypto"] = settings.show_crypto

    if "show_weather" in payload:
        settings.show_weather = _coerce_bool(payload["show_weather"])
        updated_fields["show_weather"] = settings.show_weather

    if "show_news" in payload:
        settings.show_news = _coerce_bool(payload["show_news"])
        updated_fields["show_news"] = settings.show_news

    if "default_city" in payload:
        default_city = str(payload["default_city"] or "").strip() or "Chicago"
        settings.default_city = default_city
        updated_fields["default_city"] = default_city

    if "refresh_interval" in payload:
        try:
            refresh_interval = max(int(payload["refresh_interval"]), 1)
        except (TypeError, ValueError):
            return (
                jsonify({"error": "refresh_interval must be an integer value >= 1."}),
                400,
            )
        settings.refresh_interval = refresh_interval
        updated_fields["refresh_interval"] = refresh_interval

    if not updated_fields:
        return jsonify({"settings": settings.to_dict(), "updated": {}}), 200

    db.session.commit()
    g._user_settings = settings

    return jsonify({"settings": settings.to_dict(), "updated": updated_fields}), 200
