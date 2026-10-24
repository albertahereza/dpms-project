"""
medical_record_db.py - database functions for the MEDICAL_RECORD table (Member 4).
"""
from db import fetch_all, fetch_one, execute, execute_returning
from helpers import require, blank_to_none

_BASE = (
    "SELECT mr.medical_record_id, mr.appointment_id, a.appointment_date, "
    "       mr.patient_id, p.name AS patient, mr.doctor_id, d.name AS doctor, "
    "       mr.medical_history, mr.diagnosis "
    "FROM medical_record mr "
    "JOIN appointment a ON a.appointment_id = mr.appointment_id "
    "JOIN patient     p ON p.patient_id     = mr.patient_id "
    "JOIN doctor      d ON d.doctor_id      = mr.doctor_id "
)


def add_record(appointment_id, doctor_id, medical_history=None, diagnosis=None):
    """
    Write a medical record for an appointment. Returns the new medical_record_id.
    The patient is copied from the appointment automatically, so the form never
    asks for it and the two can never disagree (the Step 7 trigger double-checks).
    """
    row = execute_returning(
        "INSERT INTO medical_record "
        "       (appointment_id, patient_id, doctor_id, medical_history, diagnosis) "
        "SELECT a.appointment_id, a.patient_id, %s, %s, %s "
        "FROM appointment a WHERE a.appointment_id = %s "
        "RETURNING medical_record_id",
        (require(doctor_id, "Doctor"), blank_to_none(medical_history),
         blank_to_none(diagnosis), require(appointment_id, "Appointment")))
    if row is None:
        raise ValueError("That appointment does not exist.")
    return row["medical_record_id"]


def get_record(medical_record_id):
    return fetch_one(_BASE + "WHERE mr.medical_record_id = %s", (medical_record_id,))


def list_records():
    return fetch_all(_BASE + "ORDER BY mr.medical_record_id")


def list_records_for_patient(patient_id):
    return fetch_all(_BASE + "WHERE mr.patient_id = %s ORDER BY a.appointment_date",
                     (patient_id,))


def update_record(medical_record_id, medical_history, diagnosis):
    return execute(
        "UPDATE medical_record SET medical_history = %s, diagnosis = %s "
        "WHERE medical_record_id = %s",
        (blank_to_none(medical_history), blank_to_none(diagnosis), medical_record_id))


def delete_record(medical_record_id):
    """Blocked by the database if prescriptions still belong to it."""
    return execute("DELETE FROM medical_record WHERE medical_record_id = %s",
                   (medical_record_id,))