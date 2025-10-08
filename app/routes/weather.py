from datetime import datetime, timezone

from flask import Blueprint, jsonify

from app.services.weather_service import get_weather_forecast

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/weather")
def weather():
    data = get_weather_forecast()
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
