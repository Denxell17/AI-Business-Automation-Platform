"""OpenAI implementation of ABAP's provider-neutral agent boundary."""

from typing import Any

from openai import OpenAI, OpenAIError

from agent_provider import AgentProviderError
from agent_provider_config import (
    OpenAIProviderSettings,
    load_openai_provider_settings,
)


SAFE_OPENAI_PROVIDER_ERROR_MESSAGE = (
    "The OpenAI provider could not complete the request."
)


class OpenAIAgentProvider:
    """Generate Agent Template responses through OpenAI."""

    def __init__(
        self,
        settings: OpenAIProviderSettings | None = None,
        client: Any | None = None,
    ) -> None:
        selected_settings = (
            settings
            if settings is not None
            else load_openai_provider_settings()
        )

        self._client = (
            client
            if client is not None
            else OpenAI(
                api_key=selected_settings["api_key"],
                timeout=selected_settings["timeout_seconds"],
                max_retries=0,
            )
        )

    def generate_response(
        self,
        *,
        model_name: str,
        system_prompt: str,
        input_text: str,
    ) -> str:
        """Generate one response with the OpenAI Responses API."""
        if (
            not isinstance(model_name, str)
            or not model_name.strip()
            or not isinstance(system_prompt, str)
            or not system_prompt.strip()
            or not isinstance(input_text, str)
            or not input_text.strip()
        ):
            raise AgentProviderError(
                SAFE_OPENAI_PROVIDER_ERROR_MESSAGE
            )

        try:
            response = self._client.responses.create(
                model=model_name.strip(),
                instructions=system_prompt.strip(),
                input=input_text.strip(),
                store=False,
            )
        except OpenAIError as error:
            raise AgentProviderError(
                SAFE_OPENAI_PROVIDER_ERROR_MESSAGE
            ) from error

        output_text = getattr(response, "output_text", None)

        if (
            not isinstance(output_text, str)
            or not output_text.strip()
        ):
            raise AgentProviderError(
                SAFE_OPENAI_PROVIDER_ERROR_MESSAGE
            )

        return output_text.strip()