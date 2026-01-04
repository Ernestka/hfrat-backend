"""Application configuration settings."""
from __future__ import annotations

import os
import secrets
from datetime import timedelta
from typing import Iterable, List

from dotenv import load_dotenv

load_dotenv()


def _csv_env(name: str, default: Iterable[str]) -> List[str]:
    raw = os.getenv(name)
    if not raw:
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _secret_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    # Generate a per-process secret for local/dev use to avoid hardcoded keys.
    return secrets.token_urlsafe(32)


def _get_database_url() -> str:
    """Get database URL, converting postgres:// to postgresql:// for SQLAlchemy."""
    db_url = os.getenv("DATABASE_URL", "sqlite:///hfrat.db")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = _secret_env("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = _secret_env("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = True

    # CORS: Allow multiple origins via environment variable
    # Example: CORS_ALLOWED_ORIGINS=https://myapp.netlify.app,https://myapp.vercel.app
    CORS_ORIGINS = _csv_env(
        "CORS_ALLOWED_ORIGINS",
        ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # SECRET_KEY and JWT_SECRET_KEY are inherited from Config
    # which uses _secret_env() to get from environment or generate a fallback


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    CORS_ORIGINS = ["http://localhost:3000"]


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
