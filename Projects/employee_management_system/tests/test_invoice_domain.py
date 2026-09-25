import re
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from crm_service import convert_lead, create_lead, update_lead
from dashboard_repository import load_dashboard_snapshot
from database import get_database_connection, load_user_account_by_username
from document_storage import PrivateFileSystemDocumentStorage
from invoice_repository import load_invoice, load_invoice_document, load_invoice_line_items
from invoice_service import calculate_invoice_lines, change_invoice_status, create_invoice
from user_service import register_user_account
from web_app import create_web_application
from workflow_service import create_workflow, create_workflow_task, update_workflow


class TestInvoiceDomain(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.database_file = root / "invoices.db"
        self.document_storage = PrivateFileSystemDocumentStorage(root / "private-documents")
        self.assertTrue(register_user_account("InvoiceAdmin", "SecureAdminPassword123!", "admin", self.database_file))
        self.assertTrue(register_user_account("InvoiceViewer", "SecureViewerPassword123!", "viewer", self.database_file))
        self.admin = load_user_account_by_username("InvoiceAdmin", self.database_file)
        self.viewer = load_user_account_by_username("InvoiceViewer", self.database_file)
        self.customer_id = self.create_customer()
        self.client = TestClient(create_web_application(
            database_file=self.database_file, session_secret="invoice-test-session",
            document_storage=self.document_storage,
        ))

    def tearDown(self):
        self.client.close()
        self.temporary_directory.cleanup()

    def create_customer(self):
        lead_id = create_lead(self.admin, "Invoice Customer", "customer@example.test",
                              company="Example Company", owner_user_id=self.admin["user_id"],
                              database_file=self.database_file)
        self.assertTrue(update_lead(self.admin, lead_id, "Invoice Customer", "customer@example.test",
                                    "", "Example Company", "contacted", self.admin["user_id"], self.database_file))
        self.assertTrue(update_lead(self.admin, lead_id, "Invoice Customer", "customer@example.test",
                                    "", "Example Company", "qualified", self.admin["user_id"], self.database_file))
        return convert_lead(self.admin, lead_id, self.database_file)

    def sign_in(self, username="InvoiceAdmin", password="SecureAdminPassword123!"):
        self.client.post("/login", data={"username": username, "password": password})

    def csrf(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, response.text)
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
        self.assertIsNotNone(match)
        return match.group(1)

    def invoice_lines(self):
        return [
            {"description": "Fractional service", "quantity": "0.333", "unit_price": "10.00", "tax_rate_percent": "7.50"},
            {"description": "Fixed service", "quantity": "1", "unit_price": "5.01", "tax_rate_percent": "0"},
        ]

    def test_decimal_snapshots_status_history_and_immutability(self):
        lines, subtotal, taxes, total = calculate_invoice_lines(self.invoice_lines())
        self.assertEqual((subtotal, taxes, total), (834, 25, 859))
        invoice_id = create_invoice(self.admin, self.customer_id, "INV-1001", "2026-10-15",
                                    self.invoice_lines(), self.database_file)
        invoice = load_invoice(invoice_id, self.database_file)
        self.assertEqual((invoice["subtotal_cents"], invoice["tax_cents"], invoice["total_cents"]), (834, 25, 859))
        self.assertTrue(change_invoice_status(self.admin, invoice_id, "sent", self.database_file))
        self.assertTrue(change_invoice_status(self.admin, invoice_id, "paid", self.database_file))
        with self.assertRaises(ValueError):
            change_invoice_status(self.admin, invoice_id, "void", self.database_file)
        line = load_invoice_line_items(invoice_id, self.database_file)[0]
        connection = get_database_connection(self.database_file)
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("UPDATE invoice_line_items SET description = ? WHERE line_item_id = ?",
                               ("Changed", line["line_item_id"]))
        connection.close()
        snapshot = load_dashboard_snapshot(self.database_file, include_employees=False,
                                           include_workflows=False, include_agents=False,
                                           include_crm=False, include_invoices=True)
        self.assertEqual(snapshot["invoice_total"], 1)
        self.assertEqual(snapshot["outstanding_invoice_total_cents"], 0)

    def test_web_pdf_download_permissions_and_workflow_link(self):
        self.assertEqual(self.client.get("/invoices", follow_redirects=False).status_code, 303)
        self.sign_in()
        token = self.csrf("/invoices/new")
        created = self.client.post("/invoices/new", data={
            "csrf_token": token, "customer_id": self.customer_id, "invoice_number": "INV-1002",
            "due_date": "2026-10-20", "description_1": "Portfolio invoice",
            "quantity_1": "1", "unit_price_1": "25.00", "tax_rate_1": "0",
        }, follow_redirects=False)
        self.assertEqual(created.status_code, 303, created.text)
        invoice_id = created.headers["location"].rsplit("/", 1)[-1]
        generated = self.client.post(f"/invoices/{invoice_id}/document", data={"csrf_token": token}, follow_redirects=False)
        self.assertEqual(generated.status_code, 303)
        document = load_invoice_document(invoice_id, self.database_file)
        self.assertIsNotNone(document)
        download = self.client.get(f"/documents/{document['document_id']}/download")
        self.assertEqual(download.status_code, 200)
        self.assertTrue(download.content.startswith(b"%PDF-"))
        self.assertEqual(download.headers["content-type"], "application/pdf")
        self.assertIn('attachment; filename="invoice-INV-1002.pdf"', download.headers["content-disposition"])
        self.assertEqual(download.headers["cache-control"], "private, no-store")
        self.assertEqual(self.client.get(f"/static/documents/{document['storage_key']}").status_code, 404)
        self.assertTrue(create_workflow(self.admin, "WF-INVOICE", "Invoice follow-up", "Synthetic", "draft", self.database_file))
        self.assertTrue(create_workflow_task(self.admin, "TASK-INVOICE", "WF-INVOICE", 1,
                                             "Follow up", "Synthetic", "manual", True, self.database_file))
        self.assertTrue(update_workflow(self.admin, "WF-INVOICE", "Invoice follow-up", "Synthetic", "active", self.database_file))
        run = self.client.post(f"/invoices/{invoice_id}/workflow", data={
            "csrf_token": token, "workflow_id": "WF-INVOICE",
        }, follow_redirects=False)
        self.assertEqual(run.status_code, 303, run.text)
        self.client.post("/logout")
        self.sign_in("InvoiceViewer", "SecureViewerPassword123!")
        self.assertEqual(self.client.get("/invoices").status_code, 200)
        self.assertEqual(self.client.get(f"/documents/{document['document_id']}/download").status_code, 200)
        self.assertEqual(self.client.get("/invoices/new").status_code, 403)
        self.assertEqual(self.client.post(f"/invoices/{invoice_id}/document", data={}).status_code, 403)

    def test_rejects_invalid_money_and_private_storage_key(self):
        with self.assertRaises(ValueError):
            calculate_invoice_lines([{"description": "Bad", "quantity": "1.0001", "unit_price": "1.00"}])
        with self.assertRaises(PermissionError):
            create_invoice(self.viewer, self.customer_id, "INV-1003", "", self.invoice_lines(), self.database_file)
        with self.assertRaises(ValueError):
            self.document_storage.save("../outside.pdf", b"data")
