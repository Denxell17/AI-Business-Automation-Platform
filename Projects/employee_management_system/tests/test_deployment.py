import os
import unittest
from unittest.mock import patch

from fastapi import Request
from fastapi.testclient import TestClient

from deployment import create_application, migrate


class TestDeployment(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "DATABASE_BACKEND": "postgresql",
                "DATABASE_URL": (
                    "postgresql://user:password@database/abap"
                ),
                "ABAP_SESSION_SECRET": (
                    "a-random-test-secret-with-at-least-32-characters"
                ),
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_rejects_sqlite(self):
        os.environ["DATABASE_BACKEND"] = "sqlite"
        with self.assertRaises(ValueError):
            create_application()

    def test_rejects_missing_short_and_placeholder_secret(self):
        invalid_secrets = (
            "",
            "short",
            "replace_with_a_random_secret_of_at_least_32_characters",
        )
        for secret in invalid_secrets:
            with self.subTest(secret=secret):
                os.environ["ABAP_SESSION_SECRET"] = secret
                with self.assertRaises(ValueError):
                    create_application()

    def test_secure_session_survives_new_application(self):
        application = create_application()

        @application.get("/test-session")
        def write_session(request: Request):
            request.session["test_value"] = "retained"
            return {"ok": True}

        replacement = create_application()

        @replacement.get("/test-session")
        def read_session(request: Request):
            return {"value": request.session.get("test_value")}

        with TestClient(application, base_url="https://testserver") as first:
            response = first.get("/test-session")
            cookie = response.headers["set-cookie"]
            self.assertIn("secure", cookie.lower())
            self.assertIn("httponly", cookie.lower())
            self.assertIn("samesite=lax", cookie.lower())
            with TestClient(replacement, base_url="https://testserver") as second:
                second.cookies.update(first.cookies)
                repeated = second.get("/test-session")
                self.assertEqual(repeated.json(), {"value": "retained"})
                self.assertEqual(repeated.status_code, 200)
                self.assertEqual(second.get("/health").status_code, 200)

    def test_explicit_migration_uses_configured_database(self):
        with patch("deployment.apply_postgresql_migrations") as apply:
            migrate()
        apply.assert_called_once_with(os.environ["DATABASE_URL"])
