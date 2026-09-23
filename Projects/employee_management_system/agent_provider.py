from enum import StrEnum
from typing import Protocol


class AgentProviderFailureCode(StrEnum):
    """Stable safe categories for provider failures."""

    PROVIDER_ERROR = "provider_error"
    INVALID_REQUEST = "invalid_request"
    INPUT_TOO_LARGE = "input_too_large"
    CONNECTION_REFUSED = "connection_refused"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    AUTHENTICATION_FAILED = "authentication_failed"
    PROVIDER_LOADING = "provider_loading"
    PROVIDER_BUSY = "provider_busy"
    PROVIDER_SERVER_ERROR = "provider_server_error"
    REQUEST_REJECTED = "request_rejected"
    REDIRECT_BLOCKED = "redirect_blocked"
    REQUEST_TOO_LARGE = "request_too_large"
    RESPONSE_TOO_LARGE = "response_too_large"
    MALFORMED_RESPONSE = "malformed_response"
    BLANK_RESPONSE = "blank_response"


class AgentProviderError(RuntimeError):
    """Represent a safe failure reported by an AI provider."""

    def __init__(
        self,
        message: str,
        code: AgentProviderFailureCode = (
            AgentProviderFailureCode.PROVIDER_ERROR
        ),
    ) -> None:
        super().__init__(message)
        self.code = code


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
