from __future__ import annotations

import os

from flask import Flask

from .extensions import db, login_manager
from .models import User
from .routes.auth import auth_bp
from .routes.crypto import crypto_bp
from .routes.main import main_bp
from .routes.news import news_bp
from .routes.weather import weather_bp


def create_app() -> Flask:
    """Application factory that wires Blueprints together."""
    app = Flask(__name__)

    app.config.setdefault(
        "SECRET_KEY", os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    )
    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI", os.environ.get("DATABASE_URL", "sqlite:///app.db")
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        if not user_id:
            return None
        return db.session.get(User, int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(crypto_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(news_bp)

    with app.app_context():
        db.create_all()

    return app
