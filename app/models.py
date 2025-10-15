from __future__ import annotations

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
