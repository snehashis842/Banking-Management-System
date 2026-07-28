"""
Centralized configuration, loaded from environment variables (.env in dev).
No secrets live in code anymore — copy .env.example to .env and fill it in.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.environ.get("DB_NAME", "project")

    FLASK_SECRET = os.environ.get("FLASK_SECRET")  # set a real one in production
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = FLASK_ENV == "development"

    SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))

    ADMIN_EMAILS = [
        e.strip()
        for e in os.environ.get("ADMIN_EMAILS", "").split(",")
        if e.strip()
    ]

    SESSION_LIFETIME_HOURS = int(os.environ.get("SESSION_LIFETIME_HOURS", 2))
