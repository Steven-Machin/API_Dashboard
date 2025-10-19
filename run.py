import os

from app import create_app

try:
    from dotenv import load_dotenv
except ImportError as exc:
    raise RuntimeError(
        "python-dotenv must be installed to load environment variables."
    ) from exc

load_dotenv()

app = create_app()
app.secret_key = os.getenv(
    "SECRET_KEY", "supersecret123"
)  # Replace with a strong key in production environments.

if __name__ == "__main__":
    app.run(debug=True)
