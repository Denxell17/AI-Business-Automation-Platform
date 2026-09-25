"""Authenticated, CSRF-protected CRM screens."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from authorization import MANAGE_CRM, VIEW_CRM, user_has_permission
from crm_repository import (
    list_assignable_owners, list_crm_history, list_customers,
    list_lead_notes, list_leads, load_customer, load_lead,
)
from crm_service import (
    ALLOWED_LEAD_STAGE_TRANSITIONS, add_lead_note, convert_lead,
    create_lead, update_customer, update_lead,
)
from models import CUSTOMER_STATUSES
from web_session import load_authenticated_session_user


def register_crm_routes(application: FastAPI, templates: Jinja2Templates,
                        database_file: Path, csrf_token_for, csrf_is_valid,
                        log_activity) -> None:
    def access(request: Request, permission: str):
        actor = load_authenticated_session_user(request, database_file)
        if actor is None:
            return None, RedirectResponse(url=request.url_for("login_page"), status_code=303)
        if not user_has_permission(actor, permission):
            return None, HTMLResponse("Access denied.", status_code=403)
        return actor, None

    def page(request, name, title, active, actor, **context):
        return templates.TemplateResponse(request=request, name=name, context={
            "page_title": title, "active_page": active, "current_user": actor,
            "csrf_token": csrf_token_for(request),
            "can_manage_crm": user_has_permission(actor, MANAGE_CRM),
            **context,
        })

    async def form_values(request):
        form = await request.form()
        if not csrf_is_valid(request, str(form.get("csrf_token", ""))):
            return None
        return form

    def owner_from_form(form):
        raw = str(form.get("owner_user_id", "")).strip()
        if not raw:
            return None
        try:
            value = int(raw)
        except ValueError as error:
            raise ValueError("Owner is invalid.") from error
        if value <= 0:
            raise ValueError("Owner is invalid.")
        return value

    def contact(form):
        return tuple(str(form.get(key, "")) for key in
                     ("name", "email", "phone_number", "company"))

    @application.get("/leads", response_class=HTMLResponse)
    def lead_directory(request: Request, q: str = "") -> Response:
        actor, denied = access(request, VIEW_CRM)
        if denied:
            return denied
        if len(q) > 120:
            return HTMLResponse("Search is too long.", status_code=400)
        return page(request, "crm_directory.html", "Leads", "leads", actor,
                    kind="lead", records=list_leads(q.strip(), database_file), query=q.strip())

    @application.get("/leads/new", response_class=HTMLResponse)
    def lead_create_form(request: Request) -> Response:
        actor, denied = access(request, MANAGE_CRM)
        if denied:
            return denied
        return page(request, "crm_form.html", "New lead", "leads", actor,
                    kind="lead", record={}, owners=list_assignable_owners(database_file),
                    stages=["new"], error_message=None)

    @application.post("/leads/new")
    async def lead_create(request: Request) -> Response:
        actor, denied = access(request, MANAGE_CRM)
        if denied:
            return denied
        form = await form_values(request)
        if form is None:
            return HTMLResponse("Invalid CSRF token.", status_code=403)
        try:
            lead_id = create_lead(actor, *contact(form), owner_from_form(form), database_file)
        except ValueError as error:
            return page(request, "crm_form.html", "New lead", "leads", actor,
                        kind="lead", record=dict(form), owners=list_assignable_owners(database_file),
                        stages=["new"], error_message=str(error))
        log_activity(f"Lead {lead_id} created by user {actor['username']}.")
        return RedirectResponse(url=request.url_for("lead_detail", lead_id=lead_id), status_code=303)

    @application.get("/leads/{lead_id}", response_class=HTMLResponse)
    def lead_detail(request: Request, lead_id: str) -> Response:
        actor, denied = access(request, VIEW_CRM)
        if denied:
            return denied
        lead = load_lead(lead_id, database_file)
        if lead is None:
            return HTMLResponse("Lead not found.", status_code=404)
        return page(request, "crm_detail.html", lead["name"], "leads", actor,
                    kind="lead", record=lead,
                    notes=list_lead_notes(lead_id, database_file),
                    history=list_crm_history("lead", lead_id, database_file))

    @application.get("/leads/{lead_id}/edit", response_class=HTMLResponse)
    def lead_edit_form(request: Request, lead_id: str) -> Response:
        actor, denied = access(request, MANAGE_CRM)
        if denied:
            return denied
        lead = load_lead(lead_id, database_file)
        if lead is None:
            return HTMLResponse("Lead not found.", status_code=404)
        if lead["stage"] == "converted":
            return HTMLResponse("Converted leads cannot be edited.", status_code=409)
        return page(request, "crm_form.html", "Edit lead", "leads", actor,
                    kind="lead", record=lead, owners=list_assignable_owners(database_file),
                    stages=sorted(ALLOWED_LEAD_STAGE_TRANSITIONS[lead["stage"]]),
                    error_message=None)

    @application.post("/leads/{lead_id}/edit")
    async def lead_edit(request: Request, lead_id: str) -> Response:
        actor, denied = access(request, MANAGE_CRM)
        if denied:
            return denied
        form = await form_values(request)
        if form is None:
            return HTMLResponse("Invalid CSRF token.", status_code=403)
        try:
            updated = update_lead(actor, lead_id, *contact(form),
                                  str(form.get("stage", "")), owner_from_form(form), database_file)
        except ValueError as error:
            return HTMLResponse(str(error), status_code=400)
        if not updated:
            return HTMLResponse("Lead cannot be edited.", status_code=409)
        log_activity(f"Lead {lead_id} updated by user {actor['username']}.")
        return RedirectResponse(url=request.url_for("lead_detail", lead_id=lead_id), status_code=303)

    @application.post("/leads/{lead_id}/notes")
    async def lead_note_create(request: Request, lead_id: str) -> Response:
        actor, denied = access(request, MANAGE_CRM)
        if denied:
            return denied
        form = await form_values(request)
        if form is None:
            return HTMLResponse("Invalid CSRF token.", status_code=403)
        try:
            note_id = add_lead_note(actor, lead_id, str(form.get("body", "")), database_file)
        except ValueError as error:
            return HTMLResponse(str(error), status_code=400)
        if note_id is None:
            return HTMLResponse("Lead cannot accept notes.", status_code=409)
        log_activity(f"Note {note_id} added to lead {lead_id} by user {actor['username']}.")
        return RedirectResponse(url=request.url_for("lead_detail", lead_id=lead_id), status_code=303)

    @application.post("/leads/{lead_id}/convert")
    async def lead_convert(request: Request, lead_id: str) -> Response:
        actor, denied = access(request, MANAGE_CRM)
        if denied:
            return denied
        if await form_values(request) is None:
            return HTMLResponse("Invalid CSRF token.", status_code=403)
        customer_id = convert_lead(actor, lead_id, database_file)
        if customer_id is None:
            return HTMLResponse("Only qualified leads can be converted.", status_code=409)
        log_activity(f"Lead {lead_id} converted to customer {customer_id} by user {actor['username']}.")
        return RedirectResponse(url=request.url_for("customer_detail", customer_id=customer_id), status_code=303)

    @application.get("/customers", response_class=HTMLResponse)
    def customer_directory(request: Request, q: str = "") -> Response:
        actor, denied = access(request, VIEW_CRM)
        if denied:
            return denied
        if len(q) > 120:
            return HTMLResponse("Search is too long.", status_code=400)
        return page(request, "crm_directory.html", "Customers", "customers", actor,
                    kind="customer", records=list_customers(q.strip(), database_file), query=q.strip())

    @application.get("/customers/{customer_id}", response_class=HTMLResponse)
    def customer_detail(request: Request, customer_id: str) -> Response:
        actor, denied = access(request, VIEW_CRM)
        if denied:
            return denied
        customer = load_customer(customer_id, database_file)
        if customer is None:
            return HTMLResponse("Customer not found.", status_code=404)
        return page(request, "crm_detail.html", customer["name"], "customers", actor,
                    kind="customer", record=customer, notes=[],
                    history=list_crm_history("customer", customer_id, database_file))

    @application.get("/customers/{customer_id}/edit", response_class=HTMLResponse)
    def customer_edit_form(request: Request, customer_id: str) -> Response:
        actor, denied = access(request, MANAGE_CRM)
        if denied:
            return denied
        customer = load_customer(customer_id, database_file)
        if customer is None:
            return HTMLResponse("Customer not found.", status_code=404)
        return page(request, "crm_form.html", "Edit customer", "customers", actor,
                    kind="customer", record=customer, owners=[], stages=sorted(CUSTOMER_STATUSES),
                    error_message=None)

    @application.post("/customers/{customer_id}/edit")
    async def customer_edit(request: Request, customer_id: str) -> Response:
        actor, denied = access(request, MANAGE_CRM)
        if denied:
            return denied
        form = await form_values(request)
        if form is None:
            return HTMLResponse("Invalid CSRF token.", status_code=403)
        try:
            updated = update_customer(actor, customer_id, *contact(form),
                                      str(form.get("status", "")), database_file)
        except ValueError as error:
            return HTMLResponse(str(error), status_code=400)
        if not updated:
            return HTMLResponse("Customer not found.", status_code=404)
        log_activity(f"Customer {customer_id} updated by user {actor['username']}.")
        return RedirectResponse(url=request.url_for("customer_detail", customer_id=customer_id), status_code=303)
