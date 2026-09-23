"""Invoice domain integration against an explicitly configured disposable PostgreSQL database."""

import os
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient

from crm_service import convert_lead, create_lead, update_lead
from document_storage import PrivateFileSystemDocumentStorage
from invoice_repository import load_invoice, load_invoice_document, load_invoice_line_items
from invoice_service import create_invoice
from postgresql_migrations import apply_postgresql_migrations
from user_service import register_user_account
from web_app import create_web_application


TEST_DATABASE_URL = os.environ.get("ABAP_TEST_DATABASE_URL", "").strip()


@unittest.skipUnless(TEST_DATABASE_URL, "ABAP_TEST_DATABASE_URL is required for live PostgreSQL tests.")
class TestInvoicePostgresqlIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment = patch.dict(os.environ, {"DATABASE_BACKEND": "postgresql", "DATABASE_URL": TEST_DATABASE_URL})
        cls.environment.start()
        apply_postgresql_migrations(TEST_DATABASE_URL)

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()

    def test_invoice_document_and_download_use_live_postgresql(self):
        suffix = uuid4().hex[:12]
        username = f"m5_{suffix}"
        lead_id = None
        customer_id = None
        invoice_id = None
        with TemporaryDirectory() as temporary_directory:
            try:
                self.assertTrue(register_user_account(username, "SyntheticM5Password123!", "admin"))
                from database import load_user_account_by_username
                actor = load_user_account_by_username(username)
                lead_id = create_lead(actor, "Synthetic Invoice Customer", "invoice@example.test",
                                      owner_user_id=actor["user_id"])
                self.assertTrue(update_lead(actor, lead_id, "Synthetic Invoice Customer", "invoice@example.test", "", "Synthetic", "contacted", actor["user_id"]))
                self.assertTrue(update_lead(actor, lead_id, "Synthetic Invoice Customer", "invoice@example.test", "", "Synthetic", "qualified", actor["user_id"]))
                customer_id = convert_lead(actor, lead_id)
                invoice_id = create_invoice(actor, customer_id, f"INV-{suffix.upper()}", "2026-10-30", [{
                    "description": "Synthetic service", "quantity": "1.250",
                    "unit_price": "12.34", "tax_rate_percent": "7.50",
                }])
                self.assertEqual(load_invoice(invoice_id)["total_cents"], 1659)
                storage = PrivateFileSystemDocumentStorage(Path(temporary_directory) / "private")
                with TestClient(create_web_application(session_secret="synthetic-m5-session", document_storage=storage)) as client:
                    client.post("/login", data={"username": username, "password": "SyntheticM5Password123!"})
                    detail = client.get(f"/invoices/{invoice_id}")
                    token = re.search(r'name="csrf_token"\s+value="([^"]+)"', detail.text).group(1)
                    generated = client.post(f"/invoices/{invoice_id}/document", data={"csrf_token": token}, follow_redirects=False)
                    self.assertEqual(generated.status_code, 303)
                    document = load_invoice_document(invoice_id)
                    download = client.get(f"/documents/{document['document_id']}/download")
                    self.assertEqual(download.status_code, 200)
                    self.assertTrue(download.content.startswith(b"%PDF-"))
                with psycopg.connect(TEST_DATABASE_URL) as connection:
                    with self.assertRaises(psycopg.Error):
                        connection.execute("UPDATE invoice_line_items SET description = %s WHERE invoice_id = %s", ("changed", invoice_id))
                    connection.rollback()
            finally:
                with psycopg.connect(TEST_DATABASE_URL) as connection:
                    if invoice_id:
                        connection.execute("DELETE FROM protected_documents WHERE invoice_id = %s", (invoice_id,))
                        connection.execute("DELETE FROM invoice_payment_events WHERE invoice_id = %s", (invoice_id,))
                        connection.execute("DELETE FROM invoice_line_items WHERE invoice_id = %s", (invoice_id,))
                        connection.execute("DELETE FROM invoices WHERE invoice_id = %s", (invoice_id,))
                    if customer_id:
                        connection.execute("DELETE FROM crm_audit_events WHERE entity_id = %s", (customer_id,))
                        connection.execute("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
                    if lead_id:
                        connection.execute("DELETE FROM crm_audit_events WHERE entity_id = %s", (lead_id,))
                        connection.execute("DELETE FROM leads WHERE lead_id = %s", (lead_id,))
                    connection.execute("DELETE FROM users WHERE username = %s", (username,))
