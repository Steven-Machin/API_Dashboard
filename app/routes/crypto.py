from flask import Blueprint, jsonify

from app.services.crypto_service import get_crypto_prices

crypto_bp = Blueprint("crypto", __name__)


@crypto_bp.route("/crypto")
def crypto():
    data = get_crypto_prices()
    return jsonify(data)
