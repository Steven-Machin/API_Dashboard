from __future__ import annotations

import os
from typing import Any, Dict

import requests
from requests import HTTPError, RequestException

OPEN_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_CITY = "Chicago"
DEFAULT_UNITS = "imperial"

_WEATHER_FALLBACK: Dict[str, Any] = {
    "name": DEFAULT_CITY,
    "main": {
        "temp": 72.0,
        "humidity": 55,
    },
    "weather": [
        {"main": "Clear", "description": "clear skies"},
    ],
    "wind": {"speed": 5.0},
}


def get_weather_forecast() -> Dict[str, Any]:
    """Fetch weather data from OpenWeatherMap or return fallback values."""
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    params = {"q": DEFAULT_CITY, "units": DEFAULT_UNITS}

    if api_key:
        params["appid"] = api_key
        try:
            response = requests.get(OPEN_WEATHER_URL, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict) and payload.get("name"):
                return payload
        except (HTTPError, RequestException, ValueError):
            # Swallow API errors to ensure the dashboard remains functional.
            pass

    return _WEATHER_FALLBACK.copy()
