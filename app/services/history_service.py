from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import statistics

import numpy as np

from app.extensions import db
from app.models import AnomalyLog, CryptoHistory, WeatherHistory

_ROLLING_WINDOW = 50
_ANOMALY_LIMIT = 200
_SIGMA_THRESHOLD = 2.0
_MIN_SAMPLE = 3
_FORECAST_MIN_POINTS = 10
_FORECAST_MAX_POINTS = 20


def _rolling_stats(values: Sequence[float]) -> Dict[str, Optional[float]]:
    cleaned = [float(v) for v in values if isinstance(v, (int, float))]
    if not cleaned:
        return {"mean": None, "std": None, "count": 0}

    mean = statistics.fmean(cleaned)
    std = statistics.pstdev(cleaned) if len(cleaned) >= 2 else 0.0
    return {"mean": mean, "std": std, "count": len(cleaned)}


def _linear_regression_forecast(values: Sequence[float]) -> Optional[float]:
    """Project the next value using a simple first-degree polynomial fit."""
    numeric = [float(v) for v in values if isinstance(v, (int, float))]
    if len(numeric) < _FORECAST_MIN_POINTS:
        return None

    window = min(len(numeric), _FORECAST_MAX_POINTS)
    series = np.array(numeric[-window:], dtype=float)
    if series.size < 2:
        return None

    x = np.arange(series.size, dtype=float)
    slope, intercept = np.polyfit(x, series, 1)
    forecast_value = slope * series.size + intercept
    return float(forecast_value)


def _estimate_next_timestamp(timestamps: Sequence[datetime]) -> Optional[datetime]:
    cleaned = [ts for ts in timestamps if isinstance(ts, datetime)]
    if not cleaned:
        return None
    if len(cleaned) == 1:
        return cleaned[0] + timedelta(hours=1)

    deltas = []
    for idx in range(1, len(cleaned)):
        current = cleaned[idx]
        previous = cleaned[idx - 1]
        delta = (current - previous).total_seconds()
        if delta > 0:
            deltas.append(delta)

    if not deltas:
        deltas = [
            (cleaned[-1] - cleaned[0]).total_seconds()
            / max(len(cleaned) - 1, 1)
        ]

    avg_seconds = float(np.mean(deltas)) if deltas else 0.0
    if avg_seconds <= 0:
        avg_seconds = 3600.0
    return cleaned[-1] + timedelta(seconds=avg_seconds)


def _log_anomaly(event_type: str, message: str) -> None:
    entry = AnomalyLog(event_type=event_type, message=message[:255])
    db.session.add(entry)
    _prune_anomalies(AnomalyLog, limit=_ANOMALY_LIMIT)


def _prune_anomalies(model: type[db.Model], limit: int) -> None:
    stale_rows = (
        model.query.order_by(model.timestamp.desc(), model.id.desc())
        .offset(limit)
        .all()
    )
    for row in stale_rows:
        db.session.delete(row)


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

    recent_rows: List[CryptoHistory] = (
        CryptoHistory.query.order_by(
            CryptoHistory.timestamp.desc(), CryptoHistory.id.desc()
        )
        .limit(_ROLLING_WINDOW)
        .all()
    )
    btc_historical = [float(row.bitcoin_price) for row in recent_rows]
    eth_historical = [float(row.ethereum_price) for row in recent_rows]

    entry = CryptoHistory(
        timestamp=datetime.now(timezone.utc),
        bitcoin_price=float(bitcoin_price),
        ethereum_price=float(ethereum_price),
    )
    db.session.add(entry)
    db.session.flush()  # Ensure the new row participates in the pruning query.

    _prune_history(CryptoHistory, limit=50)

    _detect_crypto_anomalies(float(bitcoin_price), float(ethereum_price), btc_historical, eth_historical)

    db.session.commit()


def save_weather_data(
    temperature: float | None, condition: str | None
) -> None:
    """Persist a weather snapshot when the core fields are available."""
    if temperature is None or not condition:
        return

    recent_rows: List[WeatherHistory] = (
        WeatherHistory.query.order_by(
            WeatherHistory.timestamp.desc(), WeatherHistory.id.desc()
        )
        .limit(_ROLLING_WINDOW)
        .all()
    )
    temp_history = [float(row.temperature) for row in recent_rows]

    entry = WeatherHistory(
        timestamp=datetime.now(timezone.utc),
        temperature=float(temperature),
        condition=condition,
    )
    db.session.add(entry)
    db.session.flush()  # Flush before pruning so the fresh row is considered.

    _prune_history(WeatherHistory, limit=50)

    _detect_weather_anomaly(float(temperature), values=temp_history)

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

    btc_values = [float(row.bitcoin_price) for row in rows]
    eth_values = [float(row.ethereum_price) for row in rows]
    btc_stats = _rolling_stats(btc_values)
    eth_stats = _rolling_stats(eth_values)

    metrics: Dict[str, Any] = {
        "bitcoin_change_pct": None,
        "ethereum_change_pct": None,
        "bitcoin_mean": btc_stats["mean"],
        "bitcoin_std": btc_stats["std"],
        "ethereum_mean": eth_stats["mean"],
        "ethereum_std": eth_stats["std"],
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
    metrics["forecast"] = forecast_crypto_prices()
    return metrics


def calculate_weather_average(days: int = 7) -> Dict[str, Any]:
    """Calculate the mean temperature captured during the supplied window."""
    window_start = datetime.now(timezone.utc) - timedelta(days=days)
    rows: List[WeatherHistory] = (
        WeatherHistory.query.filter(WeatherHistory.timestamp >= window_start)
        .order_by(WeatherHistory.timestamp.asc(), WeatherHistory.id.asc())
        .all()
    )

    temps = [float(row.temperature) for row in rows]
    stats = _rolling_stats(temps)

    metrics: Dict[str, Any] = {
        "average_temperature": stats["mean"],
        "temperature_std": stats["std"],
        "sample_size": len(rows),
    }
    if not rows:
        return metrics

    total = sum(float(row.temperature) for row in rows)
    metrics["average_temperature"] = total / len(rows)
    metrics["forecast"] = forecast_weather_temperature()
    return metrics


def forecast_crypto_prices() -> Dict[str, float | str | None]:
    """Return linear regression forecasts for the next crypto prices."""
    rows: List[CryptoHistory] = (
        CryptoHistory.query.order_by(
            CryptoHistory.timestamp.desc(), CryptoHistory.id.desc()
        )
        .limit(_FORECAST_MAX_POINTS)
        .all()
    )
    if len(rows) < _FORECAST_MIN_POINTS:
        return {"bitcoin_price": None, "ethereum_price": None, "next_timestamp": None}

    ordered = list(reversed(rows))
    timestamps = [row.timestamp for row in ordered]
    btc_values = [float(row.bitcoin_price) for row in ordered]
    eth_values = [float(row.ethereum_price) for row in ordered]

    forecast_btc = _linear_regression_forecast(btc_values)
    forecast_eth = _linear_regression_forecast(eth_values)
    next_time = _estimate_next_timestamp(timestamps)

    return {
        "bitcoin_price": forecast_btc,
        "ethereum_price": forecast_eth,
        "next_timestamp": next_time.isoformat() if next_time else None,
    }


def forecast_weather_temperature() -> Dict[str, float | str | None]:
    """Return the projected average temperature for the next interval."""
    rows: List[WeatherHistory] = (
        WeatherHistory.query.order_by(
            WeatherHistory.timestamp.desc(), WeatherHistory.id.desc()
        )
        .limit(_FORECAST_MAX_POINTS)
        .all()
    )
    if len(rows) < _FORECAST_MIN_POINTS:
        return {"average_temperature": None, "next_timestamp": None}

    ordered = list(reversed(rows))
    timestamps = [row.timestamp for row in ordered]
    temps = [float(row.temperature) for row in ordered]

    forecast_temp = _linear_regression_forecast(temps)
    next_time = _estimate_next_timestamp(timestamps)

    return {
        "average_temperature": forecast_temp,
        "next_timestamp": next_time.isoformat() if next_time else None,
    }


def _detect_crypto_anomalies(
    new_btc: float, new_eth: float, btc_history: Sequence[float], eth_history: Sequence[float]
) -> None:
    if len(btc_history) >= _MIN_SAMPLE:
        _flag_if_anomalous(
            category="crypto",
            metric="Bitcoin",
            value=new_btc,
            stats=_rolling_stats(btc_history),
        )

    if len(eth_history) >= _MIN_SAMPLE:
        _flag_if_anomalous(
            category="crypto",
            metric="Ethereum",
            value=new_eth,
            stats=_rolling_stats(eth_history),
        )


def _detect_weather_anomaly(temperature: float, values: Sequence[float]) -> None:
    if len(values) < _MIN_SAMPLE:
        return
    _flag_if_anomalous(
        category="weather",
        metric="Average temperature",
        value=temperature,
        stats=_rolling_stats(values),
    )


def _flag_if_anomalous(
    category: str, metric: str, value: float, stats: Dict[str, Optional[float]]
) -> None:
    mean = stats.get("mean")
    std = stats.get("std")
    if mean is None or std is None or std == 0 or stats.get("count", 0) < _MIN_SAMPLE:
        return

    deviation = abs(value - mean)
    if deviation <= _SIGMA_THRESHOLD * std:
        return

    message = (
        f"{metric} value {value:.2f} deviated more than {_SIGMA_THRESHOLD:.0f}σ "
        f"from mean {mean:.2f} (σ={std:.2f})."
    )
    _log_anomaly(category, message)


def has_recent_anomalies(hours: int = 24) -> bool:
    window_start = datetime.now(timezone.utc) - timedelta(hours=hours)
    return (
        AnomalyLog.query.filter(AnomalyLog.timestamp >= window_start)
        .limit(1)
        .first()
        is not None
    )


def recent_anomalies(limit: int = 10) -> List[Dict[str, Any]]:
    rows: List[AnomalyLog] = (
        AnomalyLog.query.order_by(AnomalyLog.timestamp.desc(), AnomalyLog.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "type": row.event_type,
            "message": row.message,
        }
        for row in rows
    ]


