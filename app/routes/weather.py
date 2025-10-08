from flask import Blueprint, jsonify

from app.services.weather_service import get_weather_forecast

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/weather")
def weather():
    data = get_weather_forecast()
    return jsonify(data)
