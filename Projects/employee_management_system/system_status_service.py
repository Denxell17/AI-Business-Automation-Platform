"""Safe operational status checks for ABAP."""

import sqlite3
from pathlib import Path

import psycopg

from database import get_database_connection


def database_is_ready(database_file: Path) -> bool:
    """Return whether ABAP's configured database is usable."""
    connection = None

    try:
        connection = get_database_connection(database_file)
        connection.execute(
            "SELECT 1 FROM employees LIMIT 1"
        )
        return True
    except (sqlite3.Error, psycopg.Error, ValueError):
        return False
    finally:
        if connection is not None:
            try:
                connection.close()
            except (sqlite3.Error, psycopg.Error):
                pass