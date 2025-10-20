"""Serve weather forecast data for the dashboard."""

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required

from app.services.settings_service import get_user_settings
from app.services.weather_service import get_weather_forecast
from app.services.history_service import save_weather_data

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/weather")
@login_required
def weather():
    settings = get_user_settings()
    requested_city = (request.args.get("city") or "").strip()
    target_city = requested_city or settings.default_city
    try:
        data = get_weather_forecast(target_city) or {}
    except Exception as exc:  # pragma: no cover - defensive
        current_app.logger.exception("Failed to fetch weather data")
        return (
            jsonify(
                {
                    "city": target_city or settings.default_city,
                    "temperature": None,
                    "condition": None,
                    "humidity": None,
                    "wind_speed": None,
                    "error": "Weather data unavailable",
                    "details": str(exc),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    if not isinstance(data, dict):
        data = {}

    main = data.get("main", {}) if isinstance(data, dict) else {}
    wind = data.get("wind", {}) if isinstance(data, dict) else {}
    weather_list = data.get("weather") if isinstance(data, dict) else []
    primary = weather_list[0] if weather_list else {}

    temperature = main.get("temp")
    condition = primary.get("description") or primary.get("main", "")

    payload = {
        "city": data.get("name") if isinstance(data, dict) else None,
        "temperature": temperature,
        "condition": condition,
        "humidity": main.get("humidity"),
        "wind_speed": wind.get("speed"),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

    # Record the weather snapshot when the API (or fallback) returns the essentials.
    if isinstance(temperature, (int, float)) and condition:
        save_weather_data(temperature, condition)

    return jsonify(payload)
