"""
test_modules.py - Step 9 check for DPMS.
Run from inside the dpms_app folder:   python -m tests.test_modules

It adds temporary rows, uses every module, then deletes what it added.
(The ID counters move on, so your next real record gets a higher number.)
"""
import psycopg2

from db_modules import users_db, doctor_db, patient_db, appointment_db
from db_modules import medical_record_db, prescription_db, payment_db
from core.db import explain_error, fetch_one

failures = 0
cleanup = []          # things to delete at the end, newest first


def check(label, condition):
    global failures
    print(("PASS  " if condition else "FAIL  ") + label)
    if not condition:
        failures += 1


def expect_error(label, func, *args):
    """The database SHOULD refuse this call. Shows the message a user would see."""
    global failures
    try:
        func(*args)
        print("FAIL  " + label + "  (it was accepted!)")
        failures += 1
    except (psycopg2.Error, ValueError) as e:
        print("PASS  " + label)
        print("        message ->", explain_error(e) if isinstance(e, psycopg2.Error) else e)


def counts():
    return {t: fetch_one(f"SELECT COUNT(*) AS n FROM {t}")["n"]
            for t in ("users", "doctor", "patient", "appointment",
                      "medical_record", "prescription", "payment")}


def main():
    before = counts()
    print("=== DPMS: database module tests ===\n")
    try:
        print("--- users_db and doctor_db (Member 2) ---")
        admin = users_db.verify_login("admin01", "Clinic@2026")
        check("verify_login accepts the right password (role Admin)",
              admin is not None and admin["role"] == "Admin")
        check("verify_login rejects a wrong password",
              users_db.verify_login("admin01", "wrong-password") is None)
        check("list_users returns accounts and no password column",
              len(users_db.list_users()) >= 8 and "password" not in users_db.list_users()[0])
        check("list_doctors returns the doctors with usernames",
              len(doctor_db.list_doctors()) >= 5)
        check("get_doctor_by_user(4) is Dr. Peter Okello",
              doctor_db.get_doctor_by_user(4)["name"] == "Dr. Peter Okello")
        tmp_user = users_db.add_user("tmp_test_user", "Temp@12345", "Receptionist")
        cleanup.append(lambda: users_db.delete_user(tmp_user))
        check("add_user then verify_login works", users_db.verify_login("tmp_test_user", "Temp@12345"))
        expect_error("add_user with a duplicate username is refused",
                     users_db.add_user, "tmp_test_user", "Temp@12345", "Receptionist")
        expect_error("a Receptionist account cannot become a doctor (trigger)",
                     doctor_db.add_doctor, tmp_user, "Dr. Nobody", "General Physician")

        print("\n--- patient_db (Member 3) ---")
        pid = patient_db.add_patient("Test Patient", "1999-05-05", "Female", "0700000001")
        cleanup.append(lambda: patient_db.delete_patient(pid))
        check("add_patient + get_patient", patient_db.get_patient(pid)["name"] == "Test Patient")
        patient_db.update_patient(pid, "Test Patient", "1999-05-05", "Female", "0700000002")
        check("update_patient changed the phone number",
              patient_db.get_patient(pid)["phone_number"] == "0700000002")
        check("search_patients finds it by part of the name (any case)",
              any(r["patient_id"] == pid for r in patient_db.search_patients("test pat")))
        expect_error("a patient with a bad phone number is refused (trigger)",
                     patient_db.add_patient, "Bad Phone", "2000-01-01", "Male", "12ab")
        expect_error("a patient with no name is refused",
                     patient_db.add_patient, "   ", "2000-01-01")

        print("\n--- appointment_db (Member 3) ---")
        aid = appointment_db.book_appointment(pid, 5, "2027-01-15", "10:00")
        cleanup.append(lambda: appointment_db.delete_appointment(aid))
        check("book_appointment gives status Scheduled by default",
              appointment_db.get_appointment(aid)["appointment_status"] == "Scheduled")
        expect_error("booking the same doctor at the same time is refused (trigger)",
                     appointment_db.book_appointment, 1, 5, "2027-01-15", "10:00")
        appointment_db.reschedule_appointment(aid, "2027-01-15", "11:00")
        check("reschedule_appointment moved it to 11:00",
              str(appointment_db.get_appointment(aid)["appointment_time"]) == "11:00:00")
        check("list_appointments_for_patient finds it",
              len(appointment_db.list_appointments_for_patient(pid)) == 1)
        appointment_db.update_appointment_status(aid, "Completed")
        expect_error("a Completed appointment cannot go back to Scheduled (trigger)",
                     appointment_db.update_appointment_status, aid, "Scheduled")

        print("\n--- medical_record_db, prescription_db, payment_db (Member 4) ---")
        mrid = medical_record_db.add_record(aid, 5, "No significant history", "Dental caries")
        cleanup.append(lambda: medical_record_db.delete_record(mrid))
        check("add_record copies the patient from the appointment",
              medical_record_db.get_record(mrid)["patient_id"] == pid)
        expect_error("a second record for the same appointment is refused",
                     medical_record_db.add_record, aid, 5, "x", "y")
        expect_error("a record for an unknown appointment is refused",
                     medical_record_db.add_record, 99999, 5, "x", "y")
        prid = prescription_db.add_prescription(mrid, "Ibuprofen 400mg, when needed")
        cleanup.append(lambda: prescription_db.delete_prescription(prid))
        check("add_prescription + list_prescriptions_for_patient",
              len(prescription_db.list_prescriptions_for_patient(pid)) == 1)
        payid = payment_db.add_payment(pid, "Consultation", "50,000", "Cash")
        cleanup.append(lambda: payment_db.delete_payment(payid))
        check("add_payment (comma in amount, date defaults to today)",
              payment_db.get_payment(payid)["amount"] == 50000)
        check("total_paid_by_patient is 50000", payment_db.total_paid_by_patient(pid) == 50000)
        expect_error("a payment of 0 is refused (CHECK constraint)",
                     payment_db.add_payment, pid, "Consultation", "0", "Cash")
        expect_error("a payment with letters in the amount is refused",
                     payment_db.add_payment, pid, "Consultation", "abc", "Cash")
        expect_error("a patient with records cannot be deleted (foreign key)",
                     patient_db.delete_patient, pid)
    finally:
        # delete in reverse order, so children go before parents
        for undo in reversed(cleanup):
            try:
                undo()
            except psycopg2.Error as e:
                print("CLEANUP problem:", explain_error(e))

    print("\n--- cleanup check ---")
    check("every table is back to its original row count", counts() == before)
    print("\nFAILED TESTS:", failures if failures else "none  -> all module tests passed")


if __name__ == "__main__":
    main()