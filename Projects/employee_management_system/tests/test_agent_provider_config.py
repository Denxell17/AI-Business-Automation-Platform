import unittest

from agent_provider_config import (
    DEFAULT_OPENAI_TIMEOUT_SECONDS,
    load_agent_provider_settings,
    load_openai_provider_settings,
)


class TestAgentProviderConfig(unittest.TestCase):
    def test_invalid_provider_states_are_rejected(self):
        invalid_environments = (
            {"ABAP_INTEGRATIONS_ENABLED": "true"},
            {"ABAP_EXTERNAL_PROVIDER": "llama_cpp"},
            {"ABAP_INTEGRATIONS_ENABLED": "yes"},
            {"ABAP_INTEGRATIONS_ENABLED": " true"},
            {"ABAP_EXTERNAL_PROVIDER": " llama_cpp"},
            {"ABAP_EXTERNAL_PROVIDER": "unknown"},
        )

        for environment in invalid_environments:
            with self.subTest(environment=environment):
                with self.assertRaises(ValueError):
                    load_agent_provider_settings(environment)

    def test_enabled_local_provider_loads_default_limits(self):
        settings = load_agent_provider_settings(
            {
                "ABAP_INTEGRATIONS_ENABLED": "true",
                "ABAP_EXTERNAL_PROVIDER": "llama_cpp",
                "ABAP_LOCAL_AI_MODEL": "qwen2.5-3b-instruct-q4_k_m",
                "ABAP_LLAMA_CPP_BASE_URL": "http://127.0.0.1:8080/v1",
                "ABAP_LLAMA_CPP_API_KEY": "synthetic-test-key",
            }
        )

        self.assertIsNotNone(settings)
        self.assertEqual(settings["provider"], "llama_cpp")
        self.assertEqual(settings["model"], "qwen2.5-3b-instruct-q4_k_m")
        self.assertEqual(settings["base_url"], "http://127.0.0.1:8080/v1")
        self.assertEqual(settings["connect_timeout_seconds"], 2.0)
        self.assertEqual(settings["read_timeout_seconds"], 90.0)
        self.assertEqual(settings["max_input_chars"], 12000)
        self.assertEqual(settings["max_output_tokens"], 256)

    def test_enabled_local_provider_loads_explicit_limits(self):
        settings = load_agent_provider_settings(
            {
                "ABAP_INTEGRATIONS_ENABLED": "true",
                "ABAP_EXTERNAL_PROVIDER": "llama_cpp",
                "ABAP_LOCAL_AI_MODEL": "qwen2.5-3b-instruct-q4_k_m",
                "ABAP_LLAMA_CPP_BASE_URL": "http://127.0.0.1:8080/v1",
                "ABAP_LLAMA_CPP_API_KEY": "synthetic-test-key",
                "ABAP_LOCAL_AI_CONNECT_TIMEOUT_SECONDS": "3",
                "ABAP_LOCAL_AI_READ_TIMEOUT_SECONDS": "45.5",
                "ABAP_LOCAL_AI_MAX_INPUT_CHARS": "6000",
                "ABAP_LOCAL_AI_MAX_OUTPUT_TOKENS": "128",
            }
        )

        self.assertEqual(settings["connect_timeout_seconds"], 3.0)
        self.assertEqual(settings["read_timeout_seconds"], 45.5)
        self.assertEqual(settings["max_input_chars"], 6000)
        self.assertEqual(settings["max_output_tokens"], 128)

    def test_enabled_provider_rejects_unsafe_model_or_key(self):
        valid_environment = {
            "ABAP_INTEGRATIONS_ENABLED": "true",
            "ABAP_EXTERNAL_PROVIDER": "llama_cpp",
            "ABAP_LOCAL_AI_MODEL": "qwen2.5-3b-instruct-q4_k_m",
            "ABAP_LLAMA_CPP_BASE_URL": "http://127.0.0.1:8080/v1",
            "ABAP_LLAMA_CPP_API_KEY": "synthetic-test-key",
        }
        invalid_values = (
            ("ABAP_LOCAL_AI_MODEL", ""),
            ("ABAP_LOCAL_AI_MODEL", " qwen2.5-3b-instruct-q4_k_m "),
            ("ABAP_LOCAL_AI_MODEL", "../private/model.gguf"),
            ("ABAP_LLAMA_CPP_API_KEY", ""),
            ("ABAP_LLAMA_CPP_API_KEY", " synthetic-test-key "),
            ("ABAP_LLAMA_CPP_API_KEY", "synthetic test key"),
        )

        for name, value in invalid_values:
            with self.subTest(name=name, value=value):
                environment = {**valid_environment, name: value}
                with self.assertRaises(ValueError):
                    load_agent_provider_settings(environment)

    def test_enabled_provider_rejects_non_loopback_base_urls(self):
        valid_environment = {
            "ABAP_INTEGRATIONS_ENABLED": "true",
            "ABAP_EXTERNAL_PROVIDER": "llama_cpp",
            "ABAP_LOCAL_AI_MODEL": "qwen2.5-3b-instruct-q4_k_m",
            "ABAP_LLAMA_CPP_BASE_URL": "http://127.0.0.1:8080/v1",
            "ABAP_LLAMA_CPP_API_KEY": "synthetic-test-key",
        }
        invalid_base_urls = (
            "http://localhost:8080/v1",
            "http://127.0.0.1:8081/v1",
            "https://127.0.0.1:8080/v1",
            "http://192.168.1.10:8080/v1",
            " http://127.0.0.1:8080/v1",
            "http://127.0.0.1:8080/v1/",
        )

        for base_url in invalid_base_urls:
            with self.subTest(base_url=base_url):
                environment = {
                    **valid_environment,
                    "ABAP_LLAMA_CPP_BASE_URL": base_url,
                }
                with self.assertRaises(ValueError):
                    load_agent_provider_settings(environment)

    def test_enabled_provider_rejects_invalid_limits(self):
        valid_environment = {
            "ABAP_INTEGRATIONS_ENABLED": "true",
            "ABAP_EXTERNAL_PROVIDER": "llama_cpp",
            "ABAP_LOCAL_AI_MODEL": "qwen2.5-3b-instruct-q4_k_m",
            "ABAP_LLAMA_CPP_BASE_URL": "http://127.0.0.1:8080/v1",
            "ABAP_LLAMA_CPP_API_KEY": "synthetic-test-key",
        }
        invalid_values = (
            ("ABAP_LOCAL_AI_CONNECT_TIMEOUT_SECONDS", " 2"),
            ("ABAP_LOCAL_AI_CONNECT_TIMEOUT_SECONDS", "slow"),
            ("ABAP_LOCAL_AI_CONNECT_TIMEOUT_SECONDS", "nan"),
            ("ABAP_LOCAL_AI_CONNECT_TIMEOUT_SECONDS", "0.5"),
            ("ABAP_LOCAL_AI_CONNECT_TIMEOUT_SECONDS", "11"),
            ("ABAP_LOCAL_AI_READ_TIMEOUT_SECONDS", "121"),
            ("ABAP_LOCAL_AI_MAX_INPUT_CHARS", "0"),
            ("ABAP_LOCAL_AI_MAX_INPUT_CHARS", "12001"),
            ("ABAP_LOCAL_AI_MAX_INPUT_CHARS", "12.5"),
            ("ABAP_LOCAL_AI_MAX_OUTPUT_TOKENS", "0"),
            ("ABAP_LOCAL_AI_MAX_OUTPUT_TOKENS", "257"),
            ("ABAP_LOCAL_AI_MAX_OUTPUT_TOKENS", "128.0"),
        )

        for name, value in invalid_values:
            with self.subTest(name=name):
                environment = {**valid_environment, name: value}
                with self.assertRaisesRegex(
                    ValueError,
                    r"^Invalid local provider configuration\.$",
                ) as context:
                    load_agent_provider_settings(environment)

                self.assertIsNone(context.exception.__cause__)


class TestOpenAIProviderConfig(unittest.TestCase):
    def test_required_api_key_and_default_timeout_are_loaded(self):
        settings = load_openai_provider_settings(
            {
                "OPENAI_API_KEY": "test-api-key",
            }
        )

        self.assertEqual(settings["api_key"], "test-api-key")
        self.assertEqual(
            settings["timeout_seconds"],
            DEFAULT_OPENAI_TIMEOUT_SECONDS,
        )

    def test_values_are_trimmed_and_explicit_timeout_is_loaded(self):
        settings = load_openai_provider_settings(
            {
                "OPENAI_API_KEY": "  test-api-key  ",
                "OPENAI_TIMEOUT_SECONDS": " 12.5 ",
            }
        )

        self.assertEqual(settings["api_key"], "test-api-key")
        self.assertEqual(settings["timeout_seconds"], 12.5)

    def test_missing_api_key_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "OPENAI_API_KEY is required",
        ):
            load_openai_provider_settings({})

    def test_non_numeric_timeout_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "OPENAI_TIMEOUT_SECONDS must be a number",
        ):
            load_openai_provider_settings(
                {
                    "OPENAI_API_KEY": "test-api-key",
                    "OPENAI_TIMEOUT_SECONDS": "slow",
                }
            )

    def test_timeout_outside_safe_range_is_rejected(self):
        for timeout_value in ("0.5", "121"):
            with self.subTest(timeout_value=timeout_value):
                with self.assertRaisesRegex(
                    ValueError,
                    "must be between 1 and 120 seconds",
                ):
                    load_openai_provider_settings(
                        {
                            "OPENAI_API_KEY": "test-api-key",
                            "OPENAI_TIMEOUT_SECONDS": timeout_value,
                        }
                    )

    def test_non_finite_timeout_is_rejected(self):
        for timeout_value in ("nan", "inf", "-inf"):
            with self.subTest(timeout_value=timeout_value):
                with self.assertRaisesRegex(
                    ValueError,
                    "must be between 1 and 120 seconds",
                ):
                    load_openai_provider_settings(
                        {
                            "OPENAI_API_KEY": "test-api-key",
                            "OPENAI_TIMEOUT_SECONDS": timeout_value,
                        }
                    )

    def test_integrations_are_disabled_and_no_provider_settings_load_by_default(
        self,
    ):
        settings = load_agent_provider_settings({})

        self.assertIsNone(settings)


if __name__ == "__main__":
    unittest.main()
