"""Configuration for external AI-provider adapters."""

import math
import os
import re
from collections.abc import Mapping
from typing import TypedDict


DEFAULT_OPENAI_TIMEOUT_SECONDS = 30.0
MIN_OPENAI_TIMEOUT_SECONDS = 1.0
MAX_OPENAI_TIMEOUT_SECONDS = 120.0
DEFAULT_LOCAL_AI_CONNECT_TIMEOUT_SECONDS = 2.0
DEFAULT_LOCAL_AI_READ_TIMEOUT_SECONDS = 90.0
DEFAULT_LOCAL_AI_MAX_INPUT_CHARS = 12000
DEFAULT_LOCAL_AI_MAX_OUTPUT_TOKENS = 256

MIN_LOCAL_AI_TIMEOUT_SECONDS = 1.0
MAX_LOCAL_AI_CONNECT_TIMEOUT_SECONDS = 10.0
MAX_LOCAL_AI_READ_TIMEOUT_SECONDS = 120.0
MIN_LOCAL_AI_MAX_INPUT_CHARS = 1
MAX_LOCAL_AI_MAX_INPUT_CHARS = 12000
MIN_LOCAL_AI_MAX_OUTPUT_TOKENS = 1
MAX_LOCAL_AI_MAX_OUTPUT_TOKENS = 256


def _load_bounded_float(
    environment: Mapping[str, str],
    name: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    value = environment.get(name, str(default))

    if not isinstance(value, str) or value != value.strip():
        raise ValueError("Invalid local provider configuration.")

    try:
        number = float(value)
    except ValueError:
        raise ValueError("Invalid local provider configuration.") from None

    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError("Invalid local provider configuration.")

    return number


def _load_bounded_positive_integer(
    environment: Mapping[str, str],
    name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    value = environment.get(name, str(default))

    if (
        not isinstance(value, str)
        or re.fullmatch(r"[1-9][0-9]*", value) is None
    ):
        raise ValueError("Invalid local provider configuration.")

    number = int(value)

    if not minimum <= number <= maximum:
        raise ValueError("Invalid local provider configuration.")

    return number


class LocalProviderSettings(TypedDict):
    provider: str
    model: str
    base_url: str
    api_key: str
    connect_timeout_seconds: float
    read_timeout_seconds: float
    max_input_chars: int
    max_output_tokens: int


def load_agent_provider_settings(
    environment: Mapping[str, str] | None = None,
) -> LocalProviderSettings | None:
    """Load local provider settings without contacting the provider."""
    selected_environment = (
        environment if environment is not None else os.environ
    )
    enabled = selected_environment.get("ABAP_INTEGRATIONS_ENABLED", "false")
    provider = selected_environment.get("ABAP_EXTERNAL_PROVIDER", "disabled")

    if enabled == "false" and provider == "disabled":
        return None

    if enabled == "true" and provider == "llama_cpp":
        model = selected_environment.get("ABAP_LOCAL_AI_MODEL", "")
        base_url = selected_environment.get("ABAP_LLAMA_CPP_BASE_URL", "")
        api_key = selected_environment.get("ABAP_LLAMA_CPP_API_KEY", "")

        if (
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", model) is None
            or not api_key
            or any(character.isspace() for character in api_key)
            or base_url != "http://127.0.0.1:8080/v1"
        ):
            raise ValueError("Invalid local provider configuration.")

        connect_timeout_seconds = _load_bounded_float(
            selected_environment,
            "ABAP_LOCAL_AI_CONNECT_TIMEOUT_SECONDS",
            DEFAULT_LOCAL_AI_CONNECT_TIMEOUT_SECONDS,
            MIN_LOCAL_AI_TIMEOUT_SECONDS,
            MAX_LOCAL_AI_CONNECT_TIMEOUT_SECONDS,
        )
        read_timeout_seconds = _load_bounded_float(
            selected_environment,
            "ABAP_LOCAL_AI_READ_TIMEOUT_SECONDS",
            DEFAULT_LOCAL_AI_READ_TIMEOUT_SECONDS,
            MIN_LOCAL_AI_TIMEOUT_SECONDS,
            MAX_LOCAL_AI_READ_TIMEOUT_SECONDS,
        )
        max_input_chars = _load_bounded_positive_integer(
            selected_environment,
            "ABAP_LOCAL_AI_MAX_INPUT_CHARS",
            DEFAULT_LOCAL_AI_MAX_INPUT_CHARS,
            MIN_LOCAL_AI_MAX_INPUT_CHARS,
            MAX_LOCAL_AI_MAX_INPUT_CHARS,
        )
        max_output_tokens = _load_bounded_positive_integer(
            selected_environment,
            "ABAP_LOCAL_AI_MAX_OUTPUT_TOKENS",
            DEFAULT_LOCAL_AI_MAX_OUTPUT_TOKENS,
            MIN_LOCAL_AI_MAX_OUTPUT_TOKENS,
            MAX_LOCAL_AI_MAX_OUTPUT_TOKENS,
        )

        return {
            "provider": provider,
            "model": model,
            "base_url": base_url,
            "api_key": api_key,
            "connect_timeout_seconds": connect_timeout_seconds,
            "read_timeout_seconds": read_timeout_seconds,
            "max_input_chars": max_input_chars,
            "max_output_tokens": max_output_tokens,
        }

    raise ValueError("Invalid external provider configuration.")


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
