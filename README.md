# API Dashboard

This project demonstrates a modular Flask application that aggregates data from several public APIs and presents the results in both JSON form and a Bootstrap-powered dashboard.

## Getting Started

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Export API keys so the live endpoints can be queried:
   - `OPENWEATHER_API_KEY` for [OpenWeatherMap](https://openweathermap.org/api).
   - `NEWS_API_KEY` for [NewsAPI](https://newsapi.org/).
   - Set `DAILY_SUMMARY_WEBHOOK_URL` to a Discord webhook if you want to receive automated summaries.
   - (Optional) Control scheduling with:
     - `ENABLE_DAILY_SUMMARY` (`true`/`false`, defaults to `true`)
     - `DAILY_SUMMARY_HOUR` and `DAILY_SUMMARY_MINUTE` (UTC by default)
     - `SCHEDULER_TIMEZONE` (e.g., `America/Chicago`)
4. Run the development server:
   ```bash
   flask --app run.py --debug run
   ```

The app exposes JSON endpoints at `/crypto`, `/weather`, and `/news` and a dashboard view at `/`.

## Project Structure

```
.
├── app
│   ├── __init__.py          # Application factory
│   ├── routes               # Flask blueprints
│   │   ├── crypto.py
│   │   ├── main.py
│   │   ├── news.py
│   │   └── weather.py
│   └── services             # API client helpers with graceful fallbacks
│       ├── crypto_service.py
│       ├── news_service.py
│       └── weather_service.py
├── templates
│   └── index.html           # Bootstrap dashboard layout
├── requirements.txt
└── run.py                   # Entry point used by Flask CLI
```

## Notes

- When API keys are not provided or network access fails, each service supplies placeholder data so the dashboard remains useful offline.
- A daily background job aggregates 24-hour crypto performance, average temperature, and the latest headlines, then pushes the summary to the configured Discord webhook with retry-safe logging.
- Insights charts include lightweight linear regression forecasts (based on the latest 10–20 readings) with dashed projection lines and inline prediction labels.
- Customize the dashboard further by adding new services, background tasks, or persistent storage as needed.
# API_Dashboard
