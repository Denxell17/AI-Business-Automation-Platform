"""Open a database connection using the selected backend."""

import sqlite3
from pathlib import Path

import psycopg

from database_config import (
    DATABASE_BACKEND_SQLITE,
    DatabaseSettings,
    load_database_settings,
)


DEFAULT_SQLITE_DATABASE_FILE = (
    Path(__file__).with_name("data") / "employees.db"
)


def open_configured_database_connection(
    settings: DatabaseSettings | None = None,
    sqlite_file: Path = DEFAULT_SQLITE_DATABASE_FILE,
):
    """Open either SQLite or PostgreSQL from validated settings."""
    selected_settings = (
        settings if settings is not None
        else load_database_settings()
    )

    if selected_settings["backend"] == DATABASE_BACKEND_SQLITE:
        connection = sqlite3.connect(sqlite_file)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    database_url = selected_settings["database_url"]

    if database_url is None:
        raise ValueError(
            "PostgreSQL requires a database connection URL."
        )

    return psycopg.connect(database_url)