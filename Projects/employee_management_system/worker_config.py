"""Validated configuration for the separate ABAP scheduler worker."""

import os
from typing import Mapping, TypedDict


class WorkerSettings(TypedDict):
    enabled: bool
    poll_seconds: int
    claim_limit: int
    max_attempts: int
    retry_base_seconds: int
    retry_max_seconds: int
    stale_after_seconds: int
    shutdown_grace_seconds: int


def _positive_integer(
    environment: Mapping[str, str],
    name: str,
    default: int,
    maximum: int,
) -> int:
    value = environment.get(name, str(default)).strip()
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive integer.") from error
    if parsed <= 0 or parsed > maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}.")
    return parsed


def load_worker_settings(
    environment: Mapping[str, str] | None = None,
) -> WorkerSettings:
    """Load bounded worker values and reject unsafe or ambiguous input."""
    selected_environment = environment if environment is not None else os.environ
    enabled_value = selected_environment.get("ABAP_WORKER_ENABLED", "false").strip().casefold()
    if enabled_value not in {"true", "false"}:
        raise ValueError("ABAP_WORKER_ENABLED must be true or false.")
    retry_base_seconds = _positive_integer(
        selected_environment, "ABAP_WORKER_RETRY_BASE_SECONDS", 5, 3600,
    )
    retry_max_seconds = _positive_integer(
        selected_environment, "ABAP_WORKER_RETRY_MAX_SECONDS", 300, 86400,
    )
    if retry_max_seconds < retry_base_seconds:
        raise ValueError(
            "ABAP_WORKER_RETRY_MAX_SECONDS must not be below "
            "ABAP_WORKER_RETRY_BASE_SECONDS."
        )
    return {
        "enabled": enabled_value == "true",
        "poll_seconds": _positive_integer(
            selected_environment, "ABAP_WORKER_POLL_SECONDS", 5, 3600,
        ),
        "claim_limit": _positive_integer(
            selected_environment, "ABAP_WORKER_CLAIM_LIMIT", 25, 1000,
        ),
        "max_attempts": _positive_integer(
            selected_environment, "ABAP_WORKER_MAX_ATTEMPTS", 5, 20,
        ),
        "retry_base_seconds": retry_base_seconds,
        "retry_max_seconds": retry_max_seconds,
        "stale_after_seconds": _positive_integer(
            selected_environment, "ABAP_WORKER_STALE_AFTER_SECONDS", 900, 604800,
        ),
        "shutdown_grace_seconds": _positive_integer(
            selected_environment, "ABAP_WORKER_SHUTDOWN_GRACE_SECONDS", 30, 3600,
        ),
    }
