"""screen_prescriptions.py - the Prescriptions screen (Member 4)."""
from db_modules import medical_record_db
from db_modules import prescription_db
from ui.ui_common import CrudScreen, Field, Column, choice, choice_int


def _record_label(patient, diagnosis):
    return f"{patient} - {diagnosis or 'no diagnosis'}"


class PrescriptionsScreen(CrudScreen):
    title = "Prescriptions"
    subtitle = "Add the medicines prescribed in a medical record."
    id_key = "prescription_id"
    fields = [
        Field("prescription_id", "Prescription ID", "readonly"),
        Field("medical_record", "Medical record", "combo", required=True),
        Field("prescription", "Prescription", "text", required=True),
    ]
    columns = [
        Column("prescription_id", "ID", 60),
        Column("medical_record_id", "Record", 70),
        Column("patient", "Patient", 170),
        Column("diagnosis", "Diagnosis", 220),
        Column("prescription", "Prescription", 380),
    ]

    # ---- Step 11 ----
    def load_choices(self):
        self.set_choices("medical_record", [
            choice(r["medical_record_id"], _record_label(r["patient"], r["diagnosis"]))
            for r in medical_record_db.list_records()])

    def load_rows(self, search_text):
        return prescription_db.list_prescriptions()

    def form_values_from_row(self, row):
        values = dict(row)
        values["medical_record"] = choice(row["medical_record_id"],
                                          _record_label(row["patient"], row["diagnosis"]))
        return values

    def create_row(self, v):
        prescription_db.add_prescription(choice_int(v["medical_record"], "Medical record"),
                                         v["prescription"])

    def update_row(self, row_id, v):
        row_id = int(row_id)
        current = prescription_db.get_prescription(row_id)
        if current is None:
            raise ValueError("That prescription no longer exists.")
        if choice_int(v["medical_record"], "Medical record") != current["medical_record_id"]:
            raise ValueError("A prescription cannot be moved to another medical record. "
                             "Delete it and add a new one.")
        prescription_db.update_prescription(row_id, v["prescription"])

    def delete_row(self, row_id):
        if prescription_db.delete_prescription(int(row_id)) == 0:
            raise ValueError("That prescription no longer exists.")