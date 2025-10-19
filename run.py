import os

from app import create_app

try:
    from dotenv import load_dotenv
except ImportError as exc:
    raise RuntimeError(
        "python-dotenv must be installed to load environment variables."
    ) from exc

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, "app", "templates")

app = create_app()
app.template_folder = TEMPLATE_DIR
if app.jinja_loader:
    searchpath = [TEMPLATE_DIR, *app.jinja_loader.searchpath]
    # Preserve order while removing duplicates
    seen = set()
    app.jinja_loader.searchpath = [
        path for path in searchpath if not (path in seen or seen.add(path))
    ]
app.secret_key = os.getenv(
    "SECRET_KEY", "supersecret123"
)  # Replace with a strong key in production environments.

if __name__ == "__main__":
    app.run(debug=True)
