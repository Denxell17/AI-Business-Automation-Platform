"""Environment configuration for ABAP's AI Assistant."""

import os
from collections.abc import Mapping
from typing import TypedDict

from ai_assistant_service import (
    MAX_AI_ASSISTANT_MODEL_NAME_LENGTH,
)


class AiAssistantSettings(TypedDict):
    """Describe validated AI Assistant configuration."""

    model_name: str


def load_ai_assistant_settings(
    environment: Mapping[str, str] | None = None,
) -> AiAssistantSettings:
    """Load the explicitly selected AI Assistant model."""
    selected_environment = (
        environment if environment is not None else os.environ
    )

    model_name = selected_environment.get(
        "AI_ASSISTANT_MODEL",
        "",
    ).strip()

    if not model_name:
        raise ValueError("AI_ASSISTANT_MODEL is required.")

    if len(model_name) > MAX_AI_ASSISTANT_MODEL_NAME_LENGTH:
        raise ValueError(
            "AI_ASSISTANT_MODEL must be no more than "
            f"{MAX_AI_ASSISTANT_MODEL_NAME_LENGTH} characters."
        )

    return {
        "model_name": model_name,
    }