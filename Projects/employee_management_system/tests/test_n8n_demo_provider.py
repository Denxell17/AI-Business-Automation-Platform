import http.client
import json
import threading
import unittest
from http import HTTPStatus
from http.server import ThreadingHTTPServer

from n8n_demo_provider import DemoActionHandler


class TestN8nDemoProvider(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), DemoActionHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, body: bytes, content_type: str = "application/json"):
        connection = http.client.HTTPConnection(*self.server.server_address)
        connection.request("POST", "/demo-action", body, {
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
        })
        response = connection.getresponse()
        result = response.status, response.read()
        connection.close()
        return result

    def test_private_provider_accepts_only_the_minimal_synthetic_action(self):
        status, body = self.request(json.dumps({
            "execution_id": "WFE-DEMO", "workflow_id": "WF-DEMO",
        }).encode())

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(json.loads(body), {"status": "completed"})

    def test_private_provider_rejects_invalid_payload_without_echoing_it(self):
        status, body = self.request(b'{"private_payload":"do not retain"}')

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertNotIn(b"private_payload", body)


if __name__ == "__main__":
    unittest.main()
