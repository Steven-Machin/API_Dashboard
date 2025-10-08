from __future__ import annotations

import os
from typing import Dict, List

import requests
from requests import HTTPError, RequestException

NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
DEFAULT_COUNTRY = "us"
DEFAULT_CATEGORY = "technology"

_NEWS_FALLBACK: List[Dict[str, str]] = [
    {
        "title": "Sample Tech Headline",
        "description": "An example story demonstrating the dashboard layout.",
        "url": "https://example.com/news/sample-tech-headline",
    },
    {
        "title": "Stay Tuned for Real Updates",
        "description": "Provide a NEWS_API_KEY environment variable to fetch live data.",
        "url": "https://example.com/news/stay-tuned",
    },
    {
        "title": "Build Something Great",
        "description": "Customize this dashboard with your own news sources.",
        "url": "https://example.com/news/build-something-great",
    },
]


def get_headlines() -> List[Dict[str, str]]:
    """Fetch top headlines from NewsAPI or return canned examples."""
    api_key = os.environ.get("NEWS_API_KEY")
    params = {"country": DEFAULT_COUNTRY, "category": DEFAULT_CATEGORY, "pageSize": 5}

    if api_key:
        try:
            response = requests.get(
                NEWS_API_URL, params=params, headers={"X-Api-Key": api_key}, timeout=10
            )
            response.raise_for_status()
            payload = response.json()
            articles = payload.get("articles", [])
            parsed = [
                {
                    "title": article.get("title", "Untitled"),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                }
                for article in articles
            ]
            if parsed:
                return parsed
        except (HTTPError, RequestException, ValueError):
            # Fallback keeps the UI populated even when the API call fails.
            pass

    return list(_NEWS_FALLBACK)
