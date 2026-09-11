import unittest

from agent_provider_config import (
    DEFAULT_OPENAI_TIMEOUT_SECONDS,
    load_openai_provider_settings,
)


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


if __name__ == "__main__":
    unittest.main()