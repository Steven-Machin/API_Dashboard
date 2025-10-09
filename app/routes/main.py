from datetime import datetime, timezone

from flask import Blueprint, render_template

from app.services.crypto_service import get_crypto_prices
from app.services.news_service import get_headlines
from app.services.weather_service import get_weather_forecast

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    crypto_prices = get_crypto_prices()
    weather_data = get_weather_forecast()
    news_headlines = get_headlines()
    current_timestamp = datetime.now(timezone.utc)

    return render_template(
        "index.html",
        crypto_prices=crypto_prices,
        crypto_last_updated=current_timestamp,
        weather_data=weather_data,
        weather_last_updated=current_timestamp,
        news_headlines=news_headlines,
        news_last_updated=current_timestamp,
    )
