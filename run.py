"""
Entry point for local development.
    python run.py

For production, use a WSGI server instead, e.g.:
    gunicorn "app:create_app()"
"""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    from app.config import Config

    app.run(debug=Config.DEBUG, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
