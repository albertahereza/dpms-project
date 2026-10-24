"""
config.py - database connection settings for DPMS (Group 7).

Every member sets their OWN password on their own machine.
Option 1: edit the "CHANGE_ME" fallback below (do not share your edited copy).
Option 2: set an environment variable named DPMS_DB_PASSWORD (preferred).
"""
import os

try:
    from core.config_local import DB_CONFIG
except ImportError:

  DB_CONFIG = {
    "host":     os.getenv("DPMS_DB_HOST", "localhost"),
    "port":     int(os.getenv("DPMS_DB_PORT", "5432")),   # pgAdmin > server Properties > Connection
    "dbname":   os.getenv("DPMS_DB_NAME", "dpms_db"),
    "user":     os.getenv("DPMS_DB_USER", "postgres"),
    "password": os.getenv("DPMS_DB_PASSWORD", "database"),
}