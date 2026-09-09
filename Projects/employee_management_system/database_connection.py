"""Open a database connection using the selected backend."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from database_config import (
    DATABASE_BACKEND_SQLITE,
    DatabaseSettings,
    load_database_settings,
)


DEFAULT_SQLITE_DATABASE_FILE = (
    Path(__file__).with_name("data") / "employees.db"
)


class DatabaseRow(dict[str, Any]):
    """Dictionary row that also supports SQLite-style numeric access."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return tuple(self.values())[key]
        return super().__getitem__(key)


def _normalize_postgresql_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _normalize_postgresql_row(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return DatabaseRow(
            {
                key: _normalize_postgresql_value(value)
                for key, value in row.items()
            }
        )
    return row


class PostgreSQLCursorAdapter:
    """Expose PostgreSQL results in the shape used by SQLite repositories."""

    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def fetchone(self):
        return _normalize_postgresql_row(self._cursor.fetchone())

    def fetchall(self):
        return [
            _normalize_postgresql_row(row)
            for row in self._cursor.fetchall()
        ]


class PostgreSQLConnectionAdapter:
    """Translate repository SQL before Psycopg executes it."""

    def __init__(self, connection):
        self._connection = connection

    @property
    def raw_connection(self):
        return self._connection

    @property
    def row_factory(self):
        return dict_row

    @row_factory.setter
    def row_factory(self, _value):
        # PostgreSQL already uses dict_row. Existing repository assignments
        # are kept harmless while SQLite continues using sqlite3.Row.
        return None

    def execute(self, query: str, parameters=None):
        from database_sql import adapt_parameter_placeholders

        normalized_query = query.strip().upper()
        if normalized_query in {"BEGIN", "BEGIN IMMEDIATE"}:
            return None

        adapted_query = adapt_parameter_placeholders(
            query,
            "postgresql",
        )
        compact_query = " ".join(
            adapted_query.upper().split()
        )
        if (
            compact_query.startswith(
                "SELECT TASK_ID, SEQUENCE_NUMBER "
                "FROM WORKFLOW_TASKS WHERE WORKFLOW_ID = %S"
            )
            or compact_query.startswith(
                "SELECT STATUS FROM WORKFLOWS WHERE WORKFLOW_ID = %S"
            )
        ) and " FOR UPDATE" not in compact_query:
            adapted_query = f"{adapted_query.rstrip()} FOR UPDATE"

        if parameters is None:
            cursor = self._connection.execute(adapted_query)
        else:
            cursor = self._connection.execute(
                adapted_query,
                parameters,
            )
        return PostgreSQLCursorAdapter(cursor)

    def executemany(self, query: str, parameters):
        from database_sql import adapt_parameter_placeholders

        cursor = self._connection.cursor()
        cursor.executemany(
            adapt_parameter_placeholders(
                query,
                "postgresql",
            ),
            parameters,
        )
        return PostgreSQLCursorAdapter(cursor)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()


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

    connection = psycopg.connect(
        database_url,
        row_factory=dict_row,
    )
    return PostgreSQLConnectionAdapter(connection)
