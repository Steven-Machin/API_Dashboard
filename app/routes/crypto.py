"""Expose cryptocurrency pricing endpoints for the dashboard."""

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify
from flask_login import login_required

from app.services.crypto_service import get_crypto_prices
from app.services.history_service import save_crypto_data

crypto_bp = Blueprint("crypto", __name__)


@crypto_bp.route("/crypto")
@login_required
def crypto():
    try:
        data = get_crypto_prices() or {}
    except Exception as exc:  # pragma: no cover - defensive
        current_app.logger.exception("Failed to fetch crypto prices")
        return (
            jsonify(
                {
                    "bitcoin": {},
                    "ethereum": {},
                    "error": "Crypto data unavailable",
                    "details": str(exc),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    if not isinstance(data, dict):
        data = {}

    bitcoin_price = data.get("bitcoin", {}).get("usd")
    ethereum_price = data.get("ethereum", {}).get("usd")

    # Persist a snapshot any time the upstream call returns both price points.
    if isinstance(bitcoin_price, (int, float)) and isinstance(
        ethereum_price, (int, float)
    ):
        save_crypto_data(bitcoin_price, ethereum_price)

    payload = {
        "bitcoin": data.get("bitcoin", {}) if isinstance(data, dict) else {},
        "ethereum": data.get("ethereum", {}) if isinstance(data, dict) else {},
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(payload)
