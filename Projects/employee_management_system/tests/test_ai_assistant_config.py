import unittest

from ai_assistant_config import load_ai_assistant_settings
from ai_assistant_service import (
    MAX_AI_ASSISTANT_MODEL_NAME_LENGTH,
)


class TestAiAssistantConfig(unittest.TestCase):
    def test_explicit_model_name_is_loaded_and_trimmed(self):
        settings = load_ai_assistant_settings(
            {
                "AI_ASSISTANT_MODEL": (
                    "  test-assistant-model  "
                ),
            }
        )

        self.assertEqual(
            settings,
            {
                "model_name": "test-assistant-model",
            },
        )

    def test_missing_model_name_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "AI_ASSISTANT_MODEL is required",
        ):
            load_ai_assistant_settings({})

    def test_blank_model_name_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "AI_ASSISTANT_MODEL is required",
        ):
            load_ai_assistant_settings(
                {
                    "AI_ASSISTANT_MODEL": "   ",
                }
            )

    def test_oversized_model_name_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "must be no more than 100 characters",
        ):
            load_ai_assistant_settings(
                {
                    "AI_ASSISTANT_MODEL": (
                        "x"
                        * (
                            MAX_AI_ASSISTANT_MODEL_NAME_LENGTH
                            + 1
                        )
                    ),
                }
            )


if __name__ == "__main__":
    unittest.main()