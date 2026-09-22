"""Run only against an explicitly configured disposable PostgreSQL database."""

import os
import re
import unittest
from unittest.mock import patch
from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient

from crm_repository import list_crm_history, list_leads, load_customer, load_lead
from database import load_user_account_by_username
from postgresql_migrations import apply_postgresql_migrations
from user_service import register_user_account
from web_app import create_web_application


TEST_DATABASE_URL = os.environ.get("ABAP_TEST_DATABASE_URL", "").strip()


@unittest.skipUnless(TEST_DATABASE_URL, "ABAP_TEST_DATABASE_URL is required for live PostgreSQL tests.")
class TestCrmPostgresqlIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment = patch.dict(os.environ, {
            "DATABASE_BACKEND": "postgresql", "DATABASE_URL": TEST_DATABASE_URL,
        })
        cls.environment.start()
        apply_postgresql_migrations(TEST_DATABASE_URL)

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()

    def test_lead_to_customer_and_browser_history(self):
        username = "m4_" + uuid4().hex[:12]
        password = "SyntheticM4Password123!"
        lead_id = None
        customer_id = None
        try:
            self.assertTrue(register_user_account(username, password, "admin"))
            actor = load_user_account_by_username(username)
            with TestClient(create_web_application(session_secret="synthetic-m4-session")) as client:
                client.post("/login", data={"username": username, "password": password})
                new_form = client.get("/leads/new")
                token_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', new_form.text)
                self.assertIsNotNone(token_match)
                token = token_match.group(1)
                created = client.post("/leads/new", data={
                    "csrf_token": token, "name": "Synthetic Lead",
                    "email": "lead@example.test", "company": "Example",
                    "owner_user_id": str(actor["user_id"]),
                }, follow_redirects=False)
                self.assertEqual(created.status_code, 303)
                lead_id = created.headers["location"].rsplit("/", 1)[-1]
                self.assertEqual(len([row for row in list_leads("Synthetic Lead")
                                      if row["lead_id"] == lead_id]), 1)
                for stage in ("contacted", "qualified"):
                    edited = client.post(f"/leads/{lead_id}/edit", data={
                        "csrf_token": token, "name": "Synthetic Lead",
                        "email": "lead@example.test", "company": "Example",
                        "owner_user_id": str(actor["user_id"]), "stage": stage,
                    }, follow_redirects=False)
                    self.assertEqual(edited.status_code, 303)
                noted = client.post(f"/leads/{lead_id}/notes", data={
                    "csrf_token": token, "body": "Synthetic note",
                }, follow_redirects=False)
                self.assertEqual(noted.status_code, 303)
                converted = client.post(f"/leads/{lead_id}/convert", data={
                    "csrf_token": token,
                }, follow_redirects=False)
                self.assertEqual(converted.status_code, 303)
                customer_id = converted.headers["location"].rsplit("/", 1)[-1]
                duplicate = client.post(f"/leads/{lead_id}/convert", data={
                    "csrf_token": token,
                }, follow_redirects=False)
                self.assertEqual(duplicate.headers["location"], converted.headers["location"])
                detail = client.get(f"/customers/{customer_id}")
                self.assertEqual(detail.status_code, 200)
                self.assertIn("Synthetic Lead", detail.text)
                self.assertIn("Audit history", detail.text)
            self.assertEqual(load_lead(lead_id)["stage"], "converted")
            self.assertEqual(load_customer(customer_id)["source_lead_id"], lead_id)
            self.assertEqual([event["event_type"] for event in list_crm_history(
                "lead", lead_id)].count("converted"), 1)
            with psycopg.connect(TEST_DATABASE_URL) as connection:
                with self.assertRaises(psycopg.Error):
                    connection.execute("UPDATE customers SET source_lead_id = %s WHERE customer_id = %s",
                                       ("other", customer_id))
                connection.rollback()
        finally:
            with psycopg.connect(TEST_DATABASE_URL) as connection:
                if lead_id:
                    connection.execute("DELETE FROM crm_audit_events WHERE entity_id = %s OR entity_id = %s",
                                       (lead_id, customer_id or ""))
                    connection.execute("DELETE FROM lead_notes WHERE lead_id = %s", (lead_id,))
                    connection.execute("DELETE FROM customers WHERE source_lead_id = %s", (lead_id,))
                    connection.execute("DELETE FROM leads WHERE lead_id = %s", (lead_id,))
                connection.execute("DELETE FROM users WHERE username = %s", (username,))
