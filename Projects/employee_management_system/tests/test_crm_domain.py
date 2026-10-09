import re
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from tests.web_auth import sign_in, sign_out

from crm_repository import list_crm_history, load_customer, load_lead
from crm_service import (
    add_lead_note,
    convert_lead,
    convert_lead_with_result,
    create_lead,
    update_customer,
    update_lead,
)
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
        return sign_in(self.client, username, password)

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
        conversion = convert_lead_with_result(self.admin, lead_id, self.database_file)
        customer_id = conversion.customer_id
        self.assertTrue(conversion.converted_now)
        duplicate = convert_lead_with_result(self.admin, lead_id, self.database_file)
        self.assertEqual(duplicate.customer_id, customer_id)
        self.assertFalse(duplicate.converted_now)
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
        viewer_customers = self.client.get("/customers")
        self.assertIn("Customers appear here after", viewer_customers.text)
        self.assertIn(">View leads<", viewer_customers.text)
        self.assertNotIn('href="http://testserver/leads/new"', viewer_customers.text)
        self.assertEqual(self.client.get("/leads/new").status_code, 403)
        self.assertEqual(self.client.post("/leads/new", data={}).status_code, 403)
        sign_out(self.client)
        self.sign_in()
        admin_customers = self.client.get("/customers")
        self.assertIn(">Create lead<", admin_customers.text)
        self.assertIn('href="http://testserver/leads/new"', admin_customers.text)
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
        self.assertIn("No matching leads found", self.client.get("/leads?q=Acme_Unknown").text)

    def test_browser_lifecycle_guidance_conversion_and_invoice_handoff(self):
        self.sign_in()
        token = self.csrf("/leads/new")
        created = self.client.post("/leads/new", data={
            "csrf_token": token,
            "name": "Guided Lead",
            "email": "guided@example.test",
            "company": "Guided Company",
            "owner_user_id": str(self.admin["user_id"]),
        }, follow_redirects=False)
        self.assertEqual(created.status_code, 303, created.text)
        lead_path = created.headers["location"]
        lead_id = lead_path.rsplit("/", 1)[-1]

        new_detail = self.client.get(lead_path)
        self.assertIn("Lead lifecycle stages", new_detail.text)
        self.assertIn("Mark this lead as Contacted", new_detail.text)
        self.assertNotIn(">Convert to customer<", new_detail.text)
        new_edit = self.client.get(f"/leads/{lead_id}/edit")
        self.assertIn("Only valid next stages are shown", new_edit.text)
        self.assertNotIn('value="qualified"', new_edit.text)

        contacted = self.client.post(f"/leads/{lead_id}/edit", data={
            "csrf_token": token,
            "name": "Guided Lead",
            "email": "guided@example.test",
            "company": "Guided Company",
            "owner_user_id": str(self.admin["user_id"]),
            "stage": "contacted",
        }, follow_redirects=False)
        self.assertEqual(contacted.status_code, 303, contacted.text)
        contacted_edit = self.client.get(f"/leads/{lead_id}/edit")
        self.assertIn('value="qualified"', contacted_edit.text)
        self.assertIn("Mark this lead as Qualified", contacted_edit.text)

        qualified = self.client.post(f"/leads/{lead_id}/edit", data={
            "csrf_token": token,
            "name": "Guided Lead",
            "email": "guided@example.test",
            "company": "Guided Company",
            "owner_user_id": str(self.admin["user_id"]),
            "stage": "qualified",
        }, follow_redirects=False)
        self.assertEqual(qualified.status_code, 303, qualified.text)
        qualified_detail = self.client.get(lead_path)
        self.assertIn("Ready to become a customer", qualified_detail.text)
        self.assertIn(">Convert to customer<", qualified_detail.text)
        self.assertEqual(
            self.client.post(f"/leads/{lead_id}/convert", data={}).status_code,
            403,
        )

        sign_out(self.client)
        self.sign_in("CrmViewer", "SecureViewerPassword123!")
        viewer_detail = self.client.get(lead_path)
        self.assertNotIn(">Convert to customer<", viewer_detail.text)
        self.assertEqual(
            self.client.post(f"/leads/{lead_id}/convert", data={
                "csrf_token": token,
            }).status_code,
            403,
        )

        sign_out(self.client)
        self.sign_in()
        token = self.csrf(lead_path)
        converted = self.client.post(f"/leads/{lead_id}/convert", data={
            "csrf_token": token,
        }, follow_redirects=False)
        self.assertEqual(converted.status_code, 303, converted.text)
        customer_path = converted.headers["location"]
        customer_id = customer_path.rsplit("/", 1)[-1]
        customer_detail = self.client.get(customer_path)
        self.assertIn(">Create invoice<", customer_detail.text)
        self.assertIn(f"/invoices/new?customer_id={customer_id}", customer_detail.text)

        repeated = self.client.post(f"/leads/{lead_id}/convert", data={
            "csrf_token": token,
        }, follow_redirects=False)
        self.assertEqual(repeated.status_code, 303)
        self.assertEqual(repeated.headers["location"], customer_path)
