from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

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


def get_crypto_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Return the newest crypto history entries ordered oldest to newest."""
    rows = (
        CryptoHistory.query.order_by(
            CryptoHistory.timestamp.desc(), CryptoHistory.id.desc()
        )
        .limit(limit)
        .all()
    )
    ordered = list(reversed(rows))
    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "bitcoin_price": float(row.bitcoin_price),
            "ethereum_price": float(row.ethereum_price),
        }
        for row in ordered
    ]


def get_weather_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Return the newest weather history entries ordered oldest to newest."""
    rows = (
        WeatherHistory.query.order_by(
            WeatherHistory.timestamp.desc(), WeatherHistory.id.desc()
        )
        .limit(limit)
        .all()
    )
    ordered = list(reversed(rows))
    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "temperature": float(row.temperature),
            "condition": row.condition,
        }
        for row in ordered
    ]


def calculate_crypto_change(hours: int = 24) -> Dict[str, Any]:
    """Compute percent change for crypto prices within a rolling window."""
    window_start = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows: List[CryptoHistory] = (
        CryptoHistory.query.filter(CryptoHistory.timestamp >= window_start)
        .order_by(CryptoHistory.timestamp.asc(), CryptoHistory.id.asc())
        .all()
    )

    metrics: Dict[str, Any] = {
        "bitcoin_change_pct": None,
        "ethereum_change_pct": None,
        "sample_size": len(rows),
    }

    if len(rows) < 2:
        return metrics

    first = rows[0]
    last = rows[-1]

    def _percent_change(start: float | None, end: float | None) -> float | None:
        if start is None or end is None:
            return None
        if start == 0:
            return None
        return ((end - start) / start) * 100.0

    metrics["bitcoin_change_pct"] = _percent_change(
        float(first.bitcoin_price), float(last.bitcoin_price)
    )
    metrics["ethereum_change_pct"] = _percent_change(
        float(first.ethereum_price), float(last.ethereum_price)
    )
    return metrics


def calculate_weather_average(days: int = 7) -> Dict[str, Any]:
    """Calculate the mean temperature captured during the supplied window."""
    window_start = datetime.now(timezone.utc) - timedelta(days=days)
    rows: List[WeatherHistory] = (
        WeatherHistory.query.filter(WeatherHistory.timestamp >= window_start)
        .order_by(WeatherHistory.timestamp.asc(), WeatherHistory.id.asc())
        .all()
    )

    metrics: Dict[str, Any] = {"average_temperature": None, "sample_size": len(rows)}
    if not rows:
        return metrics

    total = sum(float(row.temperature) for row in rows)
    metrics["average_temperature"] = total / len(rows)
    return metrics


