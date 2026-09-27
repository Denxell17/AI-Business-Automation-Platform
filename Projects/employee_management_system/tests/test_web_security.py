import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from tests.web_auth import sign_in, sign_out
from user_service import register_user_account
from web_app import create_web_application
from web_security import CONTENT_SECURITY_POLICY, PERMISSIONS_POLICY


class TestWebSecurityPolicy(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name) / "web-security.db"
        )
        self.username = "SecurityAdmin"
        self.password = "SecureSecurityPassword123!"
        self.assertTrue(
            register_user_account(
                self.username,
                self.password,
                "admin",
                self.database_file,
            )
        )
        self.client = TestClient(
            create_web_application(
                database_file=self.database_file,
                session_secret="web-security-test-session-secret",
            )
        )

    def tearDown(self):
        self.client.close()
        self.temporary_directory.cleanup()

    def test_normal_application_response_has_strict_browser_headers(self):
        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["content-security-policy"],
            CONTENT_SECURITY_POLICY,
        )
        self.assertNotIn(
            "'unsafe-inline'",
            response.headers["content-security-policy"],
        )
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(
            response.headers["x-content-type-options"],
            "nosniff",
        )
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertEqual(
            response.headers["permissions-policy"],
            PERMISSIONS_POLICY,
        )
        self.assertNotIn("strict-transport-security", response.headers)

    def test_development_documentation_keeps_narrow_csp_exception(self):
        for path in ("/docs", "/redoc", "/openapi.json"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("content-security-policy", response.headers)
                self.assertEqual(response.headers["x-frame-options"], "DENY")
                self.assertNotIn("cache-control", response.headers)

    def test_sensitive_responses_are_not_stored(self):
        login_page = self.client.get("/login")
        self.assertEqual(
            login_page.headers["cache-control"],
            "private, no-store",
        )

        login = sign_in(
            self.client,
            self.username,
            self.password,
        )
        self.assertEqual(login.status_code, 303)
        self.assertEqual(
            login.headers["cache-control"],
            "private, no-store",
        )

        authenticated_page = self.client.get("/")
        self.assertEqual(authenticated_page.status_code, 200)
        self.assertEqual(
            authenticated_page.headers["cache-control"],
            "private, no-store",
        )

        authenticated_error = self.client.get("/employees/NOT-FOUND")
        self.assertEqual(authenticated_error.status_code, 404)
        self.assertEqual(
            authenticated_error.headers["cache-control"],
            "private, no-store",
        )

        logout = sign_out(self.client)
        self.assertEqual(logout.status_code, 303)
        self.assertEqual(
            logout.headers["cache-control"],
            "private, no-store",
        )

    def test_public_and_static_responses_do_not_get_sensitive_cache_policy(self):
        sign_in(
            self.client,
            self.username,
            self.password,
        )
        responses = (
            self.client.get("/static/styles.css"),
            self.client.get("/health"),
            self.client.get("/ready"),
            self.client.post("/integrations/webhooks/callback", content=b"{}"),
        )

        for response in responses:
            with self.subTest(url=str(response.request.url)):
                self.assertNotIn("cache-control", response.headers)


if __name__ == "__main__":
    unittest.main()
