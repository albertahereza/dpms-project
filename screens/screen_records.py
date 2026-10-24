"""screen_records.py - the Medical Records screen (Member 4)."""
from db_modules import appointment_db
from db_modules import doctor_db
from db_modules import medical_record_db
from ui.ui_common import CrudScreen, Field, Column, choice, choice_int


class MedicalRecordsScreen(CrudScreen):
    title = "Medical Records"
    subtitle = "Write the history and diagnosis for an appointment."
    id_key = "medical_record_id"
    fields = [
        Field("medical_record_id", "Record ID", "readonly"),
        Field("appointment", "Appointment", "combo", required=True),
        Field("doctor", "Doctor", "combo", required=True),
        Field("patient", "Patient (from the appointment)", "readonly"),
        Field("medical_history", "Medical history", "text"),
        Field("diagnosis", "Diagnosis", "text"),
    ]
    columns = [
        Column("medical_record_id", "ID", 60),
        Column("patient", "Patient", 180),
        Column("doctor", "Doctor", 180),
        Column("appointment_date", "Visit date", 110),
        Column("diagnosis", "Diagnosis", 320),
    ]

    # ---- Step 11 ----
    def load_choices(self):
        # only appointments that are not cancelled and have no record yet
        self.set_choices("appointment", [
            choice(a["appointment_id"], f"{a['patient']}, {a['appointment_date']}")
            for a in appointment_db.list_appointments_without_record()])
        self.set_choices("doctor", [choice(d["doctor_id"], d["name"])
                                    for d in doctor_db.list_doctors()])

    def load_rows(self, search_text):
        return medical_record_db.list_records()

    def form_values_from_row(self, row):
        values = dict(row)
        values["appointment"] = choice(row["appointment_id"],
                                       f"{row['patient']}, {row['appointment_date']}")
        values["doctor"] = choice(row["doctor_id"], row["doctor"])
        return values

    def create_row(self, v):
        medical_record_db.add_record(choice_int(v["appointment"], "Appointment"),
                                     choice_int(v["doctor"], "Doctor"),
                                     v["medical_history"], v["diagnosis"])

    def update_row(self, row_id, v):
        row_id = int(row_id)
        current = medical_record_db.get_record(row_id)
        if current is None:
            raise ValueError("That record no longer exists.")
        if (choice_int(v["appointment"], "Appointment") != current["appointment_id"]
                or choice_int(v["doctor"], "Doctor") != current["doctor_id"]):
            raise ValueError("Only the history and the diagnosis can be changed on an "
                             "existing record.")
        medical_record_db.update_record(row_id, v["medical_history"], v["diagnosis"])

    def delete_row(self, row_id):
        if medical_record_db.delete_record(int(row_id)) == 0:
            raise ValueError("That record no longer exists.")