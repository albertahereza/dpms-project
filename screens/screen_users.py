"""screen_users.py - the User Accounts screen (Member 2). Meant for the Admin only (Step 12)."""
from db_modules import users_db
from ui.ui_common import CrudScreen, Field, Column


class UsersScreen(CrudScreen):
    title = "User Accounts"
    subtitle = ("Create logins and set their roles. Passwords are stored hashed. "
                "When editing, leave Password empty to keep the current one.")
    id_key = "user_id"
    fields = [
        Field("user_id", "User ID", "readonly"),
        Field("username", "Username", required=True),
        Field("password", "Password (min 8 characters)", "password"),
        Field("role", "Role", "combo", ["Admin", "Doctor", "Receptionist"], required=True),
    ]
    columns = [
        Column("user_id", "ID", 60),
        Column("username", "Username", 220),
        Column("role", "Role", 160),
    ]

    # ---- Step 11 ----
    def load_rows(self, search_text):
        return users_db.list_users()

    def form_values_from_row(self, row):
        values = dict(row)
        values["password"] = ""            # the hash is never shown
        return values

    def create_row(self, v):
        if not v["password"]:
            raise ValueError("A password is required for a new account.")
        users_db.add_user(v["username"], v["password"], v["role"])

    def update_row(self, row_id, v):
        row_id = int(row_id)
        current = users_db.get_user(row_id)
        if current is None:
            raise ValueError("That user no longer exists.")
        if v["username"] != current["username"]:
            raise ValueError("A username cannot be changed.")
        if row_id == self.app.user["user_id"] and v["role"] != self.app.user["role"]:
            raise ValueError("You cannot change the role of the account you are signed in with.")
        users_db.update_user_role(row_id, v["role"])
        if v["password"]:
            users_db.change_password(row_id, v["password"])

    def delete_row(self, row_id):
        if int(row_id) == self.app.user["user_id"]:
            raise ValueError("You cannot delete the account you are signed in with.")
        if users_db.delete_user(int(row_id)) == 0:
            raise ValueError("That user no longer exists.")