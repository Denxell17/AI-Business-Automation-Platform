import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from database import update_user_account_active_status
from user_service import register_user_account

from web_app import create_web_application


class TestWebApplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = TemporaryDirectory()
        cls.database_file = (
            Path(cls.temporary_directory.name)
            / "employees.db"
        )
        cls.username = "WebAdmin"
        cls.password = "SecureWebPassword123!"

        register_user_account(
            cls.username,
            cls.password,
            "admin",
            cls.database_file,
        )
        register_user_account(
            "InactiveViewer",
            "InactivePassword123!",
            "viewer",
            cls.database_file,
        )
        update_user_account_active_status(
            "InactiveViewer",
            False,
            cls.database_file,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temporary_directory.cleanup()

    def setUp(self):
        application = create_web_application(
            database_file=self.database_file,
            session_secret="day-84-test-session-secret",
        )
        self.client = TestClient(application)

    def tearDown(self):
        self.client.close()

    def sign_in(
        self,
        username: str | None = None,
        password: str | None = None,
    ):
        return self.client.post(
            "/login",
            data={
                "username": (
                    self.username
                    if username is None
                    else username
                ),
                "password": (
                    self.password
                    if password is None
                    else password
                ),
            },
            follow_redirects=False,
        )

    def test_home_page_returns_employee_management_html(self):
        self.sign_in()
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "text/html",
            response.headers["content-type"],
        )
        self.assertIn(
            "Employee Management System",
            response.text,
        )
        self.assertIn(
            "Securely manage workforce information",
            response.text,
        )

    def test_home_page_uses_reusable_navigation_layout(self):
        self.sign_in()
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'aria-label="Primary navigation"',
            response.text,
        )
        self.assertIn(
            'aria-current="page"',
            response.text,
        )
        self.assertIn(
            "API documentation",
            response.text,
        )
        self.assertIn(
            "System health",
            response.text,
        )

    def test_home_page_includes_accessibility_foundations(self):
        self.sign_in()
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'class="skip-link"',
            response.text,
        )
        self.assertIn(
            'href="#main-content"',
            response.text,
        )
        self.assertIn(
            'id="main-content"',
            response.text,
        )
        self.assertIn(
            'aria-expanded="false"',
            response.text,
        )

    def test_home_page_links_to_static_assets(self):
        self.sign_in()
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "/static/styles.css",
            response.text,
        )
        self.assertIn(
            "/static/navigation.js",
            response.text,
        )

    def test_login_page_returns_accessible_password_form(self):
        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Sign in to your workspace",
            response.text,
        )
        self.assertIn(
            'method="post"',
            response.text,
        )
        self.assertIn(
            'autocomplete="username"',
            response.text,
        )
        self.assertIn(
            'type="password"',
            response.text,
        )
        self.assertIn(
            'autocomplete="current-password"',
            response.text,
        )

    def test_home_page_redirects_unauthenticated_user(self):
        response = self.client.get(
            "/",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    def test_valid_login_creates_signed_session(self):
        response = self.sign_in()

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/",
        )

        cookie_header = response.headers["set-cookie"].lower()

        self.assertIn("abap_session=", cookie_header)
        self.assertIn("httponly", cookie_header)
        self.assertIn("samesite=lax", cookie_header)
        self.assertIn("max-age=28800", cookie_header)

    def test_invalid_login_returns_generic_error(self):
        response = self.sign_in(
            password="WrongPassword123!",
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn(
            "Username or password is incorrect.",
            response.text,
        )
        self.assertNotIn(
            "WrongPassword123!",
            response.text,
        )

    def test_inactive_account_cannot_sign_in(self):
        response = self.sign_in(
            username="InactiveViewer",
            password="InactivePassword123!",
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn(
            "Username or password is incorrect.",
            response.text,
        )

    def test_authenticated_home_displays_current_user(self):
        self.sign_in()

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.username, response.text)
        self.assertIn("Admin", response.text)

    def test_static_stylesheet_is_available(self):
        response = self.client.get("/static/styles.css")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "text/css",
            response.headers["content-type"],
        )
        self.assertIn(
            "--color-primary",
            response.text,
        )
        self.assertIn(
            "--color-background: #1b1d21",
            response.text,
        )

    def test_navigation_script_is_available(self):
        response = self.client.get("/static/navigation.js")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "javascript",
            response.headers["content-type"],
        )
        self.assertIn(
            "setNavigationOpen",
            response.text,
        )

    def test_health_check_returns_healthy_status(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "healthy",
            },
        )

    def test_api_documentation_is_available(self):
        response = self.client.get("/docs")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "text/html",
            response.headers["content-type"],
        )


if __name__ == "__main__":
    unittest.main()