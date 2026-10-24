"""screen_payments.py - the Payments screen (Member 4)."""
import patient_db
import payment_db
from ui_common import CrudScreen, Field, Column, choice, choice_int


class PaymentsScreen(CrudScreen):
    title = "Payments"
    subtitle = "Record what patients pay. Leave the date empty to use today."
    id_key = "payment_id"
    can_delete = False            # financial records are kept, not deleted
    fields = [
        Field("payment_id", "Payment ID", "readonly"),
        Field("patient", "Patient", "combo", required=True),
        Field("service_type", "Service", required=True),
        Field("amount", "Amount (UGX)", required=True),
        Field("payment_method", "Payment method", "combo",
              ["Cash", "Mobile Money", "Card", "Insurance"], required=True),
        Field("payment_date", "Date (YYYY-MM-DD, empty = today)"),
    ]
    columns = [
        Column("payment_id", "ID", 60),
        Column("patient", "Patient", 190),
        Column("service_type", "Service", 160),
        Column("amount", "Amount", 110),
        Column("payment_method", "Method", 120),
        Column("payment_date", "Date", 110),
    ]

    # ---- Step 11 ----
    def load_choices(self):
        self.set_choices("patient", [choice(p["patient_id"], p["name"])
                                     for p in patient_db.list_patients()])

    def load_rows(self, search_text):
        return payment_db.list_payments()

    def form_values_from_row(self, row):
        values = dict(row)
        values["patient"] = choice(row["patient_id"], row["patient"])
        return values

    def create_row(self, v):
        payment_db.add_payment(choice_int(v["patient"], "Patient"), v["service_type"],
                               v["amount"], v["payment_method"], v["payment_date"])

    def update_row(self, row_id, v):
        row_id = int(row_id)
        current = payment_db.get_payment(row_id)
        if current is None:
            raise ValueError("That payment no longer exists.")
        if choice_int(v["patient"], "Patient") != current["patient_id"]:
            raise ValueError("The patient of a payment cannot be changed.")
        payment_db.update_payment(row_id, v["service_type"], v["amount"],
                                  v["payment_method"], v["payment_date"] or current["payment_date"])