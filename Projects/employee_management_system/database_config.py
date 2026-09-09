"""Database backend configuration for local and production environments."""

import os
from collections.abc import Mapping
from typing import TypedDict
from urllib.parse import urlparse


DATABASE_BACKEND_SQLITE = "sqlite"
DATABASE_BACKEND_POSTGRESQL = "postgresql"

VALID_DATABASE_BACKENDS = frozenset(
    {
        DATABASE_BACKEND_SQLITE,
        DATABASE_BACKEND_POSTGRESQL,
    }
)


class DatabaseSettings(TypedDict):
    backend: str
    database_url: str | None


def load_database_settings(
    environment: Mapping[str, str] | None = None,
) -> DatabaseSettings:
    """Load and validate database settings without opening a connection."""
    selected_environment = (
        environment if environment is not None else os.environ
    )

    backend = selected_environment.get(
        "DATABASE_BACKEND",
        DATABASE_BACKEND_SQLITE,
    ).strip().casefold()

    if backend not in VALID_DATABASE_BACKENDS:
        raise ValueError(
            "DATABASE_BACKEND must be sqlite or postgresql."
        )

    database_url = selected_environment.get(
        "DATABASE_URL",
        "",
    ).strip()

    if backend == DATABASE_BACKEND_SQLITE:
        return {
            "backend": backend,
            "database_url": None,
        }

    if not database_url:
        raise ValueError(
            "DATABASE_URL is required when PostgreSQL is selected."
        )

    parsed_url = urlparse(database_url)

    if parsed_url.scheme not in {"postgres", "postgresql"}:
        raise ValueError(
            "DATABASE_URL must use the PostgreSQL connection format."
        )

    if not parsed_url.hostname or not parsed_url.path.strip("/"):
        raise ValueError(
            "DATABASE_URL must include a host and database name."
        )

    return {
        "backend": backend,
        "database_url": database_url,
    }