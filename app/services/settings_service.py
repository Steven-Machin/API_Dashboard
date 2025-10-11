from __future__ import annotations

from flask import g
from flask_login import current_user

from app.extensions import db
from app.models import UserSettings


def get_user_settings() -> UserSettings:
    """Return the authenticated user's settings, creating defaults if missing."""
    if not current_user.is_authenticated:
        raise RuntimeError("Cannot access user settings for anonymous user.")

    cached = getattr(g, "_user_settings", None)
    if cached and isinstance(cached, UserSettings):
        return cached

    settings = getattr(current_user, "settings", None)
    if not settings:
        settings = UserSettings(user=current_user)
        db.session.add(settings)
        db.session.commit()

    g._user_settings = settings
    return settings
