from flask import Flask

from .routes.crypto import crypto_bp
from .routes.main import main_bp
from .routes.news import news_bp
from .routes.weather import weather_bp


def create_app() -> Flask:
    """Application factory that wires Blueprints together."""
    app = Flask(__name__)

    app.register_blueprint(main_bp)
    app.register_blueprint(crypto_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(news_bp)

    return app
