"""
payment_db.py - database functions for the PAYMENT table (Member 4).
"""
from decimal import Decimal, InvalidOperation

from core.db import fetch_all, fetch_one, execute, execute_returning
from core.helpers import require, blank_to_none

_BASE = (
    "SELECT pay.payment_id, pay.patient_id, p.name AS patient, pay.service_type, "
    "       pay.amount, pay.payment_method, pay.payment_date "
    "FROM payment pay JOIN patient p ON p.patient_id = pay.patient_id "
)


def _to_amount(value):
    """Turn what the user typed into a Decimal (money is never a float)."""
    try:
        return Decimal(str(require(value, "Amount")).replace(",", ""))
    except InvalidOperation:
        raise ValueError("Amount must be a number.")


def add_payment(patient_id, service_type, amount, payment_method, payment_date=None):
    """
    Record a payment. Leave payment_date empty to use today's date.
    The database refuses an amount of 0 or less and unknown payment methods.
    Returns the new payment_id.
    """
    row = execute_returning(
        "INSERT INTO payment (patient_id, service_type, amount, payment_method, payment_date) "
        "VALUES (%s, %s, %s, %s, COALESCE(%s, CURRENT_DATE)) RETURNING payment_id",
        (require(patient_id, "Patient"), require(service_type, "Service type"),
         _to_amount(amount), require(payment_method, "Payment method"),
         blank_to_none(payment_date)))
    return row["payment_id"]


def get_payment(payment_id):
    return fetch_one(_BASE + "WHERE pay.payment_id = %s", (payment_id,))


def list_payments():
    return fetch_all(_BASE + "ORDER BY pay.payment_date DESC, pay.payment_id DESC")


def list_payments_for_patient(patient_id):
    return fetch_all(_BASE + "WHERE pay.patient_id = %s ORDER BY pay.payment_date, pay.payment_id",
                     (patient_id,))


def total_paid_by_patient(patient_id):
    """Total amount a patient has paid (0 if none)."""
    row = fetch_one("SELECT COALESCE(SUM(amount), 0) AS total FROM payment WHERE patient_id = %s",
                    (patient_id,))
    return row["total"]


def update_payment(payment_id, service_type, amount, payment_method, payment_date):
    return execute(
        "UPDATE payment SET service_type = %s, amount = %s, payment_method = %s, payment_date = %s "
        "WHERE payment_id = %s",
        (require(service_type, "Service type"), _to_amount(amount),
         require(payment_method, "Payment method"), require(payment_date, "Payment date"),
         payment_id))


def delete_payment(payment_id):
    """Financial records are normally kept; the app will only offer this to the Admin."""
    return execute("DELETE FROM payment WHERE payment_id = %s", (payment_id,))