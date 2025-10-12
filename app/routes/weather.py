from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.services.settings_service import get_user_settings
from app.services.weather_service import get_weather_forecast

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/weather")
@login_required
def weather():
    settings = get_user_settings()
    requested_city = (request.args.get("city") or "").strip()
    target_city = requested_city or settings.default_city
    data = get_weather_forecast(target_city)
    main = data.get("main", {}) if isinstance(data, dict) else {}
    wind = data.get("wind", {}) if isinstance(data, dict) else {}
    weather_list = data.get("weather") if isinstance(data, dict) else []
    primary = weather_list[0] if weather_list else {}

    payload = {
        "city": data.get("name") if isinstance(data, dict) else None,
        "temperature": main.get("temp"),
        "condition": (primary.get("description") or primary.get("main", "")),
        "humidity": main.get("humidity"),
        "wind_speed": wind.get("speed"),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(payload)
