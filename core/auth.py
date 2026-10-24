"""
auth.py - authentication and role permissions for DPMS (Member 2).

Authentication = proving WHO you are (username + password).
Authorisation  = deciding WHAT you may open (the role -> screens table below).
"""
from db_modules import users_db

# Which screens each role may open (the keys match NAV in main.py).
ROLE_SCREENS = {
    "Admin": ("home", "patients", "appointments", "records", "prescriptions",
              "payments", "doctors", "users", "reports"),
    "Doctor": ("home", "patients", "appointments", "records", "prescriptions", "reports"),
    "Receptionist": ("home", "patients", "appointments", "payments", "reports"),
}


def can_open(role, screen_key):
    """True when a user with this role may open this screen."""
    return screen_key in ROLE_SCREENS.get(role, ())


def authenticate(username, password):
    """
    Check a login. Returns {user_id, username, role} when correct, or None when the
    username or password is wrong. Raises ValueError if a box was left empty.
    The password is compared inside PostgreSQL against the stored bcrypt hash.
    """
    username = (username or "").strip()
    if not username or not password:
        raise ValueError("Enter your username and your password.")
    return users_db.verify_login(username, password)