"""Private history, expiring immutable proposals and durable call reservations."""

import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from assistant_cloud_config import limit as configured_limit

from database import get_database_connection


class AssistantStore:
    def __init__(self, database_file):
        self.database_file = database_file
        # SQLite local/test equivalent of migration 014. PostgreSQL uses deployment migrations.
        connection = get_database_connection(database_file)
        try:
            if isinstance(connection, sqlite3.Connection):
                schema = (Path(__file__).parent /
                          'migrations/postgresql/014_advanced_assistant.sql').read_text(encoding='utf-8')
                connection.executescript(schema)
                connection.executescript((Path(__file__).parent / 'migrations/postgresql/015_assistant_cloud_controls.sql').read_text(encoding='utf-8'))
                connection.executescript((Path(__file__).parent / 'migrations/postgresql/016_assistant_demo_leads.sql').read_text(encoding='utf-8'))
                connection.commit()
        finally:
            connection.close()

    def _connect(self):
        connection = get_database_connection(self.database_file)
        connection.row_factory = sqlite3.Row
        return connection

    def purge(self):
        now = int(time.time())
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
        connection = self._connect()
        try:
            connection.execute('DELETE FROM assistant_entries WHERE expires_at <= ?', (now,))
            connection.execute('DELETE FROM assistant_budgets WHERE day < ?', (cutoff,))
            connection.commit()
        finally:
            connection.close()

    def add(self, actor, kind, payload, ttl=604800):
        identity = str(uuid4())
        now = int(time.time())
        connection = self._connect()
        try:
            connection.execute('''INSERT INTO assistant_entries
                (entry_id,user_id,session_version,kind,payload,state,created_at,expires_at)
                VALUES (?,?,?,?,?,'pending',?,?)''',
                (identity, actor['user_id'], actor['session_version'], kind,
                 json.dumps(payload, ensure_ascii=False), now, now + ttl))
            if payload.get('demo_only') is True:
                connection.execute('INSERT INTO assistant_demo_entries(entry_id) VALUES(?)',(identity,))
            connection.commit()
            return identity
        finally:
            connection.close()

    def entries(self, actor, demo=False):
        connection = self._connect()
        try:
            rows = connection.execute('''SELECT * FROM assistant_entries
                WHERE user_id=? AND session_version=? AND expires_at>?
                AND kind IN ('chat','action') ''' +
                ("AND EXISTS (SELECT 1 FROM assistant_demo_entries d WHERE d.entry_id=assistant_entries.entry_id) " if demo else "") +
                'ORDER BY created_at DESC, entry_id DESC LIMIT 30',
                (actor['user_id'], actor['session_version'], int(time.time()))).fetchall()
            return [{**dict(row), 'payload': json.loads(row['payload'])} for row in reversed(rows)]
        finally:
            connection.close()

    def claim(self, actor, identity, execute):
        """Claim once; join the caller business transaction when one is active."""
        connection = self._connect()
        try:
            row = connection.execute('''UPDATE assistant_entries SET state=?
                WHERE entry_id=? AND user_id=? AND session_version=? AND kind='action'
                AND state='pending' AND expires_at>? RETURNING payload''',
                ('claimed' if execute else 'cancelled', identity, actor['user_id'],
                 actor['session_version'], int(time.time()))).fetchone()
            connection.commit()
            if row is None:
                raise ValueError('Action expired or already handled.')
            return json.loads(row['payload'])
        finally:
            connection.close()

    def finish(self, actor, identity, state):
        connection = self._connect()
        try:
            connection.execute('''UPDATE assistant_entries SET state=? WHERE entry_id=?
                AND user_id=? AND state='claimed' ''', (state, identity, actor['user_id']))
            connection.commit()
        finally:
            connection.close()

    def clear(self, actor, demo=False):
        connection = self._connect()
        try:
            if demo:
                rows = connection.execute("SELECT entry_id FROM assistant_entries WHERE user_id=? AND kind IN ('chat','action') AND EXISTS (SELECT 1 FROM assistant_demo_entries d WHERE d.entry_id=assistant_entries.entry_id)", (actor['user_id'],)).fetchall()
                for row in rows:
                    connection.execute('DELETE FROM assistant_entries WHERE entry_id=? AND user_id=?', (row['entry_id'],actor['user_id']))
                connection.commit()
                return
            connection.execute("DELETE FROM assistant_entries WHERE user_id=? AND kind='chat'", (actor['user_id'],))
            connection.execute("UPDATE assistant_entries SET state='cancelled' WHERE user_id=? AND kind='action' AND state='pending'", (actor['user_id'],))
            connection.commit()
        finally:
            connection.close()

    def reserve(self, actor, user_limit=None, global_limit=None, model_id=None, provider=None, connection=None):
        from assistant_cloud_config import limit as configured_limit, AssistantLimitError
        user_limit = user_limit if user_limit is not None else configured_limit('USER_DAILY_LIMIT', 100)
        global_limit = global_limit if global_limit is not None else configured_limit('GLOBAL_DAILY_LIMIT', 1000)
        day = datetime.now(timezone.utc).date().isoformat()
        owned = connection is None
        connection = connection or self._connect()
        scopes = [(f"user:{actor['user_id']}", user_limit), ('global', global_limit)]
        if model_id and provider:
            scopes += [('model:'+model_id, configured_limit('MODEL_DAILY_LIMIT',40)),
                       ('provider:'+provider, configured_limit('PROVIDER_DAILY_LIMIT',40)),
                       (f"user-model:{actor['user_id']}:{model_id}", configured_limit('USER_MODEL_DAILY_LIMIT',20))]
        scopes = [(scope, day, maximum) for scope, maximum in scopes]
        if model_id and provider:
            minute = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M')
            scopes += [('minute-user:'+str(actor['user_id']),minute,configured_limit('USER_PER_MINUTE',10)),
                       ('minute-model:'+model_id,minute,configured_limit('MODEL_PER_MINUTE',20)),
                       ('minute-provider:'+provider,minute,configured_limit('PROVIDER_PER_MINUTE',20)),
                       ('minute-global',minute,configured_limit('GLOBAL_PER_MINUTE',60))]
        try:
            for scope, window, limit in scopes:
                row = connection.execute('''INSERT INTO assistant_budgets(scope,day,used) VALUES(?,?,1)
                    ON CONFLICT(scope,day) DO UPDATE SET used=assistant_budgets.used+1
                    WHERE assistant_budgets.used < ? RETURNING used''', (scope, window, limit)).fetchone()
                if row is None:
                    connection.rollback()
                    raise AssistantLimitError('ABAP request budget reached. Provider quotas are separate; select another eligible model if its budget permits.')
            if owned:
                connection.commit()
        finally:
            if owned:
                connection.close()

    def usage_summary(self, actor):
        connection = self._connect()
        try:
            day = datetime.now(timezone.utc).date().isoformat()
            row = connection.execute('SELECT used FROM assistant_budgets WHERE scope=? AND day=?',
                                     (f"user:{actor['user_id']}", day)).fetchone()
            return {'day_utc': day, 'model_calls': row['used'] if row else 0, 'limit': configured_limit('USER_DAILY_LIMIT', 100)}
        finally:
            connection.close()


    def unavailable(self, model_id, provider):
        connection = self._connect()
        try:
            return connection.execute('SELECT reason FROM assistant_cloud_status WHERE scope IN (?,?) AND unavailable_until>?',
                ('model:'+model_id,'provider:'+provider,int(time.time()))).fetchone() is not None
        finally:
            connection.close()

    def mark_unavailable(self, model_id, provider, provider_wide=False, duration=60):
        connection = self._connect()
        try:
            scope = 'provider:'+provider if provider_wide else 'model:'+model_id
            connection.execute('''INSERT INTO assistant_cloud_status(scope,unavailable_until,reason) VALUES(?,?,?)
                ON CONFLICT(scope) DO UPDATE SET unavailable_until=excluded.unavailable_until,reason=excluded.reason''',
                (scope,int(time.time())+duration,'Provider quota or availability failure; retry after cooldown.'))
            connection.commit()
        finally:
            connection.close()

    def acquire_cloud(self, actor, model_id, provider):
        from assistant_cloud_config import limit, AssistantLimitError
        connection = self._connect()
        identity = str(uuid4())
        try:
            if isinstance(connection, sqlite3.Connection):
                connection.execute('BEGIN IMMEDIATE')
            else:
                connection.execute("SET LOCAL lock_timeout = '5s'")
            # One cross-process mutex protects all counters and lease counts together.
            connection.execute('UPDATE assistant_cloud_control SET control_id=control_id WHERE control_id=1')
            connection.execute('DELETE FROM assistant_cloud_leases WHERE expires_at<=?',(int(time.time()),))
            checks = [('1=1',(),limit('GLOBAL_CONCURRENCY',4)),
                      ('provider=?',(provider,),limit('PROVIDER_CONCURRENCY',2)),
                      ('model_id=?',(model_id,),limit('MODEL_CONCURRENCY',2)),
                      ('user_id=?',(actor['user_id'],),limit('USER_CONCURRENCY',1))]
            for where,parameters,maximum in checks:
                count=connection.execute('SELECT COUNT(*) AS n FROM assistant_cloud_leases WHERE '+where,parameters).fetchone()['n']
                if count>=maximum:
                    raise AssistantLimitError('ABAP concurrency limit reached. Try again shortly.')
            if self.unavailable(model_id,provider):
                raise AssistantLimitError('Provider quota or model cooldown active. Select another eligible cloud model.')
            self.reserve(actor,model_id=model_id,provider=provider,connection=connection)
            connection.execute('INSERT INTO assistant_cloud_leases(lease_id,user_id,model_id,provider,expires_at) VALUES(?,?,?,?,?)',
                (identity,actor['user_id'],model_id,provider,int(time.time())+300))
            connection.commit()
            return identity
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def release_cloud(self, identity):
        connection=self._connect()
        try:
            connection.execute('DELETE FROM assistant_cloud_leases WHERE lease_id=?',(identity,))
            connection.commit()
        finally:
            connection.close()
