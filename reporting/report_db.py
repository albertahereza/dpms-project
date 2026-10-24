"""
report_db.py - the SQL behind every report (Member 3 writes the queries, Member 5 uses them).
Each function returns a list of dictionaries and changes nothing in the database.
"""
from core.db import fetch_all


def appointments_per_doctor():
    """Every doctor, including doctors with no appointments (LEFT JOIN)."""
    return fetch_all(
        "SELECT d.name AS doctor, COUNT(a.appointment_id) AS appointments "
        "FROM doctor d LEFT JOIN appointment a ON a.doctor_id = d.doctor_id "
        "GROUP BY d.doctor_id, d.name "
        "ORDER BY appointments DESC, d.name")


def appointments_by_status():
    return fetch_all(
        "SELECT appointment_status AS status, COUNT(*) AS total "
        "FROM appointment GROUP BY appointment_status "
        "ORDER BY total DESC, status")


def revenue_per_month():
    return fetch_all(
        "SELECT TO_CHAR(payment_date, 'YYYY-MM') AS month, "
        "       COUNT(*) AS payments, SUM(amount) AS revenue "
        "FROM payment GROUP BY TO_CHAR(payment_date, 'YYYY-MM') "
        "ORDER BY month")


def revenue_by_method():
    return fetch_all(
        "SELECT payment_method AS method, COUNT(*) AS payments, SUM(amount) AS revenue "
        "FROM payment GROUP BY payment_method "
        "ORDER BY revenue DESC, method")


def top_patients_by_payment(limit=5):
    return fetch_all(
        "SELECT p.name AS patient, COUNT(*) AS payments, SUM(py.amount) AS total_paid "
        "FROM patient p JOIN payment py ON py.patient_id = p.patient_id "
        "GROUP BY p.patient_id, p.name "
        "ORDER BY total_paid DESC, p.name LIMIT %s", (limit,))


def patients_by_gender():
    return fetch_all(
        "SELECT COALESCE(gender, 'Not recorded') AS gender, COUNT(*) AS patients "
        "FROM patient GROUP BY COALESCE(gender, 'Not recorded') "
        "ORDER BY patients DESC, gender")


def top_diagnoses(limit=10):
    return fetch_all(
        "SELECT diagnosis, COUNT(*) AS cases "
        "FROM medical_record WHERE diagnosis IS NOT NULL "
        "GROUP BY diagnosis ORDER BY cases DESC, diagnosis LIMIT %s", (limit,))