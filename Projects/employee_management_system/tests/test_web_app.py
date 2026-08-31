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

    def test_home_page_links_to_static_stylesheet(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "/static/styles.css",
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