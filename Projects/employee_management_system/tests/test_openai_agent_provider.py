import unittest
from types import SimpleNamespace
from unittest.mock import patch

from openai import OpenAIError

from agent_provider import AgentProviderError
from openai_agent_provider import (
    SAFE_OPENAI_PROVIDER_ERROR_MESSAGE,
    OpenAIAgentProvider,
)


class DeterministicResponsesClient:
    def __init__(
        self,
        output_text="Deterministic OpenAI response.",
        error=None,
    ):
        self.output_text = output_text
        self.error = error
        self.calls = []

    def create(self, **request):
        self.calls.append(request)

        if self.error is not None:
            raise self.error

        return SimpleNamespace(output_text=self.output_text)


class DeterministicOpenAIClient:
    def __init__(
        self,
        output_text="Deterministic OpenAI response.",
        error=None,
    ):
        self.responses = DeterministicResponsesClient(
            output_text=output_text,
            error=error,
        )


class TestOpenAIAgentProvider(unittest.TestCase):
    def setUp(self):
        self.settings = {
            "api_key": "test-api-key",
            "timeout_seconds": 12.5,
        }

    def test_constructor_configures_safe_timeout_and_no_retries(self):
        with patch(
            "openai_agent_provider.OpenAI"
        ) as client_constructor:
            OpenAIAgentProvider(settings=self.settings)

        client_constructor.assert_called_once_with(
            api_key="test-api-key",
            timeout=12.5,
            max_retries=0,
        )

    def test_generate_response_sends_expected_responses_request(self):
        client = DeterministicOpenAIClient(
            output_text="  Generated business response.  "
        )
        provider = OpenAIAgentProvider(
            settings=self.settings,
            client=client,
        )

        output = provider.generate_response(
            model_name="  test-model  ",
            system_prompt="  Protect customer data.  ",
            input_text="  Summarize this request.  ",
        )

        self.assertEqual(
            output,
            "Generated business response.",
        )
        self.assertEqual(
            client.responses.calls,
            [
                {
                    "model": "test-model",
                    "instructions": "Protect customer data.",
                    "input": "Summarize this request.",
                    "store": False,
                }
            ],
        )

    def test_invalid_request_values_are_rejected_without_client_call(self):
        invalid_requests = (
            {
                "model_name": "",
                "system_prompt": "System prompt",
                "input_text": "Input text",
            },
            {
                "model_name": "test-model",
                "system_prompt": "   ",
                "input_text": "Input text",
            },
            {
                "model_name": "test-model",
                "system_prompt": "System prompt",
                "input_text": "",
            },
        )

        for request in invalid_requests:
            with self.subTest(request=request):
                client = DeterministicOpenAIClient()
                provider = OpenAIAgentProvider(
                    settings=self.settings,
                    client=client,
                )

                with self.assertRaisesRegex(
                    AgentProviderError,
                    SAFE_OPENAI_PROVIDER_ERROR_MESSAGE,
                ):
                    provider.generate_response(**request)

                self.assertEqual(client.responses.calls, [])

    def test_sdk_failure_becomes_safe_provider_error(self):
        unsafe_provider_detail = (
            "request failed with secret test-api-key"
        )
        client = DeterministicOpenAIClient(
            error=OpenAIError(unsafe_provider_detail)
        )
        provider = OpenAIAgentProvider(
            settings=self.settings,
            client=client,
        )

        with self.assertRaises(AgentProviderError) as context:
            provider.generate_response(
                model_name="test-model",
                system_prompt="System prompt",
                input_text="Input text",
            )

        self.assertEqual(
            str(context.exception),
            SAFE_OPENAI_PROVIDER_ERROR_MESSAGE,
        )
        self.assertNotIn(
            unsafe_provider_detail,
            str(context.exception),
        )

    def test_missing_or_blank_output_becomes_safe_provider_error(self):
        for output_text in (None, "", "   "):
            with self.subTest(output_text=output_text):
                client = DeterministicOpenAIClient(
                    output_text=output_text
                )
                provider = OpenAIAgentProvider(
                    settings=self.settings,
                    client=client,
                )

                with self.assertRaisesRegex(
                    AgentProviderError,
                    SAFE_OPENAI_PROVIDER_ERROR_MESSAGE,
                ):
                    provider.generate_response(
                        model_name="test-model",
                        system_prompt="System prompt",
                        input_text="Input text",
                    )


if __name__ == "__main__":
    unittest.main()