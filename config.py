import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'pitchtrack.db')}"
    )

    # for render
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
            )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Seed demo data on first start when the database is empty; tests switch this off
    AUTO_SEED = True

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 60))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 30))
    )

    JWT_TOKEN_LOCATION = ["headers"]

    FRONTEND_ORIGINS = os.environ.get(
        "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")

    # Resend (transactional email)
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "noreply@yourdomain.com")

    # Frontend URL (used for building password-reset links)
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
