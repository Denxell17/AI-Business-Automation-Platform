"""Closed tool set with refreshed accounts, scoped SQL and domain service writes."""

import sqlite3
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from authorization import (EXECUTE_AGENT_TEMPLATES, VIEW_CRM, MANAGE_CRM,
    VIEW_INVOICES, MANAGE_INVOICES, VIEW_EMPLOYEE, VIEW_WORKFLOWS,
    MANAGE_WORKFLOWS, user_has_permission)
from database import (get_database_connection, load_user_account_by_username,
                      load_workflow_by_id)
from crm_repository import load_lead, load_customer
from crm_service import create_lead, update_lead, convert_lead, validate_contact
from invoice_service import create_invoice, calculate_invoice_lines
from workflow_service import start_workflow_execution


class Arguments(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Read(Arguments):
    tool: Literal['leads', 'customers', 'invoices', 'employees', 'workflows', 'activity']


class Contact(Arguments):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(default='', max_length=254)
    phone_number: str = Field(default='', max_length=40)
    company: str = Field(default='', max_length=120)


class LeadCreate(Contact):
    tool: Literal['create_lead']


class LeadUpdate(Contact):
    tool: Literal['update_lead']
    lead_id: str = Field(min_length=1, max_length=60)
    stage: Literal['new', 'contacted', 'qualified', 'unqualified']


class CustomerPrepare(Arguments):
    tool: Literal['prepare_customer']
    lead_id: str = Field(min_length=1, max_length=60)


class Line(Arguments):
    description: str = Field(min_length=1, max_length=300)
    quantity: str = Field(min_length=1, max_length=30)
    unit_price: str = Field(min_length=1, max_length=30)
    tax_rate_percent: str = Field(default='0', max_length=10)


class InvoiceDraft(Arguments):
    tool: Literal['draft_invoice']
    customer_id: str = Field(min_length=1, max_length=60)
    invoice_number: str = Field(min_length=1, max_length=40)
    due_date: str = Field(default='', max_length=10)
    lines: list[Line] = Field(min_length=1, max_length=20)


class WorkflowStart(Arguments):
    tool: Literal['start_workflow']
    workflow_id: str = Field(min_length=1, max_length=60)


WRITES = {schema.model_fields['tool'].annotation.__args__[0]: schema for schema in
          (LeadCreate, LeadUpdate, CustomerPrepare, InvoiceDraft, WorkflowStart)}


def actor_now(actor, database_file, permission=EXECUTE_AGENT_TEMPLATES):
    stored = load_user_account_by_username(actor['username'], database_file)
    if (not stored or not stored['is_active'] or stored['user_id'] != actor['user_id']
            or stored['session_version'] != actor['session_version']
            or not user_has_permission(stored, EXECUTE_AGENT_TEMPLATES)
            or not user_has_permission(stored, permission)):
        raise PermissionError('Assistant access denied.')
    return stored


def _query(database_file, sql, parameters=()):
    connection = get_database_connection(database_file)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute(sql, parameters).fetchall()]
    finally:
        connection.close()


def read_tool(actor, arguments, database_file):
    name = Read.model_validate(arguments).tool
    permission = {'leads': VIEW_CRM, 'customers': VIEW_CRM, 'invoices': VIEW_INVOICES,
                  'employees': VIEW_EMPLOYEE, 'workflows': VIEW_WORKFLOWS, 'activity': VIEW_CRM}[name]
    actor = actor_now(actor, database_file, permission)
    from assistant_demo import demo_only, synthetic_result
    if demo_only():
        return synthetic_result(arguments, actor, database_file)
    identity = (actor['user_id'],)
    # SQL is constant, bounded, parameterized. No contact details, payroll or free-text notes.
    queries = {
        'leads': ('''SELECT lead_id,name,company,stage FROM leads
            WHERE owner_user_id=? ORDER BY updated_at DESC LIMIT 30''', identity),
        'customers': ('''SELECT c.customer_id,c.name,c.company,c.status FROM customers c
            JOIN leads l ON l.lead_id=c.source_lead_id WHERE l.owner_user_id=?
            ORDER BY c.updated_at DESC LIMIT 30''', identity),
        'invoices': ('''SELECT i.invoice_id,i.invoice_number,i.customer_id,i.status,i.currency,
            i.total_cents,i.due_date FROM invoices i JOIN customers c ON c.customer_id=i.customer_id
            JOIN leads l ON l.lead_id=c.source_lead_id
            WHERE l.owner_user_id=? AND i.created_by_user_id=? ORDER BY i.updated_at DESC LIMIT 30''', identity * 2),
        'employees': ('''SELECT employee_id,name,department,position FROM employees
            ORDER BY employee_id LIMIT 30''', ()),
        'workflows': ('''SELECT workflow_id,name,status,n8n_enabled FROM workflows
            WHERE created_by_user_id=? ORDER BY updated_at DESC LIMIT 30''', identity),
        'activity': ('''SELECT entity_type,entity_id,event_type,created_at FROM crm_audit_events
            WHERE actor_user_id=? ORDER BY created_at DESC LIMIT 30''', identity),
    }
    rows = _query(database_file, *queries[name])
    if name == 'workflows':
        for row in rows:
            row['executions'] = _query(database_file, '''SELECT execution_id,status,started_at,finished_at
                FROM workflow_executions WHERE workflow_id=? AND started_by_user_id=?
                ORDER BY started_at DESC LIMIT 5''', (row['workflow_id'], actor['user_id']))
    result = {'tool': name, 'scope': 'Authorized sample, maximum 30 records; not complete business totals.', 'records': rows}
    if name == 'invoices':
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date().isoformat()
        outstanding = [r for r in rows if r['status'] == 'sent']
        overdue = [r for r in outstanding if r['due_date'] and r['due_date'] < today]
        result['sample_summary'] = {'as_of_utc': today, 'currency': 'USD',
            'outstanding_sent_total_cents': sum(r['total_cents'] for r in outstanding),
            'overdue_sent_total_cents': sum(r['total_cents'] for r in overdue),
            'overdue_sent_count': len(overdue)}
    return result


def _owned_lead(actor, identity, database_file):
    lead = load_lead(identity, database_file)
    if not lead or lead['owner_user_id'] != actor['user_id']:
        raise PermissionError('Record is unavailable.')
    return lead


def validate_action(actor, arguments, database_file):
    from assistant_demo import demo_only
    if demo_only():
        raise PermissionError('Live business actions are disabled in demonstration mode.')
    if (not isinstance(arguments, dict) or not isinstance(arguments.get('tool'), str)
            or arguments.get('tool') not in WRITES):
        raise ValueError('Unsupported action.')
    values = WRITES[arguments['tool']].model_validate(arguments).model_dump()
    name = values['tool']
    permission = MANAGE_INVOICES if name == 'draft_invoice' else MANAGE_WORKFLOWS if name == 'start_workflow' else MANAGE_CRM
    actor = actor_now(actor, database_file, permission)
    if name in ('create_lead', 'update_lead'):
        values.update(validate_contact(**{k: values[k] for k in ('name', 'email', 'phone_number', 'company')}))
    if name in ('update_lead', 'prepare_customer'):
        lead = _owned_lead(actor, values['lead_id'], database_file)
        if name == 'prepare_customer' and lead['stage'] != 'qualified':
            raise ValueError('Only an owned qualified lead can become a customer.')
        if name == 'update_lead':
            from crm_service import ALLOWED_LEAD_STAGE_TRANSITIONS
            if lead['stage'] == 'converted' or values['stage'] not in ALLOWED_LEAD_STAGE_TRANSITIONS[lead['stage']]:
                raise ValueError('Lead stage transition is invalid.')
    if name == 'draft_invoice':
        customer = load_customer(values['customer_id'], database_file)
        if not customer or customer['status'] != 'active':
            raise ValueError('Customer is unavailable.')
        _owned_lead(actor, customer['source_lead_id'], database_file)
        calculate_invoice_lines(values['lines'])
        from invoice_service import INVOICE_NUMBER_PATTERN
        from datetime import date
        values['invoice_number'] = values['invoice_number'].strip().upper()
        if not INVOICE_NUMBER_PATTERN.fullmatch(values['invoice_number']):
            raise ValueError('Invoice number is invalid.')
        if values['due_date']:
            date.fromisoformat(values['due_date'])
    if name == 'start_workflow':
        workflow = load_workflow_by_id(values['workflow_id'], database_file)
        if (not workflow or workflow['created_by_user_id'] != actor['user_id']
                or workflow['status'] != 'active'):
            raise PermissionError('Only owned active workflows are supported.')
        if workflow['n8n_enabled']:
            require_dispatch_allowed(workflow['workflow_id'])
    return values


def execute_action(actor, values, database_file):
    values = validate_action(actor, values, database_file)
    name = values.pop('tool')
    actor = actor_now(actor, database_file)
    if name == 'create_lead':
        return create_lead(actor, **values, owner_user_id=actor['user_id'], database_file=database_file)
    if name == 'update_lead':
        return update_lead(actor, **values, owner_user_id=actor['user_id'], database_file=database_file)
    if name == 'prepare_customer':
        return convert_lead(actor, values['lead_id'], database_file)
    if name == 'draft_invoice':
        return create_invoice(actor, **values, database_file=database_file)
    workflow = load_workflow_by_id(values['workflow_id'], database_file)
    if workflow and workflow['n8n_enabled']:
        from business_transaction import current_connection
        if current_connection(database_file) is None:
            raise ValueError('Dispatch requires atomic confirmation.')
    result = start_workflow_execution(actor, values['workflow_id'], database_file)
    if result:
        workflow = load_workflow_by_id(values['workflow_id'], database_file)
        if workflow['n8n_enabled']:
            from business_transaction import current_connection
            if current_connection(database_file) is None:
                raise ValueError('Dispatch requires an atomic confirmation transaction.')
            require_dispatch_allowed(workflow['workflow_id'])
            from datetime import datetime, timezone
            from uuid import uuid4
            from webhook_contract import build_webhook_envelope
            from webhook_delivery_service import queue_outbound_webhook_delivery
            now = datetime.now(timezone.utc)
            envelope = build_webhook_envelope(str(uuid4()), result['execution_id'],
                'workflow.execution.started', now, {'execution_id': result['execution_id'],
                'workflow_id': result['workflow_id'], 'trigger_type': 'manual'})
            if not queue_outbound_webhook_delivery(envelope, now, database_file):
                raise ValueError('Outbox insertion failed.')
    return result['execution_id'] if result else None


def action_review(actor, values, database_file):
    """Bind the review to the current object version and implicit copied fields."""
    name = values['tool']
    if name in ('update_lead', 'prepare_customer'):
        row = _owned_lead(actor, values['lead_id'], database_file)
        return {k: row[k] for k in ('lead_id', 'name', 'email', 'phone_number',
                                    'company', 'stage', 'owner_user_id', 'updated_at')}
    if name == 'draft_invoice':
        row = load_customer(values['customer_id'], database_file)
        _, subtotal, tax, total = calculate_invoice_lines(values['lines'])
        return {'customer_id': row['customer_id'], 'customer_name': row['name'],
                'updated_at': row['updated_at'], 'currency': 'USD',
                'subtotal_cents': subtotal, 'tax_cents': tax, 'total_cents': total}
    if name == 'start_workflow':
        row = load_workflow_by_id(values['workflow_id'], database_file)
        return {k: row[k] for k in ('workflow_id', 'name', 'status', 'updated_at', 'n8n_enabled')}
    return {'owner_user_id': actor['user_id'], 'stage': 'new'}


def tool_instructions():
    schemas = [Read.model_json_schema()] + [schema.model_json_schema() for schema in WRITES.values()]
    import json
    return json.dumps(schemas, ensure_ascii=False)


def require_dispatch_allowed(workflow_id):
    import os
    from integration_config import load_integration_settings
    allowed = {value.strip() for value in os.environ.get('ABAP_ASSISTANT_N8N_WORKFLOWS', '').split(',') if value.strip()}
    if workflow_id not in allowed or not load_integration_settings()['enabled']:
        raise PermissionError('Workflow is not approved for assistant dispatch.')
