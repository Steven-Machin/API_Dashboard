"""Provide headline data endpoints for the dashboard."""

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify
from flask_login import login_required

from app.services.news_service import get_headlines

news_bp = Blueprint("news", __name__)


@news_bp.route("/news")
@login_required
def news():
    try:
        headlines = get_headlines() or []
    except Exception as exc:  # pragma: no cover - defensive
        current_app.logger.exception("Failed to fetch news headlines")
        return (
            jsonify(
                {
                    "headlines": [],
                    "error": "News data unavailable",
                    "details": str(exc),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    if not isinstance(headlines, list):
        headlines = []

    payload = {
        "headlines": headlines[:5],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(payload)
