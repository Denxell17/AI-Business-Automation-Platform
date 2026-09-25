"""Validated settings for the future webhook integration boundary.

This module only parses configuration. The sender must validate the resolved
network destination and any redirect again immediately before connecting.
"""

import ipaddress
import os
import re
from collections.abc import Mapping
from typing import TypedDict
from urllib.parse import urlsplit


_HOST_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class IntegrationSettings(TypedDict):
    runtime_environment: str
    enabled: bool
    private_development_network: bool
    base_url: str | None
    workflow_path: str | None
    allowed_hosts: tuple[str, ...]
    outbound_secret: str | None
    inbound_secret: str | None
    connect_timeout_seconds: int
    read_timeout_seconds: int
    max_request_bytes: int
    max_response_bytes: int
    signature_ttl_seconds: int
    max_attempts: int
    retry_poll_seconds: int
    retry_lease_seconds: int
    retry_claim_limit: int


def _bounded_integer(
    environment: Mapping[str, str], name: str, default: int, maximum: int,
) -> int:
    value = environment.get(name, str(default)).strip()
    try:
        number = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive integer.") from error
    if not 1 <= number <= maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}.")
    return number


def _public_hostname(hostname: str) -> str:
    host = hostname.casefold()
    if not host or host.endswith(".") or not host.isascii():
        raise ValueError("Integration host must be a public DNS hostname.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("Integration host must be a public DNS hostname.")
    labels = host.split(".")
    if (
        len(host) > 253
        or len(labels) < 2
        or any(not _HOST_LABEL.fullmatch(label) for label in labels)
        or labels[-1].isdigit()
        or host.endswith((".local", ".localhost", ".internal"))
    ):
        raise ValueError("Integration host must be a public DNS hostname.")
    return host


def _allowed_hosts(value: str) -> tuple[str, ...]:
    hosts = tuple(_public_hostname(part.strip()) for part in value.split(","))
    if len(set(hosts)) != len(hosts):
        raise ValueError("ABAP_INTEGRATION_ALLOWED_HOSTS contains duplicates.")
    return hosts


def _base_url(value: str, allowed_hosts: tuple[str, ...]) -> str:
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("ABAP_N8N_BASE_URL is invalid.") from error
    if (
        parsed.scheme != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or port == 0
        or "\\" in value
        or any(ord(character) < 33 for character in value)
    ):
        raise ValueError("ABAP_N8N_BASE_URL must be a clean HTTPS origin.")
    host = _public_hostname(hostname)
    if host not in allowed_hosts:
        raise ValueError("ABAP_N8N_BASE_URL host is not allowlisted.")
    return f"https://{host}{f':{port}' if port is not None else ''}"


def _private_development_base_url(value: str) -> str:
    """Allow only the fixed private Compose service in non-production demos."""
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("Private n8n URL is invalid.") from error
    if (
        parsed.scheme != "http"
        or hostname != "n8n"
        or port != 5678
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or "\\" in value
        or any(ord(character) < 33 for character in value)
    ):
        raise ValueError("Private n8n URL must be http://n8n:5678.")
    return "http://n8n:5678"


def load_integration_settings(
    environment: Mapping[str, str] | None = None,
) -> IntegrationSettings:
    """Fail closed on unsafe settings without exposing values in errors."""
    selected = environment if environment is not None else os.environ
    runtime_environment = selected.get("ABAP_ENVIRONMENT", "local").strip()
    if runtime_environment not in {"local", "integration-test", "staging", "production"}:
        raise ValueError("ABAP_ENVIRONMENT must name a supported environment.")
    enabled_text = selected.get("ABAP_INTEGRATIONS_ENABLED", "false").strip().casefold()
    if enabled_text not in {"true", "false"}:
        raise ValueError("ABAP_INTEGRATIONS_ENABLED must be true or false.")
    enabled = enabled_text == "true"
    private_text = selected.get(
        "ABAP_N8N_PRIVATE_DEVELOPMENT_NETWORK", "false",
    ).strip().casefold()
    if private_text not in {"true", "false"}:
        raise ValueError("ABAP_N8N_PRIVATE_DEVELOPMENT_NETWORK must be true or false.")
    private_development_network = private_text == "true"
    if private_development_network and runtime_environment not in {
        "local", "integration-test",
    }:
        raise ValueError("Private n8n networking is limited to local and integration-test.")
    limits = {
        "connect_timeout_seconds": _bounded_integer(
            selected, "ABAP_WEBHOOK_CONNECT_TIMEOUT_SECONDS", 3, 30,
        ),
        "read_timeout_seconds": _bounded_integer(
            selected, "ABAP_WEBHOOK_READ_TIMEOUT_SECONDS", 15, 120,
        ),
        "max_request_bytes": _bounded_integer(
            selected, "ABAP_WEBHOOK_MAX_REQUEST_BYTES", 262144, 1048576,
        ),
        "max_response_bytes": _bounded_integer(
            selected, "ABAP_WEBHOOK_MAX_RESPONSE_BYTES", 262144, 1048576,
        ),
        "signature_ttl_seconds": _bounded_integer(
            selected, "ABAP_WEBHOOK_SIGNATURE_TTL_SECONDS", 300, 900,
        ),
        "max_attempts": _bounded_integer(
            selected, "ABAP_WEBHOOK_MAX_ATTEMPTS", 3, 10,
        ),
        "retry_poll_seconds": _bounded_integer(
            selected, "ABAP_WEBHOOK_RETRY_POLL_SECONDS", 10, 300,
        ),
        "retry_lease_seconds": _bounded_integer(
            selected, "ABAP_WEBHOOK_RETRY_LEASE_SECONDS", 30, 300,
        ),
        "retry_claim_limit": _bounded_integer(
            selected, "ABAP_WEBHOOK_RETRY_CLAIM_LIMIT", 25, 100,
        ),
    }
    if not enabled:
        return {
            "runtime_environment": runtime_environment,
            "enabled": False,
            "private_development_network": private_development_network,
            "base_url": None, "workflow_path": None,
            "allowed_hosts": (), "outbound_secret": None,
            "inbound_secret": None, **limits,
        }

    url_text = selected.get("ABAP_N8N_BASE_URL", "").strip()
    if not url_text:
        raise ValueError("ABAP_N8N_BASE_URL is required.")
    if private_development_network:
        if selected.get("ABAP_INTEGRATION_ALLOWED_HOSTS", "").strip() != "n8n":
            raise ValueError("Private n8n networking requires the exact n8n allowlist.")
        hosts = ("n8n",)
        base_url = _private_development_base_url(url_text)
    else:
        hosts_text = selected.get("ABAP_INTEGRATION_ALLOWED_HOSTS", "").strip()
        if not hosts_text:
            raise ValueError("ABAP_INTEGRATION_ALLOWED_HOSTS is required.")
        hosts = _allowed_hosts(hosts_text)
        base_url = _base_url(url_text, hosts)
    path = selected.get("ABAP_N8N_WORKFLOW_PATH", "").strip()
    if (
        not path.startswith("/") or path.startswith("//") or path == "/"
        or "?" in path or "#" in path or "\\" in path
        or any(ord(character) < 33 or ord(character) == 127 for character in path)
    ):
        raise ValueError("ABAP_N8N_WORKFLOW_PATH must be a clean absolute path.")
    outbound = selected.get("ABAP_OUTBOUND_WEBHOOK_SECRET", "").strip()
    inbound = selected.get("ABAP_INBOUND_WEBHOOK_SECRET", "").strip()
    if not outbound:
        raise ValueError("ABAP_OUTBOUND_WEBHOOK_SECRET is required.")
    if not inbound:
        raise ValueError("ABAP_INBOUND_WEBHOOK_SECRET is required.")
    if inbound == outbound:
        raise ValueError("Inbound and outbound webhook secrets must differ.")
    return {
        "runtime_environment": runtime_environment,
        "enabled": True,
        "private_development_network": private_development_network,
        "base_url": base_url, "workflow_path": path,
        "allowed_hosts": hosts, "outbound_secret": outbound,
        "inbound_secret": inbound, **limits,
    }
