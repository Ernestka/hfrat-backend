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


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = _secret_env("SECRET_KEY")

    # Handle Heroku-style DATABASE_URL (postgres:// -> postgresql://)
    _db_url = os.getenv("DATABASE_URL", "sqlite:///hfrat.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url

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

    # In production, require proper secrets (not auto-generated)
    @property
    def SECRET_KEY(self):
        key = os.getenv("SECRET_KEY")
        if not key:
            raise ValueError(
                "SECRET_KEY environment variable must be set in production")
        return key

    @property
    def JWT_SECRET_KEY(self):
        key = os.getenv("JWT_SECRET_KEY")
        if not key:
            raise ValueError(
                "JWT_SECRET_KEY environment variable must be set in production")
        return key


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
