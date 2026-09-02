import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient
from database import (
    insert_employee,
    update_user_account_active_status,
)
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
        cls.viewer_username = "WebViewer"
        cls.viewer_password = "SecureViewerPassword123!"

        register_user_account(
            cls.viewer_username,
            cls.viewer_password,
            "viewer",
            cls.database_file,
        )

        insert_employee(
            {
                "employee_id": "EMP-WEB-001",
                "name": "Test Employee",
                "department": "Operations",
                "position": "Automation Specialist",
                "country": "Test Country",
                "salary": 85000,
                "email": "test.employee@example.com",
                "phone_number": "+81-90-1234-5678",
                "years_of_experience": 5,
                "company": "ABAP",
                "employment_status": "Active",
                "performance_score": 9,
            },
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

    def get_csrf_token(self) -> str:
        response = self.client.get("/employees/new")

        self.assertEqual(response.status_code, 200)

        token_match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            response.text,
        )

        self.assertIsNotNone(token_match)

        return token_match.group(1)

    def get_edit_csrf_token(
        self,
        employee_id: str,
    ) -> str:
        response = self.client.get(
            f"/employees/{employee_id}/edit"
        )

        self.assertEqual(response.status_code, 200)

        token_match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            response.text,
        )

        self.assertIsNotNone(token_match)

        return token_match.group(1)

    def get_delete_csrf_token(
        self,
        employee_id: str,
    ) -> str:
        response = self.client.get(
            f"/employees/{employee_id}/delete"
        )

        self.assertEqual(response.status_code, 200)

        token_match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            response.text,
        )

        self.assertIsNotNone(token_match)

        return token_match.group(1)

    def employee_form_data(
        self,
        csrf_token: str,
        **overrides: str,
    ) -> dict[str, str]:
        form_data = {
            "csrf_token": csrf_token,
            "employee_id": "EMP-WEB-NEW",
            "name": "New Web Employee",
            "department": "Engineering",
            "position": "Automation Engineer",
            "country": "Philippines",
            "salary": "72000",
            "email": "new.employee@example.com",
            "phone_number": "+63-917-000-0000",
            "years_of_experience": "4",
            "company": "ABAP",
            "employment_status": "Active",
            "performance_score": "85",
        }
        form_data.update(overrides)

        return form_data

    def employee_directory_sort_records(self):
        return [
            {
                "employee_id": "EMP-SORT-003",
                "name": "Zoe Automation",
                "department": "Engineering",
                "position": "Automation Engineer",
                "employment_status": "Active",
                "salary": 65000,
            },
            {
                "employee_id": "EMP-SORT-001",
                "name": "Alice Business",
                "department": "Operations",
                "position": "Operations Analyst",
                "employment_status": "Active",
                "salary": 95000,
            },
            {
                "employee_id": "EMP-SORT-002",
                "name": "Marco Systems",
                "department": "Engineering",
                "position": "Systems Specialist",
                "employment_status": "Inactive",
                "salary": 78000,
            },
        ]

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

    def test_authenticated_layout_includes_post_logout_form(self):
        self.sign_in()

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn('action="http://testserver/logout"', response.text)
        self.assertIn('method="post"', response.text)
        self.assertIn("Sign out", response.text)

    def test_logout_requires_post_request(self):
        self.sign_in()

        response = self.client.get(
            "/logout",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.client.get("/").status_code, 200)

    @patch("web_app.log_activity")
    def test_logout_clears_session_and_records_username(
        self,
        mock_log_activity,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        response = self.client.post(
            "/logout",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )
        cookie_header = response.headers["set-cookie"].lower()
        self.assertIn("abap_session=null", cookie_header)
        self.assertIn(
            "expires=thu, 01 jan 1970 00:00:00 gmt",
            cookie_header,
        )
        self.assertEqual(
            self.client.get(
                "/",
                follow_redirects=False,
            ).status_code,
            303,
        )
        mock_log_activity.assert_called_once_with(
            f"User {self.username} "
            "logged out of the web application."
        )

    @patch("web_app.log_activity")
    def test_logout_without_valid_session_is_safe_and_not_logged(
        self,
        mock_log_activity,
    ):
        response = self.client.post(
            "/logout",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )
        mock_log_activity.assert_not_called()

    def test_employee_directory_redirects_unauthenticated_user(self):
        response = self.client.get(
            "/employees",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    def test_workforce_report_redirects_unauthenticated_user(self):
        response = self.client.get(
            "/reports/workforce",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    def test_employee_report_download_redirects_unauthenticated_user(
        self,
    ):
        response = self.client.get(
            "/reports/employees.csv",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    @patch("web_app.log_activity")
    def test_administrator_can_download_employee_report(
        self,
        mock_log_activity,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        response = self.client.get("/reports/employees.csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["content-type"],
            "text/csv; charset=utf-8",
        )
        self.assertEqual(
            response.headers["content-disposition"],
            'attachment; filename="employee_report.csv"',
        )
        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))
        self.assertIn(
            "employee_id,name,department,position,salary",
            response.text,
        )
        self.assertIn(
            "EMP-WEB-001,Test Employee,Operations,"
            "Automation Specialist,85000",
            response.text,
        )
        mock_log_activity.assert_called_once_with(
            f"User {self.username} downloaded "
            "the web employee report."
        )

    def test_viewer_can_download_employee_report(self):
        self.sign_in(
            username=self.viewer_username,
            password=self.viewer_password,
        )

        response = self.client.get("/reports/employees.csv")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))
        self.assertIn(
            "employee_id,name,department,position,salary",
            response.text,
        )

    @patch(
        "web_app.user_has_permission",
        return_value=False,
    )
    @patch("web_app.log_activity")
    def test_employee_report_download_denies_missing_permission(
        self,
        mock_log_activity,
        mock_user_has_permission,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        response = self.client.get("/reports/employees.csv")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.text, "Access denied.")
        mock_user_has_permission.assert_called_once()
        mock_log_activity.assert_called_once_with(
            "Web employee-report export access denied "
            f"for user {self.username}."
        )

    @patch(
        "web_app.load_employee_records",
        return_value=None,
    )
    def test_employee_report_download_handles_loading_failure(
        self,
        mock_load_employee_records,
    ):
        self.sign_in()

        response = self.client.get("/reports/employees.csv")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.text,
            "Employee records could not be loaded.",
        )
        mock_load_employee_records.assert_called_once_with(
            database_file=self.database_file,
        )

    def test_workforce_report_shows_download_link(self):
        self.sign_in()

        response = self.client.get("/reports/workforce")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Download employee CSV", response.text)
        self.assertIn(
            'href="http://testserver/reports/employees.csv"',
            response.text,
        )

    def test_administrator_can_view_workforce_report(self):
        self.sign_in()

        response = self.client.get("/reports/workforce")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Workforce report", response.text)
        self.assertIn("Total employees", response.text)
        self.assertIn("Total departments", response.text)
        self.assertIn("Department headcounts", response.text)
        self.assertIn("Operations", response.text)
        self.assertIn("Reports", response.text)
        self.assertIn('aria-current="page"', response.text)
        self.assertNotIn("85,000.00", response.text)

    def test_viewer_can_view_workforce_report(self):
        self.sign_in(
            username=self.viewer_username,
            password=self.viewer_password,
        )

        response = self.client.get("/reports/workforce")

        self.assertEqual(response.status_code, 200)
        self.assertIn("WebViewer", response.text)
        self.assertIn("Workforce report", response.text)
        self.assertIn("Department headcounts", response.text)

    @patch(
        "web_app.user_has_permission",
        return_value=False,
    )
    @patch("web_app.log_activity")
    def test_workforce_report_denies_missing_permission(
        self,
        mock_log_activity,
        mock_user_has_permission,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        response = self.client.get("/reports/workforce")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.text, "Access denied.")
        mock_user_has_permission.assert_called_once()
        mock_log_activity.assert_called_once_with(
            "Web workforce-report access denied "
            f"for user {self.username}."
        )

    @patch(
        "web_app.load_employee_records",
        return_value=None,
    )
    def test_workforce_report_handles_loading_failure(
        self,
        mock_load_employee_records,
    ):
        self.sign_in()

        response = self.client.get("/reports/workforce")

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Employee records could not be loaded.",
            response.text,
        )
        mock_load_employee_records.assert_called_once_with(
            database_file=self.database_file,
        )

    @patch(
        "web_app.load_employee_records",
        return_value=[],
    )
    def test_workforce_report_displays_empty_state(
        self,
        mock_load_employee_records,
    ):
        self.sign_in()

        response = self.client.get("/reports/workforce")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Total employees", response.text)
        self.assertIn("No employee data is available", response.text)
        self.assertIn(
            "Add an employee to generate department headcounts.",
            response.text,
        )
        mock_load_employee_records.assert_called_once_with(
            database_file=self.database_file,
        )

    def test_activity_log_redirects_unauthenticated_user(self):
        response = self.client.get(
            "/activity-log",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    @patch(
        "web_app.load_recent_activity_entries",
        return_value=[
            "2026-09-02 10:00:00 | INFO | Test activity.",
            "2026-09-02 09:00:00 | INFO | <script>alert(1)</script>",
        ],
    )
    def test_administrator_can_view_activity_log(
        self,
        mock_load_recent_activity_entries,
    ):
        self.sign_in()

        response = self.client.get("/activity-log")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Activity log", response.text)
        self.assertIn("Recent activity", response.text)
        self.assertIn("Test activity.", response.text)
        self.assertIn(
            "&lt;script&gt;alert(1)&lt;/script&gt;",
            response.text,
        )
        self.assertNotIn("<script>alert(1)</script>", response.text)
        self.assertIn(
            'href="http://testserver/activity-log"',
            response.text,
        )
        self.assertIn('aria-current="page"', response.text)
        mock_load_recent_activity_entries.assert_called_once_with()

    @patch("web_app.load_recent_activity_entries")
    @patch("web_app.log_activity")
    def test_viewer_cannot_view_activity_log(
        self,
        mock_log_activity,
        mock_load_recent_activity_entries,
    ):
        self.sign_in(
            username=self.viewer_username,
            password=self.viewer_password,
        )

        directory_response = self.client.get("/employees")

        self.assertEqual(directory_response.status_code, 200)
        self.assertNotIn(
            'href="http://testserver/activity-log"',
            directory_response.text,
        )

        mock_log_activity.reset_mock()

        response = self.client.get("/activity-log")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.text, "Access denied.")
        mock_load_recent_activity_entries.assert_not_called()
        mock_log_activity.assert_called_once_with(
            "Web activity-log access denied "
            f"for user {self.viewer_username}."
        )

    @patch(
        "web_app.load_recent_activity_entries",
        return_value=None,
    )
    def test_activity_log_handles_loading_failure(
        self,
        mock_load_recent_activity_entries,
    ):
        self.sign_in()

        response = self.client.get("/activity-log")

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Activity log entries could not be loaded.",
            response.text,
        )
        mock_load_recent_activity_entries.assert_called_once_with()

    @patch(
        "web_app.load_recent_activity_entries",
        return_value=[],
    )
    def test_activity_log_displays_empty_state(
        self,
        mock_load_recent_activity_entries,
    ):
        self.sign_in()

        response = self.client.get("/activity-log")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "No activity has been recorded",
            response.text,
        )
        self.assertIn(
            "New application and security actions will appear here.",
            response.text,
        )
        mock_load_recent_activity_entries.assert_called_once_with()


    def test_administrator_can_view_employee_directory(self):
        self.sign_in()

        response = self.client.get("/employees")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Employee directory", response.text)
        self.assertIn("EMP-WEB-001", response.text)
        self.assertIn("Test Employee", response.text)
        self.assertIn("Operations", response.text)
        self.assertIn("Automation Specialist", response.text)
        self.assertIn("Active", response.text)
        self.assertIn("<table", response.text)

    def test_employee_directory_displays_filter_form(self):
        self.sign_in()

        response = self.client.get("/employees")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'method="get"',
            response.text,
        )
        self.assertIn(
            'action="http://testserver/employees"',
            response.text,
        )
        self.assertIn('name="search_text"', response.text)
        self.assertIn('name="department"', response.text)
        self.assertIn('name="minimum_salary"', response.text)
        self.assertIn('name="maximum_salary"', response.text)
        self.assertIn('name="sort_by"', response.text)
        self.assertIn("Name: A to Z", response.text)
        self.assertIn("Salary: highest first", response.text)
        self.assertIn("Apply filters", response.text)

    @patch("web_app.load_employee_records")
    def test_employee_directory_sorts_by_name(
        self,
        mock_load_employee_records,
    ):
        mock_load_employee_records.return_value = (
            self.employee_directory_sort_records()
        )
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "sort_by": "name",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Clear filters", response.text)
        self.assertLess(
            response.text.index("Alice Business"),
            response.text.index("Marco Systems"),
        )
        self.assertLess(
            response.text.index("Marco Systems"),
            response.text.index("Zoe Automation"),
        )

    @patch("web_app.load_employee_records")
    def test_employee_directory_sorts_by_salary(
        self,
        mock_load_employee_records,
    ):
        mock_load_employee_records.return_value = (
            self.employee_directory_sort_records()
        )
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "sort_by": "salary",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Clear filters", response.text)
        self.assertLess(
            response.text.index("Alice Business"),
            response.text.index("Marco Systems"),
        )
        self.assertLess(
            response.text.index("Marco Systems"),
            response.text.index("Zoe Automation"),
        )

    @patch("web_app.load_employee_records")
    def test_employee_directory_sorts_filtered_results(
        self,
        mock_load_employee_records,
    ):
        mock_load_employee_records.return_value = (
            self.employee_directory_sort_records()
        )
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "department": "Engineering",
                "sort_by": "salary",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Marco Systems", response.text)
        self.assertIn("Zoe Automation", response.text)
        self.assertNotIn("Alice Business", response.text)
        self.assertLess(
            response.text.index("Marco Systems"),
            response.text.index("Zoe Automation"),
        )

    @patch("web_app.load_employee_records")
    def test_employee_directory_ignores_unknown_sort_value(
        self,
        mock_load_employee_records,
    ):
        mock_load_employee_records.return_value = (
            self.employee_directory_sort_records()
        )
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "sort_by": "unknown",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Clear filters", response.text)
        self.assertLess(
            response.text.index("Zoe Automation"),
            response.text.index("Alice Business"),
        )
        self.assertLess(
            response.text.index("Alice Business"),
            response.text.index("Marco Systems"),
        )

    @patch("web_app.load_employee_records")
    def test_viewer_can_sort_employee_directory(
        self,
        mock_load_employee_records,
    ):
        mock_load_employee_records.return_value = (
            self.employee_directory_sort_records()
        )
        self.sign_in(
            username=self.viewer_username,
            password=self.viewer_password,
        )

        response = self.client.get(
            "/employees",
            params={
                "sort_by": "name",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("WebViewer", response.text)
        self.assertLess(
            response.text.index("Alice Business"),
            response.text.index("Marco Systems"),
        )
        self.assertLess(
            response.text.index("Marco Systems"),
            response.text.index("Zoe Automation"),
        )

    def test_employee_directory_searches_by_name(self):
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "search_text": "employee",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn(
            'value="employee"',
            response.text,
        )
        self.assertIn("Clear filters", response.text)

    def test_employee_directory_filters_by_department(self):
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "department": "operations",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn(
            'value="operations"',
            response.text,
        )
        self.assertIn("Clear filters", response.text)

    def test_employee_directory_filters_by_salary_range(self):
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "minimum_salary": "80000",
                "maximum_salary": "90000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn('value="80000"', response.text)
        self.assertIn('value="90000"', response.text)
        self.assertIn("Clear filters", response.text)

    def test_employee_directory_combines_filters(self):
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "search_text": "test",
                "department": "Operations",
                "minimum_salary": "80000",
                "maximum_salary": "90000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn("Clear filters", response.text)

    def test_employee_directory_shows_no_match_state(self):
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "search_text": "not-a-real-employee",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "No matching employees found",
            response.text,
        )
        self.assertIn(
            "Try changing or clearing the current filters.",
            response.text,
        )
        self.assertNotIn("Test Employee", response.text)

    def test_employee_directory_rejects_incomplete_salary_range(
        self,
    ):
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "minimum_salary": "80000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Enter both minimum and maximum salary values.",
            response.text,
        )
        self.assertIn("Test Employee", response.text)
        self.assertIn('value="80000"', response.text)

    def test_employee_directory_rejects_non_integer_salary(
        self,
    ):
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "minimum_salary": "eighty thousand",
                "maximum_salary": "90000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Salary values must be whole numbers.",
            response.text,
        )
        self.assertIn("Test Employee", response.text)

    def test_employee_directory_rejects_negative_salary(
        self,
    ):
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "minimum_salary": "-1",
                "maximum_salary": "90000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Salary values cannot be negative.",
            response.text,
        )
        self.assertIn("Test Employee", response.text)

    def test_employee_directory_rejects_reversed_salary_range(
        self,
    ):
        self.sign_in()

        response = self.client.get(
            "/employees",
            params={
                "minimum_salary": "90000",
                "maximum_salary": "80000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Minimum salary cannot exceed maximum salary.",
            response.text,
        )
        self.assertIn("Test Employee", response.text)

    def test_viewer_can_filter_employee_directory(self):
        self.sign_in(
            username=self.viewer_username,
            password=self.viewer_password,
        )

        response = self.client.get(
            "/employees",
            params={
                "search_text": "Test",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn("Clear filters", response.text)

    def test_viewer_can_view_employee_directory(self):
        self.sign_in(
            username=self.viewer_username,
            password=self.viewer_password,
        )

        response = self.client.get("/employees")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn("WebViewer", response.text)
        self.assertIn("Viewer", response.text)

    @patch(
        "web_app.user_has_permission",
        return_value=False,
    )
    @patch("web_app.log_activity")
    def test_employee_directory_denies_missing_permission(
        self,
        mock_log_activity,
        mock_user_has_permission,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        response = self.client.get("/employees")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.text, "Access denied.")
        mock_user_has_permission.assert_called_once()
        mock_log_activity.assert_called_once_with(
            "Web employee-directory access denied "
            f"for user {self.username}."
        )

    @patch(
        "web_app.load_employee_records",
        return_value=None,
    )
    def test_employee_directory_handles_loading_failure(
        self,
        mock_load_employee_records,
    ):
        self.sign_in()

        response = self.client.get("/employees")

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Employee records could not be loaded.",
            response.text,
        )
        mock_load_employee_records.assert_called_once_with(
            database_file=self.database_file,
        )

    @patch(
        "web_app.load_employee_records",
        return_value=[],
    )
    def test_employee_directory_displays_empty_state(
        self,
        mock_load_employee_records,
    ):
        self.sign_in()

        response = self.client.get("/employees")

        self.assertEqual(response.status_code, 200)
        self.assertIn("No employees found", response.text)
        self.assertIn("0", response.text)
        mock_load_employee_records.assert_called_once_with(
            database_file=self.database_file,
        )

    def test_employee_directory_navigation_is_active(self):
        self.sign_in()

        response = self.client.get("/employees")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'href="http://testserver/employees"',
            response.text,
        )
        self.assertIn("Employees", response.text)
        self.assertIn('aria-current="page"', response.text)

    def test_employee_directory_links_to_employee_profile(self):
        self.sign_in()

        response = self.client.get("/employees")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'href="http://testserver/employees/EMP-WEB-001"',
            response.text,
        )
        self.assertIn(
            'class="employee-profile-link"',
            response.text,
        )

    def test_employee_profile_redirects_unauthenticated_user(self):
        response = self.client.get(
            "/employees/EMP-WEB-001",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    def test_administrator_can_view_employee_profile(self):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn("EMP-WEB-001", response.text)
        self.assertIn("Operations", response.text)
        self.assertIn("Automation Specialist", response.text)
        self.assertIn("test.employee@example.com", response.text)
        self.assertIn("Employment details", response.text)
        self.assertIn("Contact details", response.text)
        self.assertIn(
            "Back to employee directory",
            response.text,
        )
        self.assertNotIn("Salary", response.text)
        self.assertNotIn("Performance score", response.text)

    def test_viewer_can_view_employee_profile(self):
        self.sign_in(
            username=self.viewer_username,
            password=self.viewer_password,
        )

        response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn("WebViewer", response.text)
        self.assertIn("Viewer", response.text)

    def test_employee_profile_id_is_case_insensitive(self):
        self.sign_in()

        response = self.client.get(
            "/employees/emp-web-001",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn("EMP-WEB-001", response.text)

    def test_employee_profile_returns_not_found(self):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-MISSING",
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("Employee not found", response.text)
        self.assertIn(
            "The requested employee record was not found.",
            response.text,
        )
        self.assertNotIn("Test Employee", response.text)

    @patch(
        "web_app.load_employee_records",
        return_value=None,
    )
    def test_employee_profile_handles_loading_failure(
        self,
        mock_load_employee_records,
    ):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Employee records could not be loaded.",
            response.text,
        )
        mock_load_employee_records.assert_called_once_with(
            database_file=self.database_file,
        )

    @patch(
        "web_app.user_has_permission",
        return_value=False,
    )
    @patch("web_app.log_activity")
    def test_employee_profile_denies_missing_permission(
        self,
        mock_log_activity,
        mock_user_has_permission,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.text, "Access denied.")
        mock_user_has_permission.assert_called_once()
        mock_log_activity.assert_called_once_with(
            "Web employee-profile access denied "
            f"for user {self.username}."
        )

    def test_employee_profile_links_to_payroll(self):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'href="http://testserver/'
            'employees/EMP-WEB-001/payroll"',
            response.text,
        )
        self.assertIn("View payroll", response.text)

    def test_employee_payroll_redirects_unauthenticated_user(self):
        response = self.client.get(
            "/employees/EMP-WEB-001/payroll",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    def test_administrator_can_view_employee_payroll(self):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001/payroll",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn("EMP-WEB-001", response.text)
        self.assertIn("Monthly payroll", response.text)
        self.assertIn("Annual compensation", response.text)
        self.assertIn("Performance basis", response.text)
        self.assertIn("₱85,000.00", response.text)
        self.assertIn("₱88,750.00", response.text)
        self.assertIn("₱1,105,000.00", response.text)
        self.assertIn("Needs Improvement", response.text)
        self.assertIn(
            "Payroll access authorized",
            response.text,
        )
        self.assertIn(
            "Back to employee profile",
            response.text,
        )

    def test_viewer_can_view_employee_payroll(self):
        self.sign_in(
            username=self.viewer_username,
            password=self.viewer_password,
        )

        response = self.client.get(
            "/employees/EMP-WEB-001/payroll",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Employee", response.text)
        self.assertIn("₱85,000.00", response.text)
        self.assertIn("WebViewer", response.text)
        self.assertIn("Viewer", response.text)

    @patch(
        "web_app.user_has_permission",
        side_effect=[True, False, False, False],
    )
    def test_employee_profile_hides_payroll_link_without_permission(
        self,
        mock_user_has_permission,
    ):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Edit employee", response.text)
        self.assertNotIn("Delete employee", response.text)
        self.assertNotIn("View payroll", response.text)
        self.assertNotIn(
            "/employees/EMP-WEB-001/payroll",
            response.text,
        )
        self.assertEqual(
            mock_user_has_permission.call_count,
            4,
        )

    @patch(
        "web_app.user_has_permission",
        return_value=False,
    )
    @patch("web_app.log_activity")
    def test_employee_payroll_denies_missing_permission(
        self,
        mock_log_activity,
        mock_user_has_permission,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        response = self.client.get(
            "/employees/EMP-WEB-001/payroll",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.text, "Access denied.")
        self.assertNotIn("₱", response.text)
        mock_user_has_permission.assert_called_once()
        mock_log_activity.assert_called_once_with(
            "Web payroll access denied "
            f"for user {self.username}."
        )

    def test_employee_payroll_returns_not_found(self):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-MISSING/payroll",
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("Employee not found", response.text)
        self.assertIn(
            "The requested employee record was not found.",
            response.text,
        )
        self.assertNotIn("₱", response.text)
        self.assertIn(
            "Back to employee directory",
            response.text,
        )

    @patch(
        "web_app.load_employee_records",
        return_value=None,
    )
    def test_employee_payroll_handles_loading_failure(
        self,
        mock_load_employee_records,
    ):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001/payroll",
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Employee records could not be loaded.",
            response.text,
        )
        self.assertNotIn("₱", response.text)
        mock_load_employee_records.assert_called_once_with(
            database_file=self.database_file,
        )

    def test_employee_create_form_redirects_unauthenticated_user(
        self,
    ):
        response = self.client.get(
            "/employees/new",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    def test_administrator_can_view_employee_create_form(self):
        self.sign_in()

        response = self.client.get("/employees/new")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Add employee", response.text)
        self.assertIn(
            "Registration access authorized",
            response.text,
        )
        self.assertIn('name="csrf_token"', response.text)
        self.assertIn('name="employee_id"', response.text)
        self.assertIn('name="performance_score"', response.text)

    def test_directory_shows_add_employee_only_to_administrator(
        self,
    ):
        self.sign_in()

        administrator_response = self.client.get("/employees")

        self.assertEqual(
            administrator_response.status_code,
            200,
        )
        self.assertIn(
            'href="http://testserver/employees/new"',
            administrator_response.text,
        )
        self.assertIn("Add employee", administrator_response.text)

        self.client.post("/logout", follow_redirects=False)
        self.sign_in(
            username=self.viewer_username,
            password=self.viewer_password,
        )

        viewer_response = self.client.get("/employees")

        self.assertEqual(viewer_response.status_code, 200)
        self.assertNotIn(
            'href="http://testserver/employees/new"',
            viewer_response.text,
        )
        self.assertNotIn("Add employee", viewer_response.text)

    @patch(
        "web_app.user_has_permission",
        return_value=False,
    )
    @patch("web_app.log_activity")
    def test_employee_create_form_denies_missing_permission(
        self,
        mock_log_activity,
        mock_user_has_permission,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        response = self.client.get("/employees/new")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.text,
            "Employee registration access is denied.",
        )
        mock_user_has_permission.assert_called_once()
        mock_log_activity.assert_called_once_with(
            "User "
            f"{self.username} was denied "
            "web employee-registration access."
        )

    def test_administrator_can_create_employee(self):
        self.sign_in()
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/employees/new",
            data=self.employee_form_data(csrf_token),
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/employees/EMP-WEB-NEW",
        )

        profile_response = self.client.get(
            "/employees/EMP-WEB-NEW",
        )

        self.assertEqual(profile_response.status_code, 200)
        self.assertIn("New Web Employee", profile_response.text)
        self.assertIn("Automation Engineer", profile_response.text)

    def test_employee_create_rejects_invalid_form_values(self):
        self.sign_in()
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/employees/new",
            data=self.employee_form_data(
                csrf_token,
                years_of_experience="61",
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Years of experience must be between 0 and 60.",
            response.text,
        )
        self.assertIn("New Web Employee", response.text)

    def test_employee_create_rejects_invalid_csrf_token(self):
        self.sign_in()

        response = self.client.post(
            "/employees/new",
            data=self.employee_form_data(
                "invalid-csrf-token",
                employee_id="EMP-WEB-CSRF",
            ),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.text,
            "Your form could not be verified.",
        )

        profile_response = self.client.get(
            "/employees/EMP-WEB-CSRF",
        )

        self.assertEqual(profile_response.status_code, 404)

    def test_employee_create_rejects_duplicate_employee_id(self):
        self.sign_in()
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/employees/new",
            data=self.employee_form_data(
                csrf_token,
                employee_id="emp-web-001",
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "An employee with that ID already exists.",
            response.text,
        )

    @patch(
        "web_app.load_employee_records",
        return_value=None,
    )
    def test_employee_create_handles_loading_failure(
        self,
        mock_load_employee_records,
    ):
        self.sign_in()
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/employees/new",
            data=self.employee_form_data(csrf_token),
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Employee records could not be loaded.",
            response.text,
        )
        mock_load_employee_records.assert_called_once_with(
            database_file=self.database_file,
        )

    @patch(
        "web_app.save_employee_records",
        return_value=False,
    )
    def test_employee_create_handles_saving_failure(
        self,
        mock_save_employee_records,
    ):
        self.sign_in()
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/employees/new",
            data=self.employee_form_data(
                csrf_token,
                employee_id="EMP-WEB-SAVE-FAIL",
            ),
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Employee could not be saved.",
            response.text,
        )
        mock_save_employee_records.assert_called_once()

    def test_employee_delete_form_redirects_unauthenticated_user(
        self,
    ):
        response = self.client.get(
            "/employees/EMP-WEB-001/delete",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    def test_employee_delete_form_shows_confirmation(self):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001/delete",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Delete employee", response.text)
        self.assertIn("Delete access authorized", response.text)
        self.assertIn("Test Employee", response.text)
        self.assertIn("EMP-WEB-001", response.text)
        self.assertIn(
            "This permanently deletes the employee record",
            response.text,
        )
        self.assertIn('name="csrf_token"', response.text)
        self.assertIn(
            'action="/employees/EMP-WEB-001/delete"',
            response.text,
        )
        self.assertIn("Cancel", response.text)
        self.assertIn(
            "Permanently delete employee",
            response.text,
        )

    def test_employee_profile_links_to_delete_confirmation(
        self,
    ):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Delete employee", response.text)
        self.assertIn(
            'href="http://testserver/'
            'employees/EMP-WEB-001/delete"',
            response.text,
        )

    def test_viewer_profile_hides_delete_action(self):
        self.sign_in(
            self.viewer_username,
            self.viewer_password,
        )

        response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Delete employee", response.text)
        self.assertNotIn(
            "/employees/EMP-WEB-001/delete",
            response.text,
        )

    @patch(
        "web_app.user_has_permission",
        return_value=False,
    )
    @patch("web_app.log_activity")
    def test_employee_delete_routes_deny_missing_permission(
        self,
        mock_log_activity,
        mock_user_has_permission,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        get_response = self.client.get(
            "/employees/EMP-WEB-001/delete",
        )

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(get_response.text, "Access denied.")
        mock_user_has_permission.assert_called_once()
        mock_log_activity.assert_called_once_with(
            "Web employee-deletion access denied "
            f"for user {self.username}."
        )

        mock_user_has_permission.reset_mock()
        mock_log_activity.reset_mock()

        post_response = self.client.post(
            "/employees/EMP-WEB-001/delete",
            data={
                "csrf_token": "not-needed-after-denial",
            },
        )

        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(post_response.text, "Access denied.")
        mock_user_has_permission.assert_called_once()
        mock_log_activity.assert_called_once_with(
            "Web employee-deletion access denied "
            f"for user {self.username}."
        )

    @patch("web_app.log_activity")
    def test_employee_delete_rejects_invalid_csrf_token(
        self,
        mock_log_activity,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        response = self.client.post(
            "/employees/EMP-WEB-001/delete",
            data={
                "csrf_token": "invalid-csrf-token",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.text,
            "Your form could not be verified.",
        )
        mock_log_activity.assert_called_once_with(
            f"User {self.username} submitted an "
            "invalid employee-deletion CSRF token."
        )

        profile_response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(profile_response.status_code, 200)
        self.assertIn("Test Employee", profile_response.text)

    @patch("web_app.log_activity")
    def test_employee_delete_removes_sqlite_record(
        self,
        mock_log_activity,
    ):
        employee_id = "EMP-WEB-DELETE"

        employee_inserted = insert_employee(
            {
                "employee_id": employee_id,
                "name": "Delete Test Employee",
                "department": "Quality Assurance",
                "position": "Test Specialist",
                "country": "Philippines",
                "salary": 64000,
                "email": "delete.test@example.com",
                "phone_number": "+63-917-999-0000",
                "years_of_experience": 3,
                "company": "ABAP",
                "employment_status": "Active",
                "performance_score": 88,
            },
            self.database_file,
        )
        self.assertTrue(employee_inserted)

        self.sign_in()
        csrf_token = self.get_delete_csrf_token(employee_id)
        mock_log_activity.reset_mock()

        response = self.client.post(
            f"/employees/{employee_id}/delete",
            data={
                "csrf_token": csrf_token,
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/employees",
        )
        mock_log_activity.assert_called_once_with(
            f"User {self.username} deleted "
            f"employee {employee_id} through "
            "the web application."
        )

        profile_response = self.client.get(
            f"/employees/{employee_id}",
        )

        self.assertEqual(profile_response.status_code, 404)
        self.assertIn(
            "The requested employee record was not found.",
            profile_response.text,
        )

    def test_employee_delete_routes_return_not_found(self):
        self.sign_in()

        get_response = self.client.get(
            "/employees/EMP-MISSING/delete",
        )

        self.assertEqual(get_response.status_code, 404)
        self.assertIn("Employee not found", get_response.text)
        self.assertIn(
            "The requested employee record was not found.",
            get_response.text,
        )
        self.assertNotIn(
            "Permanently delete employee",
            get_response.text,
        )

        csrf_token = self.get_delete_csrf_token(
            "EMP-WEB-001"
        )

        post_response = self.client.post(
            "/employees/EMP-MISSING/delete",
            data={
                "csrf_token": csrf_token,
            },
        )

        self.assertEqual(post_response.status_code, 404)
        self.assertIn(
            "The requested employee record was not found.",
            post_response.text,
        )
        self.assertNotIn(
            "Permanently delete employee",
            post_response.text,
        )

    @patch(
        "web_app.load_employee_records",
        return_value=None,
    )
    def test_employee_delete_form_handles_loading_failure(
        self,
        mock_load_employee_records,
    ):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001/delete",
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Employee records could not be loaded.",
            response.text,
        )
        self.assertNotIn(
            "Permanently delete employee",
            response.text,
        )
        mock_load_employee_records.assert_called_once_with(
            database_file=self.database_file,
        )

    @patch(
        "web_app.save_employee_records",
        return_value=False,
    )
    @patch("web_app.log_activity")
    def test_employee_delete_handles_saving_failure(
        self,
        mock_log_activity,
        mock_save_employee_records,
    ):
        self.sign_in()
        csrf_token = self.get_delete_csrf_token(
            "EMP-WEB-001"
        )
        mock_log_activity.reset_mock()

        response = self.client.post(
            "/employees/EMP-WEB-001/delete",
            data={
                "csrf_token": csrf_token,
            },
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Employee deletion could not be saved.",
            response.text,
        )
        mock_save_employee_records.assert_called_once()
        mock_log_activity.assert_not_called()

        profile_response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(profile_response.status_code, 200)
        self.assertIn("Test Employee", profile_response.text)

    def test_employee_edit_form_redirects_unauthenticated_user(
        self,
    ):
        response = self.client.get(
            "/employees/EMP-WEB-001/edit",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    def test_employee_edit_form_prefills_existing_values(self):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001/edit",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Edit employee", response.text)
        self.assertIn("Update access authorized", response.text)
        self.assertIn('value="Operations"', response.text)
        self.assertIn(
            'value="Automation Specialist"',
            response.text,
        )
        self.assertIn('name="csrf_token"', response.text)
        self.assertIn(
            'value="test.employee@example.com"',
            response.text,
        )
        self.assertIn(
            'value="+81-90-1234-5678"',
            response.text,
        )

    def test_employee_profile_links_to_edit_form(self):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Edit employee", response.text)
        self.assertIn(
            'href="http://testserver/'
            'employees/EMP-WEB-001/edit"',
            response.text,
        )

    @patch(
        "web_app.user_has_permission",
        return_value=False,
    )
    @patch("web_app.log_activity")
    def test_employee_edit_routes_deny_missing_permission(
        self,
        mock_log_activity,
        mock_user_has_permission,
    ):
        self.sign_in()
        mock_log_activity.reset_mock()

        get_response = self.client.get(
            "/employees/EMP-WEB-001/edit",
        )

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(get_response.text, "Access denied.")
        mock_user_has_permission.assert_called_once()
        mock_log_activity.assert_called_once_with(
            "Web employee-update access denied "
            f"for user {self.username}."
        )

        mock_user_has_permission.reset_mock()
        mock_log_activity.reset_mock()

        post_response = self.client.post(
            "/employees/EMP-WEB-001/edit",
            data={
                "csrf_token": "not-needed-after-denial",
                "department": "Security",
                "position": "Security Analyst",
                "email": "security@example.com",
                "phone_number": "+63-917-000-0000",
            },
        )

        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(post_response.text, "Access denied.")
        mock_user_has_permission.assert_called_once()
        mock_log_activity.assert_called_once_with(
            "Web employee-update access denied "
            f"for user {self.username}."
        )

    def test_employee_update_changes_department_and_position(
        self,
    ):
        self.sign_in()
        csrf_token = self.get_edit_csrf_token(
            "EMP-WEB-001"
        )

        response = self.client.post(
            "/employees/EMP-WEB-001/edit",
            data={
                "csrf_token": csrf_token,
                "department": "Product Engineering",
                "position": "Senior Automation Engineer",
                "email": "updated.employee@example.com",
                "phone_number": "+63-917-111-2222",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/employees/EMP-WEB-001",
        )

        profile_response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertEqual(profile_response.status_code, 200)
        self.assertIn(
            "Product Engineering",
            profile_response.text,
        )
        self.assertIn(
            "Senior Automation Engineer",
            profile_response.text,
        )
        self.assertIn(
            "updated.employee@example.com",
            profile_response.text,
        )
        self.assertIn(
            "+63-917-111-2222",
            profile_response.text,
        )

    def test_employee_update_rejects_blank_values(self):
        self.sign_in()
        csrf_token = self.get_edit_csrf_token(
            "EMP-WEB-001"
        )

        response = self.client.post(
            "/employees/EMP-WEB-001/edit",
            data={
                "csrf_token": csrf_token,
                "department": "   ",
                "position": "Automation Lead",
                "email": "lead@example.com",
                "phone_number": "+63-917-333-4444",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Department, position, email, and phone "
            "number are required.",
            response.text,
        )
        self.assertIn(
            'value="Automation Lead"',
            response.text,
        )

    def test_employee_update_rejects_invalid_csrf_token(self):
        self.sign_in()

        response = self.client.post(
            "/employees/EMP-WEB-001/edit",
            data={
                "csrf_token": "invalid-csrf-token",
                "department": "Untrusted Department",
                "position": "Untrusted Position",
                "email": "untrusted@example.com",
                "phone_number": "+63-917-555-6666",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.text,
            "Your form could not be verified.",
        )

        profile_response = self.client.get(
            "/employees/EMP-WEB-001",
        )

        self.assertNotIn(
            "Untrusted Department",
            profile_response.text,
        )
        self.assertNotIn(
            "Untrusted Position",
            profile_response.text,
        )

    def test_employee_edit_form_returns_not_found(self):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-MISSING/edit",
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("Employee not found", response.text)
        self.assertIn(
            "The requested employee record was not found.",
            response.text,
        )
        self.assertNotIn("Save changes", response.text)

    @patch(
        "web_app.load_employee_records",
        return_value=None,
    )
    def test_employee_edit_form_handles_loading_failure(
        self,
        mock_load_employee_records,
    ):
        self.sign_in()

        response = self.client.get(
            "/employees/EMP-WEB-001/edit",
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Employee records could not be loaded.",
            response.text,
        )
        self.assertNotIn("Save changes", response.text)
        mock_load_employee_records.assert_called_once_with(
            database_file=self.database_file,
        )

    @patch(
        "web_app.save_employee_records",
        return_value=False,
    )
    def test_employee_update_handles_saving_failure(
        self,
        mock_save_employee_records,
    ):
        self.sign_in()
        csrf_token = self.get_edit_csrf_token(
            "EMP-WEB-001"
        )

        response = self.client.post(
            "/employees/EMP-WEB-001/edit",
            data={
                "csrf_token": csrf_token,
                "department": "Temporary Department",
                "position": "Temporary Position",
                "email": "temporary@example.com",
                "phone_number": "+63-917-777-8888",
            },
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Employee changes could not be saved.",
            response.text,
        )
        mock_save_employee_records.assert_called_once()

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
