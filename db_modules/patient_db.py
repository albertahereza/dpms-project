"""
patient_db.py - database functions for the PATIENT table (Member 3).
"""
from core.db import fetch_all, fetch_one, execute, execute_returning
from core.helpers import require, blank_to_none


def add_patient(name, date_of_birth, gender=None, phone_number=None):
    """Register a patient. date_of_birth is 'YYYY-MM-DD'. Returns the new patient_id."""
    row = execute_returning(
        "INSERT INTO patient (name, date_of_birth, gender, phone_number) "
        "VALUES (%s, %s, %s, %s) RETURNING patient_id",
        (require(name, "Name"), require(date_of_birth, "Date of birth"),
         blank_to_none(gender), blank_to_none(phone_number)))
    return row["patient_id"]


def get_patient(patient_id):
    return fetch_one("SELECT * FROM patient WHERE patient_id = %s", (patient_id,))


def list_patients():
    return fetch_all("SELECT * FROM patient ORDER BY patient_id")


def search_patients(text):
    """Find patients whose name or phone number contains the text (ignores upper/lower case)."""
    pattern = "%" + text.strip() + "%"
    return fetch_all(
        "SELECT * FROM patient WHERE name ILIKE %s OR phone_number LIKE %s ORDER BY name",
        (pattern, pattern))


def update_patient(patient_id, name, date_of_birth, gender=None, phone_number=None):
    """Returns the number of rows changed (0 means no such patient)."""
    return execute(
        "UPDATE patient SET name = %s, date_of_birth = %s, gender = %s, phone_number = %s "
        "WHERE patient_id = %s",
        (require(name, "Name"), require(date_of_birth, "Date of birth"),
         blank_to_none(gender), blank_to_none(phone_number), patient_id))


def delete_patient(patient_id):
    """Blocked by the database if the patient has appointments, records or payments."""
    return execute("DELETE FROM patient WHERE patient_id = %s", (patient_id,))