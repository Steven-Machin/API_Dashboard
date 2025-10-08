from flask import Blueprint, render_template

from app.services.crypto_service import get_crypto_prices
from app.services.news_service import get_headlines
from app.services.weather_service import get_weather_forecast

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    # Fetch sample data for dashboard cards; failures fall back to placeholders.
    crypto_data = get_crypto_prices()
    weather_data = get_weather_forecast()
    news_data = get_headlines()

    crypto_cards = [
        {"symbol": symbol, "usd": details.get("usd")}
        for symbol, details in crypto_data.items()
    ]
    weather_summary = {
        "city": weather_data.get("name"),
        "temperature": weather_data.get("main", {}).get("temp"),
        "humidity": weather_data.get("main", {}).get("humidity"),
        "wind_speed": weather_data.get("wind", {}).get("speed"),
        "description": (
            (weather_data.get("weather") or [{}])[0].get("description", "Unknown")
        ),
    }

    return render_template(
        "index.html",
        crypto_cards=crypto_cards,
        weather=weather_summary,
        news_items=news_data,
    )
