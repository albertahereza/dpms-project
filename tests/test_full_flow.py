"""
test_full_flow.py - Step 14: automated end-to-end test of the whole DPMS (Group 7).

Run from inside the dpms_app folder:   python -m tests.test_full_flow

It plays one full clinic day through the real modules (register, book, treat, prescribe,
pay, report), then tries to break every rule, then tidies up after itself.
Results are printed AND saved to test_results.csv for your report.
"""
import csv
import io

import psycopg2
from psycopg2 import errors as pg
from matplotlib.figure import Figure

from db_modules import appointment_db, doctor_db, medical_record_db
from core import auth
from db_modules import patient_db, payment_db, prescription_db, users_db
from reporting import report_db, reports
from core.db import execute, fetch_one

results = []       # (id, category, test, expected, actual, status)
cleanup = []       # undo actions, run newest first
ctx = {}           # values passed from one test to the next


# ---------------------------------------------------------------- test helpers
def message_of(e):
    diag = getattr(e, "diag", None)
    text = getattr(diag, "message_primary", None) or str(e)
    return text.strip().splitlines()[0]


def step(tid, category, test, expected, func):
    """Run func(). It returns (passed, actual_text). An unexpected error counts as a FAIL."""
    try:
        passed, actual = func()
    except Exception as e:
        passed, actual = False, f"Unexpected {type(e).__name__}: {message_of(e)}"
    results.append((tid, category, test, expected, actual, "PASS" if passed else "FAIL"))
    print(f"{'PASS' if passed else 'FAIL'}  {tid}  {test}")
    if not passed:
        print(f"        expected: {expected}\n        actual:   {actual}")


def refused(error_type, call, must_contain=None):
    """The database SHOULD refuse call() with error_type."""
    def run():
        try:
            call()
        except error_type as e:
            text = message_of(e)
            ok = must_contain is None or must_contain.lower() in text.lower()
            return ok, f"Refused: {text}"
        except ValueError as e:
            if error_type is ValueError:
                return True, f"Refused: {e}"
            raise
        return False, "Accepted (it should have been refused)"
    return run


def counts():
    return {t: fetch_one(f"SELECT COUNT(*) AS n FROM {t}")["n"]
            for t in ("users", "doctor", "patient", "appointment",
                      "medical_record", "prescription", "payment")}


def track(undo):
    cleanup.append(undo)


# ---------------------------------------------------------------- the tests
def main():
    before = counts()
    print("=== DPMS: complete flow test ===\n")
    try:
        # ============ A. the full clinic workflow (happy path) ============
        cat = "A. Full workflow"
        rev_before = sum(float(r["revenue"]) for r in report_db.revenue_by_method())

        def t01():
            u = auth.authenticate("reception01", "Clinic@2026")
            ctx["reception"] = u
            return bool(u) and u["role"] == "Receptionist", f"Signed in as {u and u['role']}"
        step("T14-01", cat, "Receptionist signs in", "Login succeeds, role Receptionist", t01)

        def t02():
            ctx["pid"] = patient_db.add_patient("Flow Patient", "1995-04-12", "Female", "0700123456")
            track(lambda p=ctx["pid"]: patient_db.delete_patient(p))
            return ctx["pid"] > 0, f"Patient {ctx['pid']} registered"
        step("T14-02", cat, "Receptionist registers a patient", "New patient_id returned", t02)

        def t03():
            ctx["aid"] = appointment_db.book_appointment(ctx["pid"], 1, "2027-02-10", "09:00")
            track(lambda a=ctx["aid"]: appointment_db.delete_appointment(a))
            a = appointment_db.get_appointment(ctx["aid"])
            return a["appointment_status"] == "Scheduled", f"Status {a['appointment_status']} with {a['doctor']}"
        step("T14-03", cat, "Receptionist books the appointment with Dr. Okello",
             "Booked, status Scheduled by default", t03)

        def t04():
            rows = appointment_db.list_appointments_for_patient(ctx["pid"])
            return len(rows) == 1 and rows[0]["patient"] == "Flow Patient", f"{len(rows)} appointment listed"
        step("T14-04", cat, "The appointment appears in the patient's list", "1 appointment shown", t04)

        def t05():
            u = auth.authenticate("dr.okello", "Clinic@2026")
            doc = doctor_db.get_doctor_by_user(u["user_id"])
            ctx["doc"] = doc
            return u["role"] == "Doctor" and doc["doctor_id"] == 1, f"{doc['name']} (doctor {doc['doctor_id']})"
        step("T14-05", cat, "Dr. Okello signs in and his doctor profile is found",
             "Role Doctor, doctor_id 1", t05)

        def t06():
            appointment_db.update_appointment_status(ctx["aid"], "Completed")
            s = appointment_db.get_appointment(ctx["aid"])["appointment_status"]
            return s == "Completed", f"Status now {s}"
        step("T14-06", cat, "The doctor marks the appointment Completed", "Status Completed", t06)

        def t07():
            ctx["mrid"] = medical_record_db.add_record(ctx["aid"], 1, "No known allergies", "Malaria")
            track(lambda m=ctx["mrid"]: medical_record_db.delete_record(m))
            r = medical_record_db.get_record(ctx["mrid"])
            return r["patient_id"] == ctx["pid"], f"Record {ctx['mrid']} belongs to patient {r['patient_id']}"
        step("T14-07", cat, "The doctor writes the medical record",
             "Record saved; patient copied from the appointment", t07)

        def t08():
            for text in ("Artemether-Lumefantrine 80/480mg twice daily", "Paracetamol 500mg three times daily"):
                pr = prescription_db.add_prescription(ctx["mrid"], text)
                track(lambda p=pr: prescription_db.delete_prescription(p))
            rows = prescription_db.list_prescriptions_for_patient(ctx["pid"])
            return len(rows) == 2, f"{len(rows)} prescriptions found for the patient"
        step("T14-08", cat, "The doctor adds two prescriptions", "2 prescriptions listed for the patient", t08)

        def t09():
            pay = payment_db.add_payment(ctx["pid"], "Consultation", "75000", "Mobile Money")
            track(lambda p=pay: payment_db.delete_payment(p))
            total = payment_db.total_paid_by_patient(ctx["pid"])
            return float(total) == 75000.0, f"Total paid {total}"
        step("T14-09", cat, "Receptionist records a Mobile Money payment of 75,000",
             "Payment saved; total paid 75,000", t09)

        def t10():
            diff = sum(float(r["revenue"]) for r in report_db.revenue_by_method()) - rev_before
            return abs(diff - 75000.0) < 0.01, f"Revenue report rose by {diff:,.2f}"
        step("T14-10", cat, "The revenue report includes the new payment", "Revenue rises by exactly 75,000", t10)

        def t11():
            bad = []
            for r in reports.REPORTS:
                rows = r.fetch()
                text = r.insight(rows)
                fig = Figure()
                reports.draw_chart(fig, r, rows)
                buf = io.BytesIO()
                fig.savefig(buf, format="png")
                if not text or len(buf.getvalue()) < 1500:
                    bad.append(r.key)
            return not bad, "All 7 reports gave a table, an insight and a chart" if not bad else f"Problems: {bad}"
        step("T14-11", cat, "Every report produces a table, a text insight and a chart",
             "7 reports work with live data", t11)

        def t12():
            n = fetch_one("""SELECT COUNT(*) AS n FROM patient p
                             JOIN appointment a      ON a.patient_id = p.patient_id
                             JOIN medical_record mr  ON mr.appointment_id = a.appointment_id
                             JOIN prescription pr    ON pr.medical_record_id = mr.medical_record_id
                             WHERE p.patient_id = %s""", (ctx["pid"],))["n"]
            return n == 2, f"Join patient to appointment to record to prescription gives {n} rows"
        step("T14-12", cat, "The relationship chain joins correctly in SQL", "2 rows", t12)

        # ============ B. rules the database must enforce ============
        cat = "B. Integrity and rules"
        step("T14-13", cat, "Duplicate username", "Refused (UNIQUE)",
             refused(pg.UniqueViolation, lambda: users_db.add_user("admin01", "Another@123", "Admin"), "uq_users_username"))
        step("T14-14", cat, "Appointment for a patient that does not exist", "Refused (FOREIGN KEY)",
             refused(pg.ForeignKeyViolation, lambda: appointment_db.book_appointment(999999, 1, "2027-05-01", "08:00"), "fk_appointment_patient"))
        step("T14-15", cat, "Patient with no date of birth", "Refused (NOT NULL)",
             refused(pg.NotNullViolation, lambda: execute("INSERT INTO patient (name) VALUES (%s)", ("No DOB",)), "date_of_birth"))
        step("T14-16", cat, "Payment of 0", "Refused (CHECK)",
             refused(pg.CheckViolation, lambda: payment_db.add_payment(ctx["pid"], "Consultation", "0", "Cash"), "ck_payment_amount"))
        step("T14-17", cat, "Gender 'Unknown'", "Refused (CHECK)",
             refused(pg.CheckViolation, lambda: execute("INSERT INTO patient (name, date_of_birth, gender) VALUES (%s, %s, %s)", ("Bad Gender", "2000-01-01", "Unknown")), "ck_patient_gender"))
        step("T14-18", cat, "Date of birth 'abcd' (wrong data type)", "Refused (invalid date)",
             refused(pg.InvalidDatetimeFormat, lambda: execute("INSERT INTO patient (name, date_of_birth) VALUES (%s, %s)", ("Bad Date", "abcd"))))
        step("T14-19", cat, "Doctor 1 booked twice at the same time", "Refused (trigger)",
             refused(pg.RaiseException, lambda: appointment_db.book_appointment(1, 1, "2027-02-10", "09:00"), "already booked"))
        step("T14-20", cat, "Completed appointment changed back to Scheduled", "Refused (trigger)",
             refused(pg.RaiseException, lambda: appointment_db.update_appointment_status(ctx["aid"], "Scheduled"), "cannot be changed"))
        step("T14-21", cat, "Record whose patient differs from the appointment's patient", "Refused (trigger)",
             refused(pg.RaiseException, lambda: execute(
                 "INSERT INTO medical_record (appointment_id, patient_id, doctor_id, diagnosis) VALUES (%s, %s, %s, %s)",
                 (ctx["aid"], 1, 1, "Test")), "does not match"))

        def t22():
            ctx["aid2"] = appointment_db.book_appointment(ctx["pid"], 2, "2027-03-05", "10:00")
            track(lambda a=ctx["aid2"]: appointment_db.delete_appointment(a))
            appointment_db.cancel_appointment(ctx["aid2"])
            return refused(pg.RaiseException, lambda: medical_record_db.add_record(ctx["aid2"], 2, "x", "y"), "cancelled")()
        step("T14-22", cat, "Medical record for a cancelled appointment", "Refused (trigger)", t22)

        step("T14-23", cat, "Doctor profile for a Receptionist account", "Refused (trigger)",
             refused(pg.RaiseException, lambda: doctor_db.add_doctor(ctx["reception"]["user_id"], "Dr. Fake", "General Physician"), "only users with role"))
        step("T14-24", cat, "Patient with an invalid phone number", "Refused (trigger)",
             refused(pg.RaiseException, lambda: patient_db.add_patient("Bad Phone", "2000-01-01", "Male", "12ab"), "invalid phone"))
        step("T14-25", cat, "Delete a patient who has appointments and records", "Refused (FOREIGN KEY RESTRICT)",
             refused(pg.ForeignKeyViolation, lambda: patient_db.delete_patient(ctx["pid"])))
        step("T14-26", cat, "Second medical record for the same appointment", "Refused (UNIQUE)",
             refused(pg.UniqueViolation, lambda: medical_record_db.add_record(ctx["aid"], 1, "x", "y"), "uq_medical_record_appointment"))
        step("T14-27", cat, "Second doctor profile for the same login account", "Refused (UNIQUE)",
             refused(pg.UniqueViolation, lambda: doctor_db.add_doctor(4, "Dr. Twin", "General Physician"), "uq_doctor_user_id"))

        # ============ C. security ============
        cat = "C. Security"
        step("T14-28", cat, "Wrong password", "Login refused",
             lambda: (auth.authenticate("admin01", "wrong-password") is None, "No user returned"))
        step("T14-29", cat, "SQL injection in the username box", "Login refused",
             lambda: (auth.authenticate("admin01' OR '1'='1", "x") is None, "No user returned"))
        step("T14-30", cat, "SQL injection in the password box", "Login refused",
             lambda: (auth.authenticate("admin01", "' OR '1'='1") is None, "No user returned"))

        def t31():
            n = fetch_one("SELECT COUNT(*) AS n FROM users WHERE password NOT LIKE '$2%'")["n"]
            return n == 0, f"{n} passwords are not bcrypt hashes"
        step("T14-31", cat, "Every stored password is a hash", "0 plain-text passwords", t31)

        step("T14-32", cat, "Role permissions", "Admin opens Users; Receptionist cannot; Doctor cannot open Payments",
             lambda: (auth.can_open("Admin", "users") and not auth.can_open("Receptionist", "users")
                      and not auth.can_open("Doctor", "payments") and auth.can_open("Doctor", "records"),
                      "Permission table behaves as designed"))

        # ============ D. edge cases ============
        cat = "D. Edge cases"

        def t33():
            pay = payment_db.add_payment(ctx["pid"], "Edge test", "0.01", "Cash")
            track(lambda p=pay: payment_db.delete_payment(p))
            return float(payment_db.get_payment(pay)["amount"]) == 0.01, "Smallest amount 0.01 accepted"
        step("T14-33", cat, "Smallest valid payment (0.01)", "Accepted", t33)

        step("T14-34", cat, "Payment larger than NUMERIC(10,2) allows (100,000,000)", "Refused (out of range)",
             refused(pg.NumericValueOutOfRange, lambda: payment_db.add_payment(ctx["pid"], "Edge test", "100000000", "Cash")))
        step("T14-35", cat, "Patient name of 101 characters", "Refused (too long)",
             refused(pg.StringDataRightTruncation, lambda: patient_db.add_patient("A" * 101, "2000-01-01")))

        def t36():
            p = patient_db.add_patient("Minimal Patient", "1990-01-01")
            track(lambda x=p: patient_db.delete_patient(x))
            r = patient_db.get_patient(p)
            return r["gender"] is None and r["phone_number"] is None, "Saved with gender and phone empty (NULL)"
        step("T14-36", cat, "Patient with only the required fields", "Accepted; optional fields are NULL", t36)

        def t37():
            p = patient_db.add_patient("   Trim Me   ", "1990-01-01", None, "+256700000001")
            track(lambda x=p: patient_db.delete_patient(x))
            name = patient_db.get_patient(p)["name"]
            return name == "Trim Me", f"Stored as '{name}' and phone with + accepted"
        step("T14-37", cat, "Name with spaces and a phone starting with +", "Name trimmed; phone accepted", t37)

        def t38():
            b = appointment_db.book_appointment(ctx["pid"], 2, "2027-03-05", "10:00")
            track(lambda a=b: appointment_db.delete_appointment(a))
            return b > 0, "A cancelled slot was booked again"
        step("T14-38", cat, "Book a slot that was cancelled", "Accepted", t38)

        step("T14-39", cat, "Update a patient that does not exist", "0 rows changed (no crash)",
             lambda: (patient_db.update_patient(999999, "Nobody", "2000-01-01") == 0, "Returned 0"))
        step("T14-40", cat, "Look up a patient that does not exist", "None returned (no crash)",
             lambda: (patient_db.get_patient(999999) is None, "Returned None"))

    finally:
        for undo in reversed(cleanup):
            try:
                undo()
            except psycopg2.Error as e:
                print("CLEANUP problem:", message_of(e))

    after = counts()
    step("T14-41", "E. Cleanup", "Every table is back to its original row count",
         "Same counts as before the test", lambda: (before == after, f"before={before} after={after}"))

    # ---------------------------------------------------------------- results
    passed = sum(1 for r in results if r[5] == "PASS")
    print(f"\nRESULT: {passed} of {len(results)} tests passed.")
    with open("test_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Test ID", "Category", "Test", "Expected Result", "Actual Result", "Status"])
        writer.writerows(results)
    print("Saved test_results.csv (open it in Excel for your report).")
    print("Note: ID counters moved on; rerun 04_insert_sample_data.sql if you want IDs to restart at 1.")


if __name__ == "__main__":
    main()