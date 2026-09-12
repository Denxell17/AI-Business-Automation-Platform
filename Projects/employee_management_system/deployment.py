"""Validated production factory and explicit PostgreSQL migration command."""

import os

from database_config import load_database_settings
from postgresql_migrations import apply_postgresql_migrations
from web_app import create_web_application


def production_settings():
    settings = load_database_settings()
    if settings["backend"] != "postgresql":
        raise ValueError("Deployment requires PostgreSQL.")
    secret = os.environ.get("ABAP_SESSION_SECRET", "").strip()
    if len(secret) < 32 or secret.startswith("replace_"):
        raise ValueError(
            "ABAP_SESSION_SECRET must be a random secret "
            "of at least 32 characters."
        )
    return settings, secret


def create_application():
    """Keep signed sessions stable across restarts and require HTTPS cookies."""
    _, secret = production_settings()
    return create_web_application(session_secret=secret, secure_cookies=True)


def migrate():
    """Run once before starting web workers; never migrate during requests."""
    settings, _ = production_settings()
    apply_postgresql_migrations(settings["database_url"])
    print("PostgreSQL migrations completed.")


if __name__ == "__main__":
    migrate()
