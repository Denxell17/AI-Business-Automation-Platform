import re
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from crm_repository import list_crm_history, load_customer, load_lead
from crm_service import add_lead_note, convert_lead, create_lead, update_customer, update_lead
from dashboard_repository import load_dashboard_snapshot
from database import get_database_connection, load_user_account_by_username
from user_service import register_user_account
from web_app import create_web_application


class TestCrmDomain(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = Path(self.temporary_directory.name) / "crm.db"
        self.assertTrue(register_user_account("CrmAdmin", "SecureAdminPassword123!", "admin", self.database_file))
        self.assertTrue(register_user_account("CrmViewer", "SecureViewerPassword123!", "viewer", self.database_file))
        self.admin = load_user_account_by_username("CrmAdmin", self.database_file)
        self.viewer = load_user_account_by_username("CrmViewer", self.database_file)
        self.client = TestClient(create_web_application(
            database_file=self.database_file, session_secret="crm-test-session"))

    def tearDown(self):
        self.client.close()
        self.temporary_directory.cleanup()

    def sign_in(self, username="CrmAdmin", password="SecureAdminPassword123!"):
        return self.client.post("/login", data={"username": username, "password": password})

    def csrf(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, response.text)
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_lead_conversion_and_immutable_source(self):
        lead_id = create_lead(self.admin, "Example <Lead>", "lead@example.test",
                              owner_user_id=self.admin["user_id"], database_file=self.database_file)
        self.assertTrue(update_lead(self.admin, lead_id, "Example <Lead>",
                                    "lead@example.test", "", "Example Co", "contacted",
                                    self.admin["user_id"], self.database_file))
        self.assertTrue(update_lead(self.admin, lead_id, "Example <Lead>",
                                    "lead@example.test", "", "Example Co", "qualified",
                                    self.admin["user_id"], self.database_file))
        self.assertIsNotNone(add_lead_note(self.admin, lead_id, "Called once", self.database_file))
        customer_id = convert_lead(self.admin, lead_id, self.database_file)
        self.assertEqual(convert_lead(self.admin, lead_id, self.database_file), customer_id)
        self.assertEqual(load_lead(lead_id, self.database_file)["stage"], "converted")
        self.assertEqual(load_customer(customer_id, self.database_file)["source_lead_id"], lead_id)
        self.assertTrue(update_customer(self.admin, customer_id, "Example Customer",
                                        "customer@example.test", "", "Example Co", "inactive",
                                        self.database_file))
        self.assertEqual(load_customer(customer_id, self.database_file)["status"], "inactive")
        self.assertEqual([event["event_type"] for event in list_crm_history(
            "lead", lead_id, self.database_file)].count("converted"), 1)
        connection = get_database_connection(self.database_file)
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("UPDATE customers SET source_lead_id = ? WHERE customer_id = ?",
                               ("other", customer_id))
        connection.close()
        snapshot = load_dashboard_snapshot(self.database_file, include_employees=False,
                                           include_workflows=False, include_agents=False,
                                           include_crm=True)
        self.assertEqual((snapshot["lead_total"], snapshot["customer_total"]), (1, 1))

    def test_permissions_csrf_and_escaped_detail(self):
        self.assertEqual(self.client.get("/leads", follow_redirects=False).status_code, 303)
        self.sign_in("CrmViewer", "SecureViewerPassword123!")
        self.assertEqual(self.client.get("/leads").status_code, 200)
        self.assertEqual(self.client.get("/leads/new").status_code, 403)
        self.assertEqual(self.client.post("/leads/new", data={}).status_code, 403)
        self.client.post("/logout")
        self.sign_in()
        self.assertEqual(self.client.post("/leads/new", data={"name": "No token"}).status_code, 403)
        token = self.csrf("/leads/new")
        response = self.client.post("/leads/new", data={
            "csrf_token": token, "name": "<script>alert(1)</script>",
            "email": "safe@example.test", "owner_user_id": str(self.admin["user_id"]),
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 303, response.text)
        detail = self.client.get(response.headers["location"])
        self.assertEqual(detail.status_code, 200)
        self.assertNotIn("<script>alert(1)</script>", detail.text)
        self.assertIn("&lt;script&gt;", detail.text)

    def test_validation_and_search(self):
        with self.assertRaises(ValueError):
            create_lead(self.admin, "", database_file=self.database_file)
        with self.assertRaises(PermissionError):
            create_lead(self.viewer, "Denied", database_file=self.database_file)
        self.sign_in()
        token = self.csrf("/leads/new")
        self.client.post("/leads/new", data={"csrf_token": token, "name": "Acme % Client"})
        self.assertIn("Acme % Client", self.client.get("/leads?q=Acme").text)
        self.assertIn("No leads found", self.client.get("/leads?q=Acme_Unknown").text)
