import json
import unittest
from agent_provider import AgentProviderError

from llama_cpp_agent_provider import (
    HttpLlamaCppTransport,
    LlamaCppAgentProvider,
)


class RecordingTransport:
    def __init__(self):
        self.requests = []

    def post_json(self, **request):
        self.requests.append(request)
        return {
            "choices": [
                {
                    "message": {
                        "content": "  Generated local response.  ",
                    }
                }
            ]
        }


class DeterministicHttpResponse:
    def __init__(self, *, status=200, json_body=None):
        self.status = status
        self._body = json.dumps(
            json_body if json_body is not None else {"choices": []}
        ).encode("utf-8")

    def read(self, amount=-1):
        return self._body[:amount]


class RecordingHttpConnection:
    def __init__(self, response):
        self.response = response
        self.requests = []
        self.closed = False

    def request(self, method, url, body, headers):
        self.requests.append((method, url, body, headers))

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


class TestLlamaCppAgentProvider(unittest.TestCase):
    def test_generate_response_maps_one_bounded_chat_request(self):
        settings = {
            "provider": "llama_cpp",
            "model": "qwen2.5-3b-instruct-q4_k_m",
            "base_url": "http://127.0.0.1:8080/v1",
            "api_key": "synthetic-test-key",
            "connect_timeout_seconds": 2.0,
            "read_timeout_seconds": 90.0,
            "max_input_chars": 12000,
            "max_output_tokens": 256,
        }
        transport = RecordingTransport()
        provider = LlamaCppAgentProvider(
            settings=settings,
            transport=transport,
        )

        output = provider.generate_response(
            model_name="qwen2.5-3b-instruct-q4_k_m",
            system_prompt="  Protect customer data.  ",
            input_text="  Summarize this request.  ",
        )

        self.assertEqual(output, "Generated local response.")
        self.assertEqual(len(transport.requests), 1)

        request = transport.requests[0]
        self.assertEqual(
            request["url"],
            "http://127.0.0.1:8080/v1/chat/completions",
        )
        self.assertEqual(
            request["json_body"],
            {
                "model": "qwen2.5-3b-instruct-q4_k_m",
                "messages": [
                    {
                        "role": "system",
                        "content": "Protect customer data.",
                    },
                    {
                        "role": "user",
                        "content": "Summarize this request.",
                    },
                ],
                "max_tokens": 256,
                "stream": False,
            },
        )
        self.assertEqual(request["connect_timeout_seconds"], 2.0)
        self.assertEqual(request["read_timeout_seconds"], 90.0)
        self.assertEqual(request["max_response_bytes"], 65536)
        self.assertFalse(request["follow_redirects"])

    def test_configured_model_alias_is_required_and_sent(self):
        settings = {
            "provider": "llama_cpp",
            "model": "custom-local-model",
            "base_url": "http://127.0.0.1:8080/v1",
            "api_key": "synthetic-test-key",
            "connect_timeout_seconds": 2.0,
            "read_timeout_seconds": 90.0,
            "max_input_chars": 12000,
            "max_output_tokens": 256,
        }
        transport = RecordingTransport()
        provider = LlamaCppAgentProvider(
            settings=settings,
            transport=transport,
        )

        provider.generate_response(
            model_name="custom-local-model",
            system_prompt="System prompt",
            input_text="Input text",
        )

        self.assertEqual(
            transport.requests[0]["json_body"]["model"],
            "custom-local-model",
        )

    def test_oversized_input_is_rejected_without_transport_call(self):
        settings = {
            "provider": "llama_cpp",
            "model": "qwen2.5-3b-instruct-q4_k_m",
            "base_url": "http://127.0.0.1:8080/v1",
            "api_key": "synthetic-test-key",
            "connect_timeout_seconds": 2.0,
            "read_timeout_seconds": 90.0,
            "max_input_chars": 10,
            "max_output_tokens": 256,
        }
        transport = RecordingTransport()
        provider = LlamaCppAgentProvider(
            settings=settings,
            transport=transport,
        )

        with self.assertRaises(AgentProviderError):
            provider.generate_response(
                model_name="qwen2.5-3b-instruct-q4_k_m",
                system_prompt="12345",
                input_text="678901",
            )

        self.assertEqual(transport.requests, [])

    def test_http_transport_posts_to_revalidated_loopback_endpoint(self):
        connection = RecordingHttpConnection(
            DeterministicHttpResponse(
                json_body={"choices": [{"message": {"content": "ok"}}]}
            )
        )
        factory_calls = []

        def connection_factory(*arguments):
            factory_calls.append(arguments)
            return connection

        transport = HttpLlamaCppTransport(
            connection_factory=connection_factory,
        )

        response = transport.post_json(
            url="http://127.0.0.1:8080/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json_body={"model": "test-model"},
            connect_timeout_seconds=2.0,
            read_timeout_seconds=90.0,
            max_response_bytes=1024,
            follow_redirects=False,
        )

        self.assertEqual(
            response,
            {"choices": [{"message": {"content": "ok"}}]},
        )
        self.assertEqual(factory_calls, [("127.0.0.1", 8080, 2.0, 90.0)])
        self.assertEqual(len(connection.requests), 1)
        method, path, body, headers = connection.requests[0]
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/v1/chat/completions")
        self.assertEqual(body, b'{"model":"test-model"}')
        self.assertEqual(headers, {"Content-Type": "application/json"})
        self.assertTrue(connection.closed)

    def test_http_transport_rejects_redirect_response(self):
        connection = RecordingHttpConnection(
            DeterministicHttpResponse(status=302)
        )
        transport = HttpLlamaCppTransport(
            connection_factory=lambda *arguments: connection,
        )

        with self.assertRaises(ValueError):
            transport.post_json(
                url="http://127.0.0.1:8080/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json_body={"model": "test-model"},
                connect_timeout_seconds=2.0,
                read_timeout_seconds=90.0,
                max_response_bytes=1024,
                follow_redirects=False,
            )

        self.assertTrue(connection.closed)

    def test_http_transport_rejects_response_above_bound(self):
        connection = RecordingHttpConnection(
            DeterministicHttpResponse(
                json_body={"choices": "x" * 128}
            )
        )
        transport = HttpLlamaCppTransport(
            connection_factory=lambda *arguments: connection,
        )

        with self.assertRaises(ValueError):
            transport.post_json(
                url="http://127.0.0.1:8080/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json_body={"model": "test-model"},
                connect_timeout_seconds=2.0,
                read_timeout_seconds=90.0,
                max_response_bytes=32,
                follow_redirects=False,
            )

        self.assertTrue(connection.closed)

    def test_http_transport_rejects_non_loopback_destination(self):
        transport = HttpLlamaCppTransport(
            connection_factory=lambda *arguments: self.fail(
                "A blocked destination must not open a connection."
            ),
        )

        with self.assertRaises(ValueError):
            transport.post_json(
                url="http://192.168.1.10:8080/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json_body={"model": "test-model"},
                connect_timeout_seconds=2.0,
                read_timeout_seconds=90.0,
                max_response_bytes=1024,
                follow_redirects=False,
            )


if __name__ == "__main__":
    unittest.main()
