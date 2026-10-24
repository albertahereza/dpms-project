"""
helpers.py - tiny shared helpers for the database modules (Group 7).
"""


def require(value, label):
    """Make sure a required value was given. Returns it (trimmed if it is text)."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise ValueError(f"{label} is required.")
    return value.strip() if isinstance(value, str) else value


def blank_to_none(value):
    """Forms send empty text for 'nothing entered'. The database wants NULL (None)."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value