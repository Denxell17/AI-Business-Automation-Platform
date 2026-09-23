"""Permission-scoped invoice and protected document routes."""

import hashlib
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from authorization import MANAGE_INVOICES, VIEW_INVOICES, user_has_permission
from document_storage import DocumentStorage
from invoice_repository import (
    list_invoice_customers, load_invoice_events, load_invoice_line_items,
    list_invoice_workflow_runs, list_invoices, load_document, load_invoice,
    load_invoice_document,
)
from invoice_service import (
    INVOICE_STATUS_TRANSITIONS, available_invoice_workflows,
    change_invoice_status, create_invoice, generate_invoice_document,
    trigger_invoice_workflow,
)
from web_session import load_authenticated_session_user


LINE_INPUT_COUNT = 5


def register_invoice_routes(application: FastAPI, templates: Jinja2Templates,
                            database_file: Path, storage: DocumentStorage,
                            csrf_token_for, csrf_is_valid, log_activity) -> None:
    def access(request: Request, permission: str):
        actor = load_authenticated_session_user(request, database_file)
        if actor is None:
            return None, RedirectResponse(url=request.url_for("login_page"), status_code=303)
        if not user_has_permission(actor, permission):
            return None, HTMLResponse("Access denied.", status_code=403)
        return actor, None

    def page(request, name, title, actor, **context):
        return templates.TemplateResponse(request=request, name=name, context={
            "page_title": title, "active_page": "invoices", "current_user": actor,
            "csrf_token": csrf_token_for(request),
            "can_manage_invoices": user_has_permission(actor, MANAGE_INVOICES),
            **context,
        })

    async def form(request):
        submitted = await request.form()
        if not csrf_is_valid(request, str(submitted.get("csrf_token", ""))):
            return None
        return submitted

    def lines_from_form(submitted):
        lines = []
        for line_number in range(1, LINE_INPUT_COUNT + 1):
            description = str(submitted.get(f"description_{line_number}", "")).strip()
            quantity = str(submitted.get(f"quantity_{line_number}", "")).strip()
            unit_price = str(submitted.get(f"unit_price_{line_number}", "")).strip()
            tax_rate = str(submitted.get(f"tax_rate_{line_number}", "")).strip()
            if not any((description, quantity, unit_price, tax_rate)):
                continue
            lines.append({"description": description, "quantity": quantity,
                          "unit_price": unit_price, "tax_rate_percent": tax_rate or "0"})
        return lines

    @application.get("/invoices", response_class=HTMLResponse)
    def invoice_directory(request: Request, customer_id: str = "") -> Response:
        actor, denied = access(request, VIEW_INVOICES)
        if denied:
            return denied
        if len(customer_id) > 64:
            return HTMLResponse("Customer filter is invalid.", status_code=400)
        return page(request, "invoices.html", "Invoices", actor,
                    invoices=list_invoices(customer_id.strip() or None, database_file),
                    selected_customer_id=customer_id.strip())

    @application.get("/invoices/new", response_class=HTMLResponse)
    def invoice_create_form(request: Request) -> Response:
        actor, denied = access(request, MANAGE_INVOICES)
        if denied:
            return denied
        return page(request, "invoice_form.html", "Create invoice", actor,
                    customers=list_invoice_customers(database_file), form_values={},
                    line_input_count=LINE_INPUT_COUNT, error_message=None)

    @application.post("/invoices/new")
    async def invoice_create(request: Request) -> Response:
        actor, denied = access(request, MANAGE_INVOICES)
        if denied:
            return denied
        submitted = await form(request)
        if submitted is None:
            return HTMLResponse("Invalid CSRF token.", status_code=403)
        try:
            invoice_id = create_invoice(
                actor, str(submitted.get("customer_id", "")),
                str(submitted.get("invoice_number", "")),
                str(submitted.get("due_date", "")), lines_from_form(submitted), database_file,
            )
        except ValueError as error:
            return page(request, "invoice_form.html", "Create invoice", actor,
                        customers=list_invoice_customers(database_file), form_values=dict(submitted),
                        line_input_count=LINE_INPUT_COUNT, error_message=str(error))
        log_activity(f"Invoice {invoice_id} created by user {actor['username']}.")
        return RedirectResponse(url=request.url_for("invoice_detail", invoice_id=invoice_id), status_code=303)

    @application.get("/invoices/{invoice_id}", response_class=HTMLResponse)
    def invoice_detail(request: Request, invoice_id: str) -> Response:
        actor, denied = access(request, VIEW_INVOICES)
        if denied:
            return denied
        invoice = load_invoice(invoice_id, database_file)
        if invoice is None:
            return HTMLResponse("Invoice not found.", status_code=404)
        return page(request, "invoice_detail.html", invoice["invoice_number"], actor,
                    invoice=invoice, line_items=load_invoice_line_items(invoice_id, database_file),
                    events=load_invoice_events(invoice_id, database_file),
                    document=load_invoice_document(invoice_id, database_file),
                    workflow_runs=list_invoice_workflow_runs(invoice_id, database_file),
                    status_options=sorted(INVOICE_STATUS_TRANSITIONS[invoice["status"]]),
                    workflows=available_invoice_workflows(actor, database_file)
                    if user_has_permission(actor, MANAGE_INVOICES) else [])

    @application.post("/invoices/{invoice_id}/status")
    async def invoice_status_change(request: Request, invoice_id: str) -> Response:
        actor, denied = access(request, MANAGE_INVOICES)
        if denied:
            return denied
        submitted = await form(request)
        if submitted is None:
            return HTMLResponse("Invalid CSRF token.", status_code=403)
        try:
            changed = change_invoice_status(actor, invoice_id, str(submitted.get("status", "")), database_file)
        except ValueError as error:
            return HTMLResponse(str(error), status_code=409)
        if not changed:
            return HTMLResponse("Invoice status could not be changed.", status_code=409)
        log_activity(f"Invoice {invoice_id} status changed by user {actor['username']}.")
        return RedirectResponse(url=request.url_for("invoice_detail", invoice_id=invoice_id), status_code=303)

    @application.post("/invoices/{invoice_id}/document")
    async def invoice_document_generate(request: Request, invoice_id: str) -> Response:
        actor, denied = access(request, MANAGE_INVOICES)
        if denied:
            return denied
        if await form(request) is None:
            return HTMLResponse("Invalid CSRF token.", status_code=403)
        try:
            document = generate_invoice_document(actor, invoice_id, storage, database_file)
        except (OSError, ValueError):
            return HTMLResponse("Invoice document could not be generated.", status_code=503)
        if document is None:
            return HTMLResponse("Invoice not found.", status_code=404)
        log_activity(f"Invoice document {document['document_id']} generated by user {actor['username']}.")
        return RedirectResponse(url=request.url_for("invoice_detail", invoice_id=invoice_id), status_code=303)

    @application.get("/documents/{document_id}/download")
    def document_download(request: Request, document_id: str) -> Response:
        actor, denied = access(request, VIEW_INVOICES)
        if denied:
            return denied
        document = load_document(document_id, database_file)
        if document is None:
            return HTMLResponse("Document not found.", status_code=404)
        try:
            content = storage.read(document["storage_key"])
        except (OSError, ValueError):
            return HTMLResponse("Document is unavailable.", status_code=503)
        if (len(content) != document["byte_size"] or
                hashlib.sha256(content).hexdigest() != document["content_sha256"]):
            return HTMLResponse("Document is unavailable.", status_code=503)
        return Response(content=content, media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="{document["filename"]}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        })

    @application.post("/invoices/{invoice_id}/workflow")
    async def invoice_workflow_start(request: Request, invoice_id: str) -> Response:
        actor, denied = access(request, MANAGE_INVOICES)
        if denied:
            return denied
        submitted = await form(request)
        if submitted is None:
            return HTMLResponse("Invalid CSRF token.", status_code=403)
        try:
            execution_id = trigger_invoice_workflow(actor, invoice_id,
                                                    str(submitted.get("workflow_id", "")), database_file)
        except ValueError as error:
            return HTMLResponse(str(error), status_code=409)
        if execution_id is None:
            return HTMLResponse("Invoice workflow could not start.", status_code=409)
        log_activity(f"Invoice {invoice_id} started workflow execution {execution_id} by user {actor['username']}.")
        return RedirectResponse(url=request.url_for("invoice_detail", invoice_id=invoice_id), status_code=303)
