import unittest

from fastapi.testclient import TestClient

from web_app import create_web_application


class TestWebApplication(unittest.TestCase):
    def setUp(self):
        application = create_web_application()
        self.client = TestClient(application)

    def test_home_page_returns_employee_management_html(self):
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