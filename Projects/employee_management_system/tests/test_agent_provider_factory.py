import unittest

from agent_provider_factory import create_agent_provider
from llama_cpp_agent_provider import (
    HttpLlamaCppTransport,
    LlamaCppAgentProvider,
)


class TestAgentProviderFactory(unittest.TestCase):
    def test_disabled_configuration_returns_no_provider(self):
        provider = create_agent_provider(
            environment={},
            transport=object(),
        )

        self.assertIsNone(provider)

    def test_enabled_llama_cpp_configuration_creates_local_provider(self):
        provider = create_agent_provider(
            environment={
                "ABAP_INTEGRATIONS_ENABLED": "true",
                "ABAP_EXTERNAL_PROVIDER": "llama_cpp",
                "ABAP_LOCAL_AI_MODEL": "qwen2.5-3b-instruct-q4_k_m",
                "ABAP_LLAMA_CPP_BASE_URL": (
                    "http://127.0.0.1:8080/v1"
                ),
                "ABAP_LLAMA_CPP_API_KEY": "synthetic-test-key",
            },
            transport=object(),
        )

        self.assertIsInstance(provider, LlamaCppAgentProvider)

    def test_enabled_configuration_uses_loopback_transport_by_default(self):
        provider = create_agent_provider(
            environment={
                "ABAP_INTEGRATIONS_ENABLED": "true",
                "ABAP_EXTERNAL_PROVIDER": "llama_cpp",
                "ABAP_LOCAL_AI_MODEL": "qwen2.5-3b-instruct-q4_k_m",
                "ABAP_LLAMA_CPP_BASE_URL": (
                    "http://127.0.0.1:8080/v1"
                ),
                "ABAP_LLAMA_CPP_API_KEY": "synthetic-test-key",
            }
        )

        self.assertIsInstance(provider, LlamaCppAgentProvider)
        self.assertIsInstance(provider._transport, HttpLlamaCppTransport)


if __name__ == "__main__":
    unittest.main()
