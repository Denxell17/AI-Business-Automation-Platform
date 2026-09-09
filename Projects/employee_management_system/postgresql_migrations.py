"""Apply versioned PostgreSQL schema migrations safely."""

import re
from pathlib import Path

import psycopg


POSTGRESQL_MIGRATIONS_DIRECTORY = (
    Path(__file__).with_name("migrations") / "postgresql"
)

MIGRATION_FILE_PATTERN = re.compile(
    r"\d{3}_[a-z0-9_]+\.sql"
)


def load_postgresql_migration_files(
    migrations_directory: Path = POSTGRESQL_MIGRATIONS_DIRECTORY,
) -> list[Path]:
    """Load valid PostgreSQL migration files in filename order."""
    if not migrations_directory.is_dir():
        raise FileNotFoundError(
            "The PostgreSQL migrations directory was not found."
        )

    migration_files = sorted(
        path
        for path in migrations_directory.glob("*.sql")
        if path.is_file()
    )

    if not migration_files:
        raise ValueError(
            "No PostgreSQL migration files were found."
        )

    for migration_file in migration_files:
        if MIGRATION_FILE_PATTERN.fullmatch(
            migration_file.name
        ) is None:
            raise ValueError(
                "PostgreSQL migration filenames must use "
                "the 001_description.sql format."
            )

        migration_sql = migration_file.read_text(
            encoding="utf-8-sig"
        )

        if not migration_sql.strip():
            raise ValueError(
                "PostgreSQL migration files cannot be empty."
            )

    return migration_files


def apply_postgresql_migrations(
    database_url: str,
    migrations_directory: Path = POSTGRESQL_MIGRATIONS_DIRECTORY,
) -> list[str]:
    """Apply pending migrations in one PostgreSQL transaction."""
    if not isinstance(database_url, str) or not database_url.strip():
        raise ValueError(
            "A PostgreSQL database URL is required."
        )

    migration_files = load_postgresql_migration_files(
        migrations_directory
    )
    applied_now: list[str] = []

    with psycopg.connect(database_url.strip()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_name TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                SELECT migration_name
                FROM schema_migrations
                ORDER BY migration_name
                """
            )
            applied_names = {
                row[0]
                for row in cursor.fetchall()
            }

            for migration_file in migration_files:
                if migration_file.name in applied_names:
                    continue

                migration_sql = migration_file.read_text(
                    encoding="utf-8-sig"
                )
                cursor.execute(migration_sql)
                cursor.execute(
                    """
                    INSERT INTO schema_migrations (
                        migration_name
                    )
                    VALUES (%s)
                    """,
                    (migration_file.name,),
                )
                applied_now.append(migration_file.name)

    return applied_now