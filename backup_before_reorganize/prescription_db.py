"""
prescription_db.py - database functions for the PRESCRIPTION table (Member 4).
"""
from db import fetch_all, fetch_one, execute, execute_returning
from helpers import require


def add_prescription(medical_record_id, prescription):
    """Add a prescription to a medical record. Returns the new prescription_id."""
    row = execute_returning(
        "INSERT INTO prescription (medical_record_id, prescription) "
        "VALUES (%s, %s) RETURNING prescription_id",
        (require(medical_record_id, "Medical record"), require(prescription, "Prescription")))
    return row["prescription_id"]


def get_prescription(prescription_id):
    return fetch_one("SELECT * FROM prescription WHERE prescription_id = %s", (prescription_id,))


def list_prescriptions():
    """All prescriptions with the patient and diagnosis (for the Prescriptions screen)."""
    return fetch_all(
        "SELECT pr.prescription_id, pr.medical_record_id, p.name AS patient, "
        "       mr.diagnosis, pr.prescription "
        "FROM prescription pr "
        "JOIN medical_record mr ON mr.medical_record_id = pr.medical_record_id "
        "JOIN patient        p  ON p.patient_id         = mr.patient_id "
        "ORDER BY pr.prescription_id")


def list_prescriptions_for_record(medical_record_id):
    return fetch_all(
        "SELECT prescription_id, medical_record_id, prescription "
        "FROM prescription WHERE medical_record_id = %s ORDER BY prescription_id",
        (medical_record_id,))


def list_prescriptions_for_patient(patient_id):
    """Every prescription a patient has ever received (joins through the medical record)."""
    return fetch_all(
        "SELECT pr.prescription_id, pr.medical_record_id, mr.diagnosis, pr.prescription "
        "FROM prescription pr "
        "JOIN medical_record mr ON mr.medical_record_id = pr.medical_record_id "
        "WHERE mr.patient_id = %s ORDER BY pr.prescription_id",
        (patient_id,))


def update_prescription(prescription_id, prescription):
    return execute("UPDATE prescription SET prescription = %s WHERE prescription_id = %s",
                   (require(prescription, "Prescription"), prescription_id))


def delete_prescription(prescription_id):
    return execute("DELETE FROM prescription WHERE prescription_id = %s", (prescription_id,))