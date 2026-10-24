"""screen_patients.py - the Patients screen (Member 3)."""
from db_modules import patient_db
from ui.ui_common import CrudScreen, Field, Column


class PatientsScreen(CrudScreen):
    title = "Patients"
    subtitle = "Register new patients, find them and correct their details."
    id_key = "patient_id"
    searchable = True
    fields = [
        Field("patient_id", "Patient ID", "readonly"),
        Field("name", "Full name", required=True),
        Field("date_of_birth", "Date of birth (YYYY-MM-DD)", required=True),
        Field("gender", "Gender", "combo", ["", "Male", "Female", "Other"]),
        Field("phone_number", "Phone number"),
    ]
    columns = [
        Column("patient_id", "ID", 70),
        Column("name", "Name", 240),
        Column("date_of_birth", "Date of birth", 120),
        Column("gender", "Gender", 90),
        Column("phone_number", "Phone", 140),
    ]

    # ---- Step 11: the four hooks, each calling patient_db ----
    def load_rows(self, search_text):
        if search_text:
            return patient_db.search_patients(search_text)
        return patient_db.list_patients()

    def create_row(self, v):
        patient_db.add_patient(v["name"], v["date_of_birth"], v["gender"], v["phone_number"])

    def update_row(self, row_id, v):
        changed = patient_db.update_patient(int(row_id), v["name"], v["date_of_birth"],
                                            v["gender"], v["phone_number"])
        if changed == 0:
            raise ValueError("That patient no longer exists.")

    def delete_row(self, row_id):
        if patient_db.delete_patient(int(row_id)) == 0:
            raise ValueError("That patient no longer exists.")