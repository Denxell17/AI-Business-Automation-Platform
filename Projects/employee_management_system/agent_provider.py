from typing import Protocol


class AgentProviderError(RuntimeError):
    """Represent a safe failure reported by an AI provider."""


class AgentProvider(Protocol):
    """Define the provider operation required by ABAP."""

    def generate_response(
        self,
        *,
        model_name: str,
        system_prompt: str,
        input_text: str,
    ) -> str:
        """Generate one response using an Agent Template."""
        ...