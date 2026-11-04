"""Atomic confirmation, domain writes, execution outbox and durable result."""
from assistant_tools import validate_action, action_review, execute_action
from business_transaction import business_transaction

def confirm_action(store, actor, identity):
    from assistant_demo import demo_only
    if demo_only():
        from assistant_demo import confirm_demo
        return confirm_demo(store, actor, identity)
    with business_transaction(store.database_file):
        proposal = store.claim(actor, identity, True)
        if proposal.get('demo_only') is True:
            raise PermissionError('Demo actions cannot execute against business services.')
        values = validate_action(actor, proposal['arguments'], store.database_file)
        if action_review(actor, values, store.database_file) != proposal['review']:
            raise ValueError('Record changed after review.')
        result = execute_action(actor, values, store.database_file)
        if not result:
            raise ValueError('Domain operation failed.')
        store.finish(actor, identity, 'completed')
        store.add(actor, 'chat', {'question': '', 'answer': f'Action completed: {result}',
            'model': 'ABAP service', 'language': '', 'tool_result': None})
        return result
