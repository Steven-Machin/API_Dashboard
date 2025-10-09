from datetime import datetime, timezone

from flask import Blueprint, jsonify

from app.services.news_service import get_headlines

news_bp = Blueprint("news", __name__)


@news_bp.route("/news")
def news():
    headlines = get_headlines()
    payload = {
        "headlines": headlines[:5],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(payload)
