"""Private deterministic action provider used only by the n8n Compose demo."""

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


MAX_REQUEST_BYTES = 4096


class DemoActionHandler(BaseHTTPRequestHandler):
    """Accept a narrow synthetic action without logging request contents."""
    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != "/demo-action":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            content_length = 0
        if (
            self.headers.get_content_type() != "application/json"
            or not 0 < content_length <= MAX_REQUEST_BYTES
        ):
            self.send_error(HTTPStatus.BAD_REQUEST)
            return
        try:
            body = json.loads(self.rfile.read(content_length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_error(HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(body, dict) or set(body) != {"execution_id", "workflow_id"}:
            self.send_error(HTTPStatus.BAD_REQUEST)
            return
        encoded = b'{"status":"completed"}'
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *_args: object) -> None:
        """Do not write request values, headers, or payloads to container logs."""


def main() -> None:
    ThreadingHTTPServer(("0.0.0.0", 8090), DemoActionHandler).serve_forever()


if __name__ == "__main__":
    main()
