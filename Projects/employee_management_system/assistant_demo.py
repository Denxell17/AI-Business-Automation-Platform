"""Synthetic-only release boundary. No arbitrary text, URLs or live business data."""
import copy
import os


def demo_only():
    default = 'true' if os.environ.get('ABAP_ENVIRONMENT') == 'production' else 'false'
    return os.environ.get('ABAP_ASSISTANT_DEMO_ONLY', default).strip().lower() != 'false'


QUESTIONS = (
    'Explain the ABAP platform using public information only.',
    'Summarize the synthetic leads demonstration.',
    'Summarize the synthetic invoices demonstration.',
    'Summarize the synthetic workflows demonstration.',
    '公開情報だけでABAPプラットフォームを説明してください。',
    '架空の見込み客デモを要約してください。',
    '架空の請求書デモを要約してください。',
    '架空のワークフローデモを要約してください。',
    'Prepare a synthetic demo lead for confirmation.',
    '承認用の架空のデモ見込み客を準備してください。',
)
ACTION_QUESTIONS = QUESTIONS[-2:]
ACTION = {'tool':'create_lead','name':'Synthetic Demo Lead','company':'Fictional Company'}

_FIXTURES = {
    'leads': [{'lead_id':'DEMO-LEAD-1','name':'Synthetic Lead Alpha','company':'Fictional Company','stage':'qualified'}],
    'customers': [{'customer_id':'DEMO-CUSTOMER-1','name':'Synthetic Customer Alpha','status':'active'}],
    'invoices': [{'invoice_id':'DEMO-INVOICE-1','invoice_number':'DEMO-001','currency':'USD','total_cents':10000,'status':'draft'}],
    'employees': [{'employee_id':'DEMO-EMPLOYEE-1','name':'Synthetic Employee Alpha','department':'Demo Department'}],
    'workflows': [{'workflow_id':'DEMO-WORKFLOW-1','name':'Synthetic Workflow','status':'active','executions':[]}],
    'activity': [],
}


def synthetic_result(arguments, actor, database_file):
    from assistant_tools import Read
    name = Read.model_validate(arguments).tool
    records=copy.deepcopy(_FIXTURES[name])
    if name=='leads':
        from database import get_database_connection
        import sqlite3
        connection=get_database_connection(database_file)
        connection.row_factory=sqlite3.Row
        try:
            records += [dict(r) for r in connection.execute('SELECT lead_id,name,company,stage FROM assistant_demo_leads WHERE user_id=? ORDER BY created_at DESC LIMIT 20',(actor['user_id'],)).fetchall()]
        finally:
            connection.close()
    return {'tool':name, 'scope':'SYNTHETIC DEMONSTRATION ONLY. No real business records.', 'records':records}


def visible_entries(entries):
    return [row for row in entries if row['payload'].get('demo_only') is True]


def confirm_demo(store, actor, identity):
    from assistant_tools import actor_now
    from business_transaction import business_transaction
    from database import get_database_connection
    from uuid import uuid4
    import time
    with business_transaction(store.database_file, demo=True):
        actor=actor_now(actor,store.database_file)
        proposal=store.claim(actor,identity,True)
        if proposal.get('demo_only') is not True or proposal.get('arguments') != ACTION:
            raise PermissionError('Only the fixed isolated demo action is permitted.')
        connection=get_database_connection(store.database_file)
        count=connection.execute('SELECT COUNT(*) AS n FROM assistant_demo_leads WHERE user_id=?',(actor['user_id'],)).fetchone()['n']
        if count>=20:
            raise ValueError('Demo record limit reached.')
        result='DEMO-'+uuid4().hex
        connection.execute('INSERT INTO assistant_demo_leads(lead_id,user_id,name,company,stage,created_at) VALUES(?,?,?,?,?,?)',
            (result,actor['user_id'],'Synthetic Demo Lead','Fictional Company','new',int(time.time())))
        store.finish(actor,identity,'completed')
        store.add(actor,'chat',{'question':'','answer':'Synthetic demo lead created: '+result,
            'model':'ABAP demo service','language':'en','tool_result':None,'demo_only':True})
        return result
