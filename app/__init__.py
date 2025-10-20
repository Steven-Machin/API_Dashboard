from __future__ import annotations

import os

from flask import Flask

from .extensions import db, login_manager, migrate
from .models import User
from .routes.auth import auth_bp
from .routes.crypto import crypto_bp
from .routes.main import main_bp
from .routes.news import news_bp
from .routes.weather import weather_bp
from .scheduler import start_scheduler
from config import APP_VERSION


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def create_app() -> Flask:
    """Application factory that wires Blueprints together."""
    app = Flask(__name__)

    app.config.setdefault("APP_VERSION", APP_VERSION)
    app.config.setdefault(
        "SECRET_KEY", os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    )
    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI", os.environ.get("DATABASE_URL", "sqlite:///app.db")
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault(
        "ENABLE_DAILY_SUMMARY", _env_flag("ENABLE_DAILY_SUMMARY", default=True)
    )
    app.config.setdefault(
        "SCHEDULER_TIMEZONE", os.environ.get("SCHEDULER_TIMEZONE", "UTC")
    )

    webhook_url = os.environ.get("DAILY_SUMMARY_WEBHOOK_URL")
    if webhook_url:
        app.config.setdefault("DAILY_SUMMARY_WEBHOOK_URL", webhook_url)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    migrate.init_app(app, db)

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

    @app.context_processor
    def inject_version() -> dict[str, str | None]:
        return {"app_version": app.config.get("APP_VERSION")}

    start_scheduler(app)

    return app
