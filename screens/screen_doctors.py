"""screen_doctors.py - the Doctors screen (Member 2)."""
from db_modules import doctor_db
from db_modules import users_db
from ui.ui_common import CrudScreen, Field, Column, choice, choice_int


class DoctorsScreen(CrudScreen):
    title = "Doctors"
    subtitle = "Each doctor is linked to a login account whose role is Doctor."
    id_key = "doctor_id"
    fields = [
        Field("doctor_id", "Doctor ID", "readonly"),
        Field("user", "Login account", "combo", required=True),
        Field("name", "Full name", required=True),
        Field("specialty", "Specialty", required=True),
    ]
    columns = [
        Column("doctor_id", "ID", 60),
        Column("name", "Name", 240),
        Column("specialty", "Specialty", 200),
        Column("username", "Login name", 160),
    ]

    # ---- Step 11 ----
    def load_choices(self):
        # only Doctor accounts that are not yet linked to a doctor profile
        linked = {d["user_id"] for d in doctor_db.list_doctors()}
        self.set_choices("user", [choice(u["user_id"], u["username"])
                                  for u in users_db.list_users()
                                  if u["role"] == "Doctor" and u["user_id"] not in linked])

    def load_rows(self, search_text):
        return doctor_db.list_doctors()

    def form_values_from_row(self, row):
        values = dict(row)
        values["user"] = choice(row["user_id"], row["username"])
        return values

    def create_row(self, v):
        doctor_db.add_doctor(choice_int(v["user"], "Login account"), v["name"], v["specialty"])

    def update_row(self, row_id, v):
        row_id = int(row_id)
        current = doctor_db.get_doctor(row_id)
        if current is None:
            raise ValueError("That doctor no longer exists.")
        if choice_int(v["user"], "Login account") != current["user_id"]:
            raise ValueError("The login account of a doctor cannot be changed.")
        doctor_db.update_doctor(row_id, v["name"], v["specialty"])

    def delete_row(self, row_id):
        if doctor_db.delete_doctor(int(row_id)) == 0:
            raise ValueError("That doctor no longer exists.")