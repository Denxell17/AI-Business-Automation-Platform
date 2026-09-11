"""Configuration for external AI-provider adapters."""

import math
import os
from collections.abc import Mapping
from typing import TypedDict


DEFAULT_OPENAI_TIMEOUT_SECONDS = 30.0
MIN_OPENAI_TIMEOUT_SECONDS = 1.0
MAX_OPENAI_TIMEOUT_SECONDS = 120.0


class OpenAIProviderSettings(TypedDict):
    """Describe validated settings required by the OpenAI adapter."""

    api_key: str
    timeout_seconds: float


def load_openai_provider_settings(
    environment: Mapping[str, str] | None = None,
) -> OpenAIProviderSettings:
    """Load and validate OpenAI settings without making a provider request."""
    selected_environment = (
        environment if environment is not None else os.environ
    )

    api_key = selected_environment.get(
        "OPENAI_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise ValueError("OPENAI_API_KEY is required.")

    timeout_value = selected_environment.get(
        "OPENAI_TIMEOUT_SECONDS",
        str(DEFAULT_OPENAI_TIMEOUT_SECONDS),
    ).strip()

    try:
        timeout_seconds = float(timeout_value)
    except ValueError as error:
        raise ValueError(
            "OPENAI_TIMEOUT_SECONDS must be a number."
        ) from error

    if (
        not math.isfinite(timeout_seconds)
        or timeout_seconds < MIN_OPENAI_TIMEOUT_SECONDS
        or timeout_seconds > MAX_OPENAI_TIMEOUT_SECONDS
    ):
        raise ValueError(
            "OPENAI_TIMEOUT_SECONDS must be between "
            f"{MIN_OPENAI_TIMEOUT_SECONDS:g} and "
            f"{MAX_OPENAI_TIMEOUT_SECONDS:g} seconds."
        )

    return {
        "api_key": api_key,
        "timeout_seconds": timeout_seconds,
    }