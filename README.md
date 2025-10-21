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

### Database Migrations

Use Flask-Migrate to manage schema changes without recreating the database:

```bash
flask db init
flask db migrate -m "add new fields"
flask db upgrade
```

The app exposes JSON endpoints at `/crypto`, `/weather`, and `/news` and a dashboard view at `/`.

## Project Structure

```
.
Γö£ΓöÇΓöÇ app
Γöé   Γö£ΓöÇΓöÇ __init__.py          # Application factory
Γöé   Γö£ΓöÇΓöÇ routes               # Flask blueprints
Γöé   Γöé   Γö£ΓöÇΓöÇ crypto.py
Γöé   Γöé   Γö£ΓöÇΓöÇ main.py
Γöé   Γöé   Γö£ΓöÇΓöÇ news.py
Γöé   Γöé   ΓööΓöÇΓöÇ weather.py
Γöé   ΓööΓöÇΓöÇ services             # API client helpers with graceful fallbacks
Γöé       Γö£ΓöÇΓöÇ crypto_service.py
Γöé       Γö£ΓöÇΓöÇ news_service.py
Γöé       ΓööΓöÇΓöÇ weather_service.py
Γö£ΓöÇΓöÇ templates
Γöé   ΓööΓöÇΓöÇ index.html           # Bootstrap dashboard layout
Γö£ΓöÇΓöÇ requirements.txt
ΓööΓöÇΓöÇ run.py                   # Entry point used by Flask CLI
```

## Notes

- When API keys are not provided or network access fails, each service supplies placeholder data so the dashboard remains useful offline.
- A daily background job aggregates 24-hour crypto performance, average temperature, and the latest headlines, then pushes the summary to the configured Discord webhook with retry-safe logging.
- Insights charts include lightweight linear regression forecasts (based on the latest 10ΓÇô20 readings) with dashed projection lines and inline prediction labels.
- Customize the dashboard further by adding new services, background tasks, or persistent storage as needed.


### 🧩 Local Development
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the example environment file and update secrets:
   ```bash
   cp .env.example .env
   ```
4. Launch the development server:
   ```bash
   flask --app run.py --debug run
   ```
# API_Dashboard
