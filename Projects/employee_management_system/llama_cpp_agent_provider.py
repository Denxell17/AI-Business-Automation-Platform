"""llama.cpp implementation of ABAP's provider-neutral agent boundary."""

import http.client
import json
import socket
from collections.abc import Callable, Mapping
from typing import Any, Protocol
from urllib.parse import urlsplit

from agent_provider import AgentProviderError
from agent_provider_config import LocalProviderSettings


SAFE_LLAMA_CPP_PROVIDER_ERROR_MESSAGE = (
    "The local AI provider could not complete the request."
)
MAX_LLAMA_CPP_RESPONSE_BYTES = 65536
MAX_LLAMA_CPP_REQUEST_BYTES = 131072


class LlamaCppTransport(Protocol):
    """Send one bounded JSON request to the local llama.cpp server."""

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        json_body: Mapping[str, Any],
        connect_timeout_seconds: float,
        read_timeout_seconds: float,
        max_response_bytes: int,
        follow_redirects: bool,
    ) -> Mapping[str, Any]:
        """Send a request and return its decoded JSON response."""


class LlamaCppResponse(Protocol):
    """Represent the bounded portion of an HTTP response that ABAP needs."""

    status: int

    def read(self, amount: int = -1) -> bytes:
        """Read at most the requested number of response bytes."""


class LlamaCppConnection(Protocol):
    """Represent one loopback HTTP connection."""

    def request(
        self,
        method: str,
        url: str,
        body: bytes,
        headers: Mapping[str, str],
    ) -> None:
        """Send one request."""

    def getresponse(self) -> LlamaCppResponse:
        """Return the server response."""

    def close(self) -> None:
        """Close the connection."""


class _LoopbackHTTPConnection(http.client.HTTPConnection):
    """Keep connect and read timeouts separate for the fixed loopback server."""

    def __init__(
        self,
        hostname: str,
        port: int,
        connect_timeout_seconds: float,
        read_timeout_seconds: float,
    ) -> None:
        super().__init__(
            hostname,
            port=port,
            timeout=connect_timeout_seconds,
        )
        self._read_timeout_seconds = read_timeout_seconds

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self.host, self.port),
            self.timeout,
        )
        self.sock.settimeout(self._read_timeout_seconds)


def _loopback_connection(
    hostname: str,
    port: int,
    connect_timeout_seconds: float,
    read_timeout_seconds: float,
) -> LlamaCppConnection:
    return _LoopbackHTTPConnection(
        hostname,
        port,
        connect_timeout_seconds,
        read_timeout_seconds,
    )


def _loopback_request_path(url: str) -> str:
    """Revalidate the fixed local API destination before each connection."""
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        raise ValueError("Local provider destination is invalid.") from None

    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or port != 8080
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path != "/v1/chat/completions"
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Local provider destination is invalid.")

    return parsed.path


class HttpLlamaCppTransport:
    """Send bounded, redirect-free requests to the fixed local llama.cpp API."""

    def __init__(
        self,
        connection_factory: Callable[
            [str, int, float, float], LlamaCppConnection
        ] = _loopback_connection,
    ) -> None:
        self._connection_factory = connection_factory

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        json_body: Mapping[str, Any],
        connect_timeout_seconds: float,
        read_timeout_seconds: float,
        max_response_bytes: int,
        follow_redirects: bool,
    ) -> Mapping[str, Any]:
        """Post one JSON body without redirects and return bounded JSON."""
        if follow_redirects:
            raise ValueError("Local provider redirects are not permitted.")

        request_path = _loopback_request_path(url)
        body = json.dumps(
            json_body,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        if len(body) > MAX_LLAMA_CPP_REQUEST_BYTES:
            raise ValueError("Local provider request is too large.")

        connection = self._connection_factory(
            "127.0.0.1",
            8080,
            connect_timeout_seconds,
            read_timeout_seconds,
        )
        try:
            connection.request("POST", request_path, body, headers)
            response = connection.getresponse()
            response_body = response.read(max_response_bytes + 1)

            if len(response_body) > max_response_bytes:
                raise ValueError("Local provider response is too large.")
            if not 200 <= response.status < 300:
                raise ValueError("Local provider response was unsuccessful.")

            try:
                decoded = json.loads(response_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ValueError("Local provider response is invalid.") from None

            if not isinstance(decoded, Mapping):
                raise ValueError("Local provider response is invalid.")
            return decoded
        finally:
            connection.close()


class LlamaCppAgentProvider:
    """Generate Agent Template responses through local llama.cpp."""

    def __init__(
        self,
        *,
        settings: LocalProviderSettings,
        transport: LlamaCppTransport,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def generate_response(
        self,
        *,
        model_name: str,
        system_prompt: str,
        input_text: str,
    ) -> str:
        """Generate one bounded, non-streaming local chat response."""
        if (
            not isinstance(model_name, str)
            or model_name.strip() != self._settings["model"]
            or not isinstance(system_prompt, str)
            or not system_prompt.strip()
            or not isinstance(input_text, str)
            or not input_text.strip()
        ):
            raise AgentProviderError(
                SAFE_LLAMA_CPP_PROVIDER_ERROR_MESSAGE
            )

        system_message = system_prompt.strip()
        user_message = input_text.strip()

        if (
            len(system_message) + len(user_message)
            > self._settings["max_input_chars"]
        ):
            raise AgentProviderError(
                SAFE_LLAMA_CPP_PROVIDER_ERROR_MESSAGE
            )

        try:
            response = self._transport.post_json(
                url=f'{self._settings["base_url"]}/chat/completions',
                headers={
                    "Authorization": (
                        f'Bearer {self._settings["api_key"]}'
                    ),
                    "Content-Type": "application/json",
                },
                json_body={
                    "model": model_name.strip(),
                    "messages": [
                        {
                            "role": "system",
                            "content": system_message,
                        },
                        {
                            "role": "user",
                            "content": user_message,
                        },
                    ],
                    "max_tokens": self._settings["max_output_tokens"],
                    "stream": False,
                },
                connect_timeout_seconds=(
                    self._settings["connect_timeout_seconds"]
                ),
                read_timeout_seconds=(
                    self._settings["read_timeout_seconds"]
                ),
                max_response_bytes=MAX_LLAMA_CPP_RESPONSE_BYTES,
                follow_redirects=False,
            )
        except Exception:
            raise AgentProviderError(
                SAFE_LLAMA_CPP_PROVIDER_ERROR_MESSAGE
            ) from None

        try:
            output_text = response["choices"][0]["message"]["content"]
        except (IndexError, KeyError, TypeError):
            raise AgentProviderError(
                SAFE_LLAMA_CPP_PROVIDER_ERROR_MESSAGE
            ) from None

        if not isinstance(output_text, str) or not output_text.strip():
            raise AgentProviderError(
                SAFE_LLAMA_CPP_PROVIDER_ERROR_MESSAGE
            )

        return output_text.strip()
