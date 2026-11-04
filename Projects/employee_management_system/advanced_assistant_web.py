"""Opt-in authenticated advanced assistant, separate from public RAG routes."""

import os
import sqlite3
from typing import Annotated

import psycopg
from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from agent_provider import AgentProviderError
from assistant_gateway import Gateway
from assistant_cloud_config import AssistantLimitError
from assistant_demo import demo_only, QUESTIONS, visible_entries
from assistant_store import AssistantStore
from assistant_tools import actor_now, validate_action, action_review, execute_action
from advanced_assistant import converse
from web_session import load_authenticated_session_user


def advanced_enabled():
    return os.environ.get('ABAP_ADVANCED_ASSISTANT_ENABLED', 'false') == 'true'


class AdvancedAssistantRequestLimit:
    """Bound form bodies before parsing, including chunked requests."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (scope['type'] != 'http' or scope.get('method') != 'POST'
                or not scope.get('path', '').startswith('/ai-assistant/advanced')):
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            event = await receive()
            if event['type'] == 'http.disconnect':
                return
            body.extend(event.get('body', b''))
            if len(body) > 65536:
                return await HTMLResponse('Request too large.', status_code=413)(scope, receive, send)
            if not event.get('more_body', False):
                break
        delivered = False
        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
            return await receive()
        await self.app(scope, bounded_receive, send)


def register_advanced_assistant_routes(app, templates, database_file, csrf_for, csrf_valid,
                                      limiter, log_activity, gateway_factory=Gateway):
    app.add_middleware(AdvancedAssistantRequestLimit)
    def access(request, token=None):
        if not advanced_enabled():
            return None, HTMLResponse('Not found.', status_code=404)
        actor = load_authenticated_session_user(request, database_file)
        if actor is None:
            return None, RedirectResponse(request.url_for('login_page'), status_code=303)
        try:
            actor = actor_now(actor, database_file)
        except PermissionError:
            return None, HTMLResponse('Access denied.', status_code=403)
        if token is not None and not csrf_valid(request, token):
            return None, HTMLResponse('Your form could not be verified.', status_code=403)
        return actor, None

    def page(request, actor, error=None, status=200):
        store = AssistantStore(database_file)
        store.purge()
        try:
            models = [model.public() for model in gateway_factory().models]
            for model in models:
                if store.unavailable(model['id'],model['provider']):
                    model.update(available=False,status='Provider quota or availability cooldown')
        except ValueError:
            models = []
            error = 'Assistant model configuration is unavailable.'
        entries = store.entries(actor, demo=demo_only())
        if demo_only():
            entries = visible_entries(entries)
        previous = next((entry['payload'] for entry in reversed(entries)
                         if entry['kind'] == 'chat' and entry['payload'].get('model') != 'ABAP service'), {})
        response = templates.TemplateResponse(request=request, name='advanced_assistant.html',
            context={'page_title': 'AI Assistant', 'active_page': 'ai_assistant',
                'current_user': actor, 'csrf_token': csrf_for(request),
                'entries': entries, 'models': models, 'error': error,
                'demo_only': demo_only(), 'demo_questions': QUESTIONS,
                'selected_model': previous.get('model'),
                'usage_summary': store.usage_summary(actor),
                'response_language': previous.get('language', actor.get('interface_language', 'en'))}, status_code=status)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/ai-assistant/advanced', response_class=HTMLResponse)
    def advanced_assistant_page(request: Request):
        actor, denied = access(request)
        if denied is not None:
            return denied
        return page(request, actor)

    @app.post('/ai-assistant/advanced')
    def advanced_assistant_ask(request: Request, csrf_token: Annotated[str, Form()],
            question: Annotated[str, Form()] = '', model_id: Annotated[str, Form()] = '',
            response_language: Annotated[str, Form()] = 'en',
            share_data: Annotated[str, Form()] = ''):
        actor, denied = access(request, csrf_token)
        if denied is not None:
            return denied
        limit = limiter.acquire(actor['user_id'])
        if not limit.allowed:
            response = page(request, actor, 'Too many requests. Try again shortly.', 429)
            response.headers['Retry-After'] = str(limit.retry_after)
            return response
        try:
            converse(actor, question, model_id, response_language, share_data == 'yes',
                database_file, AssistantStore(database_file), gateway_factory())
            log_activity(f"Advanced assistant request completed for user {actor['user_id']}.")
        except AssistantLimitError as error:
            return page(request, actor, str(error), 429)
        except AgentProviderError:
            return page(request, actor, 'Model unavailable or quota exhausted. Select another configured model.', 502)
        except PermissionError:
            return page(request, actor, 'Requested data or action is not permitted.', 403)
        except ValueError:
            return page(request, actor, 'Invalid request, unavailable model, or daily call limit reached.', 400)
        except (sqlite3.Error, psycopg.Error):
            return HTMLResponse('Assistant storage unavailable.', status_code=503)
        finally:
            limiter.release()
        return RedirectResponse(request.url_for('advanced_assistant_page'), status_code=303)

    @app.post('/ai-assistant/advanced/actions/{identity}')
    def advanced_assistant_confirm(request: Request, identity: str,
            csrf_token: Annotated[str, Form()], decision: Annotated[str, Form()]):
        actor, denied = access(request, csrf_token)
        if denied is not None:
            return denied
        if decision not in ('confirm', 'cancel') or len(identity) > 60:
            return HTMLResponse('Invalid action.', status_code=400)
        store = AssistantStore(database_file)
        try:
            if decision == 'confirm':
                from assistant_confirmation import confirm_action
                confirm_action(store, actor, identity)
                log_activity(f"Advanced assistant action {identity} completed for user {actor['user_id']}.")
            else:
                if demo_only():
                    from business_transaction import business_transaction
                    with business_transaction(database_file,demo=True):
                        proposal=store.claim(actor,identity,False)
                        if proposal.get('demo_only') is not True:
                            raise PermissionError('Non-demo action is unavailable.')
                else:
                    store.claim(actor, identity, False)
        except (ValueError, PermissionError, sqlite3.Error, psycopg.Error):
            return page(request, actor, 'Action expired, already handled, or could not complete. Review business records before proposing again.', 409)
        return RedirectResponse(request.url_for('advanced_assistant_page'), status_code=303)

    @app.post('/ai-assistant/advanced/clear')
    def advanced_assistant_clear(request: Request, csrf_token: Annotated[str, Form()]):
        actor, denied = access(request, csrf_token)
        if denied is not None:
            return denied
        AssistantStore(database_file).clear(actor, demo=demo_only())
        return RedirectResponse(request.url_for('advanced_assistant_page'), status_code=303)
