from flask import Blueprint, jsonify

from app.services.news_service import get_headlines

news_bp = Blueprint("news", __name__)


@news_bp.route("/news")
def news():
    data = get_headlines()
    return jsonify(data)
