"""Create AI providers only from validated external-provider settings."""

from collections.abc import Mapping

from agent_provider import AgentProvider
from agent_provider_config import load_agent_provider_settings
from llama_cpp_agent_provider import (
    HttpLlamaCppTransport,
    LlamaCppAgentProvider,
    LlamaCppTransport,
)


def create_agent_provider(
    *,
    environment: Mapping[str, str] | None = None,
    transport: LlamaCppTransport | None = None,
) -> AgentProvider | None:
    """Create the selected local provider or no provider when disabled."""
    settings = load_agent_provider_settings(environment)

    if settings is None:
        return None

    return LlamaCppAgentProvider(
        settings=settings,
        transport=(
            transport if transport is not None else HttpLlamaCppTransport()
        ),
    )
