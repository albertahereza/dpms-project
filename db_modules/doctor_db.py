"""
doctor_db.py - database functions for the DOCTOR table (Member 2).
"""
from core.db import fetch_all, fetch_one, execute, execute_returning
from core.helpers import require


def add_doctor(user_id, name, specialty):
    """Create a doctor profile for an existing login account. Returns the new doctor_id."""
    row = execute_returning(
        "INSERT INTO doctor (user_id, name, specialty) VALUES (%s, %s, %s) RETURNING doctor_id",
        (require(user_id, "User"), require(name, "Name"), require(specialty, "Specialty")))
    return row["doctor_id"]


def get_doctor(doctor_id):
    return fetch_one("SELECT doctor_id, user_id, name, specialty FROM doctor WHERE doctor_id = %s",
                     (doctor_id,))


def get_doctor_by_user(user_id):
    """Find the doctor profile of a logged-in user (None if the user is not a doctor)."""
    return fetch_one("SELECT doctor_id, user_id, name, specialty FROM doctor WHERE user_id = %s",
                     (user_id,))


def list_doctors():
    """All doctors with their login names."""
    return fetch_all(
        "SELECT d.doctor_id, d.name, d.specialty, d.user_id, u.username "
        "FROM doctor d JOIN users u ON u.user_id = d.user_id "
        "ORDER BY d.doctor_id")


def update_doctor(doctor_id, name, specialty):
    return execute("UPDATE doctor SET name = %s, specialty = %s WHERE doctor_id = %s",
                   (require(name, "Name"), require(specialty, "Specialty"), doctor_id))


def delete_doctor(doctor_id):
    """Blocked by the database if the doctor has appointments or records."""
    return execute("DELETE FROM doctor WHERE doctor_id = %s", (doctor_id,))