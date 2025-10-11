from datetime import datetime, timezone

from flask import Blueprint, jsonify
from flask_login import login_required

from app.services.crypto_service import get_crypto_prices

crypto_bp = Blueprint("crypto", __name__)


@crypto_bp.route("/crypto")
@login_required
def crypto():
    data = get_crypto_prices()
    payload = {
        "bitcoin": data.get("bitcoin", {}),
        "ethereum": data.get("ethereum", {}),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(payload)
