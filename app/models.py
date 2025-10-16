from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from flask_login import UserMixin

from .extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)

    settings = db.relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class UserSettings(db.Model):
    __tablename__ = "user_settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True
    )
    show_crypto = db.Column(db.Boolean, nullable=False, default=True)
    show_weather = db.Column(db.Boolean, nullable=False, default=True)
    show_news = db.Column(db.Boolean, nullable=False, default=True)
    default_city = db.Column(db.String(128), nullable=False, default="Chicago")
    refresh_interval = db.Column(db.Integer, nullable=False, default=5)

    user = db.relationship("User", back_populates="settings")

    @classmethod
    def ensure_for_user(cls, user: User) -> "UserSettings":
        settings: Optional["UserSettings"] = getattr(user, "settings", None)
        if settings:
            return settings

        settings = cls(user=user)
        db.session.add(settings)
        db.session.commit()
        return settings

    def __repr__(self) -> str:
        return f"<UserSettings user_id={self.user_id} refresh_interval={self.refresh_interval}>"

    def to_dict(self) -> dict:
        return {
            "show_crypto": self.show_crypto,
            "show_weather": self.show_weather,
            "show_news": self.show_news,
            "default_city": self.default_city,
            "refresh_interval": self.refresh_interval,
        }


class CryptoHistory(db.Model):
    """Persist a point-in-time snapshot of crypto prices for trend tracking."""

    __tablename__ = "crypto_history"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    bitcoin_price = db.Column(db.Float, nullable=False)
    ethereum_price = db.Column(db.Float, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<CryptoHistory id={self.id} timestamp={self.timestamp.isoformat()} "
            f"btc={self.bitcoin_price} eth={self.ethereum_price}>"
        )


class WeatherHistory(db.Model):
    """Capture weather readings so the dashboard can display recent history."""

    __tablename__ = "weather_history"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    temperature = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(128), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<WeatherHistory id={self.id} timestamp={self.timestamp.isoformat()} "
            f"temp={self.temperature} condition={self.condition!r}>"
        )
