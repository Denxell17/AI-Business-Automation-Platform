"""Scoped transaction loans let existing domain services join one unit of work."""
from contextvars import ContextVar
from contextlib import contextmanager
from pathlib import Path
import sqlite3

_active = ContextVar('business_transaction', default=None)

def current_connection(database_file):
    value = _active.get()
    if value is None:
        return None
    path, loan = value
    if Path(database_file).resolve() != path:
        raise ValueError('Cross-database transaction access denied.')
    return loan

class ConnectionLoan:
    def __init__(self, connection):
        self.connection = connection
        self.failed = False
    @property
    def row_factory(self):
        return self.connection.row_factory
    @row_factory.setter
    def row_factory(self, value):
        self.connection.row_factory = value
    def execute(self, sql, parameters=()):
        if sql.strip().upper() in ('BEGIN', 'BEGIN IMMEDIATE'):
            return None
        return self.connection.execute(sql, parameters)
    def executemany(self, sql, parameters):
        return self.connection.executemany(sql, parameters)
    def commit(self):
        pass
    def close(self):
        pass
    def rollback(self):
        self.failed = True

@contextmanager
def business_transaction(database_file, *, demo=False):
    if _active.get() is not None:
        raise RuntimeError('Nested business units of work are unsupported.')
    from database import get_database_connection
    connection = get_database_connection(database_file)
    connection.row_factory = sqlite3.Row
    token = None
    try:
        if isinstance(connection, sqlite3.Connection):
            connection.execute('BEGIN IMMEDIATE')
        else:
            connection.execute("SET LOCAL lock_timeout = '5s'")
            connection.execute("SET LOCAL statement_timeout = '30s'")
            # Conservative serialization also blocks ordinary domain writers during review.
            connection.execute('LOCK TABLE users IN SHARE ROW EXCLUSIVE MODE' if demo else
                               'LOCK TABLE users, leads, customers, invoices, workflows, workflow_tasks IN SHARE ROW EXCLUSIVE MODE')
        loan = ConnectionLoan(connection)
        token = _active.set((Path(database_file).resolve(), loan))
        yield loan
        if loan.failed:
            raise ValueError('A domain operation rolled back.')
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        if token is not None:
            _active.reset(token)
        connection.close()
