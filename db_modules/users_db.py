"""
users_db.py - database functions for the USERS table (Member 2).
Passwords are hashed by PostgreSQL (pgcrypto, bcrypt). They are never stored or returned as text.
"""
from core.db import fetch_all, fetch_one, execute, execute_returning
from core.helpers import require

ROLES = ("Admin", "Doctor", "Receptionist")


def add_user(username, password, role):
    """Create a login account. Returns the new user_id."""
    username = require(username, "Username")
    role = require(role, "Role")
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    row = execute_returning(
        "INSERT INTO users (username, password, role) "
        "VALUES (%s, crypt(%s, gen_salt('bf')), %s) RETURNING user_id",
        (username, password, role))
    return row["user_id"]


def verify_login(username, password):
    """
    Check a username and password (used by the login screen in Step 12).
    Returns {user_id, username, role} when correct, otherwise None.
    crypt(typed_password, stored_hash) gives the stored hash back only when the password is right.
    """
    return fetch_one(
        "SELECT user_id, username, role FROM users "
        "WHERE username = %s AND password = crypt(%s, password)",
        (username, password))


def get_user(user_id):
    return fetch_one("SELECT user_id, username, role FROM users WHERE user_id = %s", (user_id,))


def list_users():
    return fetch_all("SELECT user_id, username, role FROM users ORDER BY user_id")


def update_user_role(user_id, role):
    """Returns the number of rows changed (0 means no such user)."""
    return execute("UPDATE users SET role = %s WHERE user_id = %s",
                   (require(role, "Role"), user_id))


def change_password(user_id, new_password):
    if not new_password or len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    return execute("UPDATE users SET password = crypt(%s, gen_salt('bf')) WHERE user_id = %s",
                   (new_password, user_id))


def delete_user(user_id):
    """Blocked by the database if the user is linked to a doctor."""
    return execute("DELETE FROM users WHERE user_id = %s", (user_id,))