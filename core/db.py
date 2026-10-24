"""
db.py - the ONE shared database connection module for DPMS (Group 7).

Every other file imports from here:
    from core.db import fetch_all, fetch_one, execute, execute_returning, explain_error
Nobody writes their own connection code.
"""
from contextlib import contextmanager

import psycopg2
from psycopg2 import errors
from psycopg2.extras import RealDictCursor

from core.config import DB_CONFIG


def get_connection():
    """Open a new connection to dpms_db (gives up after 5 seconds)."""
    return psycopg2.connect(connect_timeout=5, **DB_CONFIG)


@contextmanager
def get_cursor(commit=False):
    """
    Open a connection and a cursor, hand the cursor over, then tidy up.
      commit=False -> for reading (SELECT)
      commit=True  -> for writing (INSERT/UPDATE/DELETE): saved when the block succeeds
    If anything fails, the changes are rolled back and the error is re-raised.
    The connection is always closed at the end.
    Rows come back as dictionaries, e.g. row["name"].
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(sql, params=None):
    """Run a SELECT and return a list of rows (each row is a dictionary)."""
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(sql, params=None):
    """Run a SELECT and return the first row (a dictionary), or None."""
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE and save it. Returns the number of rows changed."""
    with get_cursor(commit=True) as cur:
        cur.execute(sql, params)
        return cur.rowcount


def execute_returning(sql, params=None):
    """Run an INSERT/UPDATE ... RETURNING ..., save it, and return the returned row."""
    with get_cursor(commit=True) as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def explain_error(exc):
    """
    Turn a database error into a short message that is safe to show a user
    in a form or message box (used by the screens in Steps 10-11).
    """
    if isinstance(exc, errors.RaiseException):          # our triggers (RAISE EXCEPTION)
        return exc.diag.message_primary
    if isinstance(exc, errors.UniqueViolation):
        return "That value already exists (it must be unique)."
    if isinstance(exc, errors.ForeignKeyViolation):
        return "This record is linked to other records, or refers to one that does not exist."
    if isinstance(exc, errors.CheckViolation):
        return "One of the values is not allowed."
    if isinstance(exc, (errors.InvalidDatetimeFormat, errors.DatetimeFieldOverflow)):
        return "A date or time is in the wrong format. Use YYYY-MM-DD for dates and HH:MM for times."
    if isinstance(exc, errors.InvalidTextRepresentation):
        return "A value has the wrong format (for example letters where a number is needed)."
    if isinstance(exc, errors.NotNullViolation):
        return "A required field was left empty."
    if isinstance(exc, psycopg2.OperationalError):
        return "Cannot reach the database. Check that PostgreSQL is running and the settings are right."
    return "Database error: " + str(exc).strip().splitlines()[0]