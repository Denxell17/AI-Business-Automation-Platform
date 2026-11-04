"""Explicit model registry; text-only adapters never grant tool authority."""

import http.client
import hashlib
import threading
from decimal import Decimal
import json
import os
import re
import socket
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from agent_provider import AgentProviderError, AgentProviderFailureCode as Code
from agent_provider_factory import create_agent_provider


@dataclass(frozen=True)
class Model:
    id: str
    provider: str
    model: str
    key: str = field(default="", repr=False)
    endpoint: str = ""
    available: bool = False
    status: str = "Unverified"

    def public(self):
        return {"id": self.id, "provider": self.provider, "model": self.model,
                "available": self.available, "status": self.status}


def configured_models(environment=None):
    env = os.environ if environment is None else environment
    from assistant_cloud_config import evidence, verified
    records = evidence(env)
    result = []
    for provider, setting, key in (
        ("gemini", "ABAP_ASSISTANT_GEMINI_MODELS", "ABAP_ASSISTANT_GEMINI_KEY"),
        ("openrouter", "ABAP_ASSISTANT_OPENROUTER_MODELS", "ABAP_ASSISTANT_OPENROUTER_KEY"),
        ("compatible", "ABAP_ASSISTANT_COMPATIBLE_MODELS", "ABAP_ASSISTANT_COMPATIBLE_KEY"),
    ):
        names = env.get(setting, "").split(",")
        for name in names:
            name = name.strip()
            if not name:
                continue
            if len(name) > 100 or not re.fullmatch(r"[A-Za-z0-9_./:-]+", name) or ".." in name:
                raise ValueError("Invalid assistant model configuration.")
            # No paid OpenRouter identifiers or automatic routing.
            if provider == "openrouter" and not name.endswith(":free"):
                raise ValueError("Only explicit :free OpenRouter models are allowed.")
            endpoint = env.get("ABAP_ASSISTANT_COMPATIBLE_URL", "") if provider == "compatible" else ""
            if provider == "compatible":
                parsed = urlsplit(endpoint)
                if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                        or parsed.password or parsed.query or parsed.fragment):
                    raise ValueError("Compatible provider requires an operator-controlled HTTPS URL.")
            # Operator must verify remote billing/quota settings before enabling calls.
            credential = env.get(key, '')
            if env.get(key + '_FILE'):
                try:
                    with Path(env[key + '_FILE']).open('r', encoding='utf-8') as secret_file:
                        credential = secret_file.read(4097).strip()
                except OSError:
                    raise ValueError('Assistant credential file is unavailable.') from None
            if len(credential) > 4096 or '\n' in credential or '\r' in credential:
                raise ValueError('Assistant credential is invalid.')
            available = (bool(credential) and env.get("ABAP_ASSISTANT_REMOTE_APPROVED") == "true"
                         and verified(f"{provider}:{name}", records)
                         and records[f"{provider}:{name}"].get("key_fingerprint") == hashlib.sha256(credential.encode()).hexdigest())
            if provider in ('gemini', 'compatible'):
                available = (available and env.get('ABAP_ASSISTANT_'+provider.upper()+'_FREE_ACCOUNT_REVIEWED') == 'true'
                             and name in {value.strip() for value in env.get('ABAP_ASSISTANT_'+provider.upper()+'_FREE_MODELS','').split(',')}) 
            result.append(Model(f"{provider}:{name}", provider, name, credential, endpoint, available, "Live validated (last 24h)" if available else "Unverified or unavailable"))
    if env.get("ABAP_EXTERNAL_PROVIDER") == "llama_cpp" and env.get("ABAP_ASSISTANT_ALLOW_LOCAL_DEVELOPMENT") == "true" and env.get("ABAP_ENVIRONMENT", "local") != "production":
        name = env.get("ABAP_LOCAL_AI_MODEL", "qwen")
        result.insert(0, Model("local", "local", name, available=env.get("ABAP_INTEGRATIONS_ENABLED") == "true"))
    if len(result) > 20 or len({m.id for m in result}) != len(result):
        raise ValueError("Invalid assistant model registry.")
    return result


class Gateway:
    def __init__(self, models=None, transport=None):
        self.models = configured_models() if models is None else models
        self.transport = transport or self._post

    def select(self, model_id):
        for model in self.models:
            if model.id == model_id and model.available:
                return model
        raise ValueError("Selected model is unavailable; select another configured model.")

    @staticmethod
    def _post(url, headers, body):
        parsed = urlsplit(url)
        connection = http.client.HTTPSConnection(parsed.hostname, parsed.port, timeout=30)
        deadline = None
        active_socket = None
        def abort():
            try:
                handle = active_socket or connection.sock
                if handle is not None:
                    handle.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        try:
            payload = json.dumps(body).encode("utf-8")
            if len(payload) > 131072:
                raise AgentProviderError("Request is too large.", Code.REQUEST_TOO_LARGE)
            connection.request("POST", parsed.path, payload, {"Content-Type": "application/json", **headers})
            active_socket = connection.sock
            deadline = threading.Timer(45, abort)
            deadline.daemon = True
            deadline.start()
            response = connection.getresponse()
            if response.status != 200:
                code = Code.PROVIDER_BUSY if response.status in (402, 429) else Code.PROVIDER_ERROR
                raise AgentProviderError("Provider unavailable. Select another configured model.", code)
            raw = response.read(262145)
            if len(raw) > 262144:
                raise AgentProviderError("Provider response too large.", Code.RESPONSE_TOO_LARGE)
            return json.loads(raw)
        except (TimeoutError, socket.timeout):
            raise AgentProviderError("Provider timed out.", Code.TIMEOUT) from None
        except AgentProviderError:
            raise
        except Exception:
            raise AgentProviderError("Provider request failed.") from None
        finally:
            if deadline is not None:
                deadline.cancel()
            connection.close()

    def generate(self, model_id, system, text):
        model = self.select(model_id)
        try:
            if model.provider == "local":
                provider = create_agent_provider()
                if provider is None:
                    raise ValueError()
                answer = provider.generate_response(model_name=model.model, system_prompt=system, input_text=text)
                usage = {}
            elif model.provider == "gemini":
                response = self.transport(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model.model}:generateContent",
                    {"x-goog-api-key": model.key},
                    {"systemInstruction": {"parts": [{"text": system}]},
                     "contents": [{"role": "user", "parts": [{"text": text}]}],
                     "generationConfig": {"maxOutputTokens": 2048}})
                answer = "".join(p.get("text", "") for p in response["candidates"][0]["content"]["parts"])
                usage = response.get("usageMetadata", {})
            else:
                response = self.transport(
                    "https://openrouter.ai/api/v1/chat/completions" if model.provider == "openrouter" else model.endpoint,
                    {"Authorization": f"Bearer {model.key}"},
                    {"model": model.model, "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": text}], "max_tokens": 2048, "stream": False,
                     **({"provider":{"max_price":{"prompt":0,"completion":0}, "allow_fallbacks":False}} if model.provider == "openrouter" else {})})
                answer = response["choices"][0]["message"]["content"]
                usage = response.get("usage", {})
                if model.provider == 'openrouter' and Decimal(str(usage.get('cost', 0))) > 0:
                    raise AgentProviderError('Unexpected provider cost; model requires review.', Code.REQUEST_REJECTED)
            if not isinstance(answer, str) or not answer.strip() or len(answer) > 50000:
                raise ValueError()
            # Keep numeric usage only; raw responses may contain provider metadata/secrets.
            safe_usage = {k: v for k, v in usage.items() if k in {
                "prompt_tokens", "completion_tokens", "total_tokens", "cost",
                "promptTokenCount", "candidatesTokenCount", "totalTokenCount"}
                and type(v) in (int, float) and 0 <= v < 1e12}
            return answer.strip(), safe_usage
        except AgentProviderError:
            raise
        except Exception:
            raise AgentProviderError("Provider returned an invalid response.", Code.MALFORMED_RESPONSE) from None
