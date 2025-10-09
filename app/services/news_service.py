from __future__ import annotations

import os
from typing import Dict, List

import requests
from requests import HTTPError, RequestException

NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
DEFAULT_COUNTRY = "us"
MAX_HEADLINES = 5

_NEWS_FALLBACK: List[Dict[str, str]] = [
    {
        "title": "Sample Tech Headline",
        "description": "An example story demonstrating the dashboard layout.",
        "url": "https://example.com/news/sample-tech-headline",
        "source": "Example News",
    },
    {
        "title": "Stay Tuned for Real Updates",
        "description": "Provide a NEWS_API_KEY environment variable to fetch live data.",
        "url": "https://example.com/news/stay-tuned",
        "source": "Example News",
    },
    {
        "title": "Build Something Great",
        "description": "Customize this dashboard with your own news sources.",
        "url": "https://example.com/news/build-something-great",
        "source": "Example News",
    },
]


def get_headlines() -> List[Dict[str, str]]:
    """Fetch top headlines from NewsAPI or return canned examples."""
    api_key = os.environ.get("NEWS_API_KEY")
    params = {"country": DEFAULT_COUNTRY, "pageSize": MAX_HEADLINES}

    if api_key:
        try:
            params["apiKey"] = api_key
            response = requests.get(NEWS_API_URL, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            articles = payload.get("articles", [])
            parsed: List[Dict[str, str]] = []
            for article in articles:
                title = article.get("title") or "Untitled"
                url = article.get("url") or ""
                if not url:
                    continue
                parsed.append(
                    {
                        "title": title,
                        "description": article.get("description", ""),
                        "url": url,
                        "source": (article.get("source") or {}).get("name", ""),
                    }
                )
                if len(parsed) >= MAX_HEADLINES:
                    break
            if parsed:
                return parsed
        except (HTTPError, RequestException, ValueError):
            # Fallback keeps the UI populated even when the API call fails.
            pass

    return list(_NEWS_FALLBACK)
