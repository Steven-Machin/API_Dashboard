from __future__ import annotations

from datetime import datetime, timezone
from app.extensions import db
from app.models import CryptoHistory, WeatherHistory


def _prune_history(model: type[db.Model], limit: int) -> None:
    """Remove rows older than the newest ``limit`` records to cap table size."""
    # Order newest first so everything beyond ``limit`` is safe to delete.
    stale_rows = (
        model.query.order_by(model.timestamp.desc(), model.id.desc()).offset(limit).all()
    )
    if not stale_rows:
        return

    for row in stale_rows:
        db.session.delete(row)


def save_crypto_data(bitcoin_price: float | None, ethereum_price: float | None) -> None:
    """Persist a crypto price snapshot if both values are present."""
    if bitcoin_price is None or ethereum_price is None:
        return

    entry = CryptoHistory(
        timestamp=datetime.now(timezone.utc),
        bitcoin_price=float(bitcoin_price),
        ethereum_price=float(ethereum_price),
    )
    db.session.add(entry)
    db.session.flush()  # Ensure the new row participates in the pruning query.

    _prune_history(CryptoHistory, limit=50)
    db.session.commit()


def save_weather_data(
    temperature: float | None, condition: str | None
) -> None:
    """Persist a weather snapshot when the core fields are available."""
    if temperature is None or not condition:
        return

    entry = WeatherHistory(
        timestamp=datetime.now(timezone.utc),
        temperature=float(temperature),
        condition=condition,
    )
    db.session.add(entry)
    db.session.flush()  # Flush before pruning so the fresh row is considered.

    _prune_history(WeatherHistory, limit=50)
    db.session.commit()
