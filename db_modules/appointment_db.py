"""
appointment_db.py - database functions for the APPOINTMENT table (Member 3).
The Step 7 triggers refuse double bookings and illegal status changes.
"""
from core.db import fetch_all, fetch_one, execute, execute_returning
from core.helpers import require

# Every list below shows patient and doctor NAMES, not just ID numbers (a JOIN).
_BASE = (
    "SELECT a.appointment_id, a.patient_id, p.name AS patient, "
    "       a.doctor_id, d.name AS doctor, "
    "       a.appointment_date, a.appointment_time, a.appointment_status "
    "FROM appointment a "
    "JOIN patient p ON p.patient_id = a.patient_id "
    "JOIN doctor  d ON d.doctor_id  = a.doctor_id "
)
_ORDER = "ORDER BY a.appointment_date, a.appointment_time"


def book_appointment(patient_id, doctor_id, appointment_date, appointment_time):
    """
    Book an appointment ('YYYY-MM-DD' and 'HH:MM'). The status becomes 'Scheduled' by DEFAULT.
    Returns the new appointment_id.
    """
    row = execute_returning(
        "INSERT INTO appointment (patient_id, doctor_id, appointment_date, appointment_time) "
        "VALUES (%s, %s, %s, %s) RETURNING appointment_id",
        (require(patient_id, "Patient"), require(doctor_id, "Doctor"),
         require(appointment_date, "Date"), require(appointment_time, "Time")))
    return row["appointment_id"]


def get_appointment(appointment_id):
    return fetch_one(_BASE + "WHERE a.appointment_id = %s", (appointment_id,))


def list_appointments():
    return fetch_all(_BASE + _ORDER)


def list_appointments_for_patient(patient_id):
    return fetch_all(_BASE + "WHERE a.patient_id = %s " + _ORDER, (patient_id,))


def list_appointments_for_doctor(doctor_id):
    return fetch_all(_BASE + "WHERE a.doctor_id = %s " + _ORDER, (doctor_id,))


def list_appointments_by_status(status):
    return fetch_all(_BASE + "WHERE a.appointment_status = %s " + _ORDER, (status,))


def list_appointments_without_record():
    """Appointments that are not cancelled and have no medical record yet (for the records form)."""
    return fetch_all(
        _BASE + "WHERE a.appointment_status <> 'Cancelled' "
                "AND NOT EXISTS (SELECT 1 FROM medical_record mr "
                "                WHERE mr.appointment_id = a.appointment_id) " + _ORDER)


def update_appointment_status(appointment_id, status):
    """Set 'Scheduled', 'Completed' or 'Cancelled'. Returns rows changed."""
    return execute("UPDATE appointment SET appointment_status = %s WHERE appointment_id = %s",
                   (require(status, "Status"), appointment_id))


def cancel_appointment(appointment_id):
    return update_appointment_status(appointment_id, "Cancelled")


def reschedule_appointment(appointment_id, new_date, new_time):
    return execute(
        "UPDATE appointment SET appointment_date = %s, appointment_time = %s "
        "WHERE appointment_id = %s",
        (require(new_date, "Date"), require(new_time, "Time"), appointment_id))


def delete_appointment(appointment_id):
    """Blocked by the database if a medical record exists for it."""
    return execute("DELETE FROM appointment WHERE appointment_id = %s", (appointment_id,))