from __future__ import annotations

from typing import Dict

import requests
from requests import HTTPError, RequestException

COIN_GECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum&vs_currencies=usd"
)

_CRYPTO_FALLBACK: Dict[str, Dict[str, float]] = {
    "bitcoin": {"usd": 27000.0},
    "ethereum": {"usd": 1800.0},
}


def get_crypto_prices() -> Dict[str, Dict[str, float]]:
    """Fetch crypto prices from CoinGecko with a static fallback."""
    try:
        response = requests.get(COIN_GECKO_URL, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and payload:
            result: Dict[str, Dict[str, float]] = {}
            for symbol, fallback in _CRYPTO_FALLBACK.items():
                value = payload.get(symbol, {}).get("usd")
                if isinstance(value, (int, float)):
                    result[symbol] = {"usd": float(value)}
                else:
                    result[symbol] = {"usd": fallback["usd"]}

            if result:
                return result
    except (HTTPError, RequestException, ValueError):
        # Intentionally fall back to canned data when an API error occurs.
        pass

    return _CRYPTO_FALLBACK.copy()
