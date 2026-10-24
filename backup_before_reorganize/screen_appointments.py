"""screen_appointments.py - the Appointments screen (Member 3)."""
from tkinter import ttk

import appointment_db
import doctor_db
import patient_db
from ui_common import (CrudScreen, Field, Column, show_error, friendly,
                       choice, choice_int)


class AppointmentsScreen(CrudScreen):
    title = "Appointments"
    subtitle = "Book, reschedule, complete or cancel appointments."
    id_key = "appointment_id"
    defaults = {"appointment_status": "Scheduled"}
    fields = [
        Field("appointment_id", "Appointment ID", "readonly"),
        Field("patient", "Patient", "combo", required=True),
        Field("doctor", "Doctor", "combo", required=True),
        Field("appointment_date", "Date (YYYY-MM-DD)", required=True),
        Field("appointment_time", "Time (HH:MM)", required=True),
        Field("appointment_status", "Status", "combo", ["Scheduled", "Completed", "Cancelled"]),
    ]
    columns = [
        Column("appointment_id", "ID", 60),
        Column("patient", "Patient", 200),
        Column("doctor", "Doctor", 200),
        Column("appointment_date", "Date", 110),
        Column("appointment_time", "Time", 90),
        Column("appointment_status", "Status", 110),
    ]

    def add_extra_buttons(self, bar):
        ttk.Button(bar, text="Mark Completed",
                   command=lambda: self.change_status("Completed")).pack(side="left", padx=(12, 6))
        ttk.Button(bar, text="Cancel Appointment",
                   command=lambda: self.change_status("Cancelled")).pack(side="left")

    def change_status(self, status):
        row_id = self.selected_id()
        if not row_id:
            show_error("Click an appointment in the table first.")
            return
        try:
            appointment_db.update_appointment_status(int(row_id), status)
        except Exception as e:
            show_error(friendly(e))
            return
        self.finish(f"Appointment marked {status}.")

    # ---- Step 11 ----
    def load_choices(self):
        self.set_choices("patient", [choice(p["patient_id"], p["name"])
                                     for p in patient_db.list_patients()])
        self.set_choices("doctor", [choice(d["doctor_id"], d["name"])
                                    for d in doctor_db.list_doctors()])

    def load_rows(self, search_text):
        return appointment_db.list_appointments()

    def form_values_from_row(self, row):
        values = dict(row)
        values["patient"] = choice(row["patient_id"], row["patient"])
        values["doctor"] = choice(row["doctor_id"], row["doctor"])
        return values

    def create_row(self, v):
        new_id = appointment_db.book_appointment(
            choice_int(v["patient"], "Patient"), choice_int(v["doctor"], "Doctor"),
            v["appointment_date"], v["appointment_time"])
        if v["appointment_status"] not in ("", "Scheduled"):
            appointment_db.update_appointment_status(new_id, v["appointment_status"])

    def update_row(self, row_id, v):
        row_id = int(row_id)
        current = appointment_db.get_appointment(row_id)
        if current is None:
            raise ValueError("That appointment no longer exists.")
        if (choice_int(v["patient"], "Patient") != current["patient_id"]
                or choice_int(v["doctor"], "Doctor") != current["doctor_id"]):
            raise ValueError("To change the patient or the doctor, cancel this appointment "
                             "and book a new one.")
        appointment_db.reschedule_appointment(row_id, v["appointment_date"], v["appointment_time"])
        if v["appointment_status"]:
            appointment_db.update_appointment_status(row_id, v["appointment_status"])

    def delete_row(self, row_id):
        if appointment_db.delete_appointment(int(row_id)) == 0:
            raise ValueError("That appointment no longer exists.")