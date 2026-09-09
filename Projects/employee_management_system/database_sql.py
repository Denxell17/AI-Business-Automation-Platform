"""Translate the small SQL differences used by ABAP's databases."""

import re

from database_config import (
    DATABASE_BACKEND_POSTGRESQL,
    DATABASE_BACKEND_SQLITE,
)


def adapt_parameter_placeholders(query: str, backend: str) -> str:
    """Return SQL compatible with the selected database backend."""
    if backend == DATABASE_BACKEND_SQLITE:
        return query

    if backend != DATABASE_BACKEND_POSTGRESQL:
        raise ValueError(
            "Database backend must be sqlite or postgresql."
        )

    adapted_query = query.replace("?", "%s")
    adapted_query = re.sub(
        r"\busername\s+COLLATE\s+NOCASE\b",
        "LOWER(username)",
        adapted_query,
        flags=re.IGNORECASE,
    )
    adapted_query = re.sub(
        r"\bWHERE\s+username\s*=\s*%s",
        "WHERE LOWER(username) = LOWER(%s)",
        adapted_query,
        flags=re.IGNORECASE,
    )
    adapted_query = re.sub(
        r"\bis_enabled\s*=\s*1\b",
        "is_enabled = TRUE",
        adapted_query,
        flags=re.IGNORECASE,
    )
    adapted_query = re.sub(
        r"\bis_enabled\s*=\s*0\b",
        "is_enabled = FALSE",
        adapted_query,
        flags=re.IGNORECASE,
    )

    if re.search(
        r"\bINSERT\s+OR\s+IGNORE\s+INTO\b",
        adapted_query,
        flags=re.IGNORECASE,
    ):
        adapted_query = re.sub(
            r"\bINSERT\s+OR\s+IGNORE\s+INTO\b",
            "INSERT INTO",
            adapted_query,
            count=1,
            flags=re.IGNORECASE,
        )
        adapted_query = f"{adapted_query.rstrip()}\nON CONFLICT DO NOTHING"

    return adapted_query
