from datetime import datetime, timezone

from flask import Blueprint, render_template

from app.services.crypto_service import get_crypto_prices

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    crypto_prices = get_crypto_prices()
    last_updated = datetime.now(timezone.utc)

    return render_template(
        "index.html",
        crypto_prices=crypto_prices,
        crypto_last_updated=last_updated,
    )
