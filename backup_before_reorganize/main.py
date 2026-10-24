"""
main.py - starts the DPMS application (Member 5, with the login from Member 2).
Run from inside the dpms_app folder:   python main.py
"""
import tkinter as tk
from tkinter import messagebox, ttk

import auth
from login_window import LoginWindow
from ui_common import apply_style
from screen_home import HomeScreen
from screen_patients import PatientsScreen
from screen_appointments import AppointmentsScreen
from screen_records import MedicalRecordsScreen
from screen_prescriptions import PrescriptionsScreen
from screen_payments import PaymentsScreen
from screen_doctors import DoctorsScreen
from screen_users import UsersScreen
from screen_reports import ReportsScreen

# key, menu label, one-line description, screen class
NAV = [
    ("home",          "Home",            "",                              HomeScreen),
    ("patients",      "Patients",        "Register and find patients",    PatientsScreen),
    ("appointments",  "Appointments",    "Book, reschedule, cancel",      AppointmentsScreen),
    ("records",       "Medical Records", "History and diagnoses",         MedicalRecordsScreen),
    ("prescriptions", "Prescriptions",   "Medicines for a record",        PrescriptionsScreen),
    ("payments",      "Payments",        "Record and view payments",      PaymentsScreen),
    ("doctors",       "Doctors",         "Doctor profiles",               DoctorsScreen),
    ("users",         "User Accounts",   "Logins and roles",              UsersScreen),
    ("reports",       "Reports",         "Summaries and charts",          ReportsScreen),
]


class App(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user                       # {user_id, username, role}
        self.logout_requested = False
        self.title("DPMS - Digital Patient Management System (Group 7)")
        self.geometry("1200x760")
        self.minsize(1000, 640)
        apply_style(self)

        # only the screens this role may open
        self.allowed = [row for row in NAV if auth.can_open(user["role"], row[0])]
        self.nav_cards = [(k, label, desc) for k, label, desc, _ in self.allowed if k != "home"]
        self.screens = {}                      # screens are created the first time they are opened

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_sidebar()
        self.content = ttk.Frame(self)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)
        self._build_menubar()
        self.show("home")

    # ------------------------------------------------------------ layout
    def _build_sidebar(self):
        bar = ttk.Frame(self, style="Sidebar.TFrame", width=210)
        bar.grid(row=0, column=0, sticky="ns")
        bar.pack_propagate(False)
        ttk.Label(bar, text="DPMS", style="Sidebar.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=16, pady=(20, 2))
        ttk.Label(bar, text="Patient Management", style="Sidebar.TLabel").pack(
            anchor="w", padx=16, pady=(0, 18))
        for key, label, _desc, _cls in self.allowed:
            ttk.Button(bar, text=label, style="Nav.TButton",
                       command=lambda k=key: self.show(k)).pack(fill="x")
        # packed from the bottom up: the log out button first, then the user label above it
        ttk.Button(bar, text="Log out", style="Nav.TButton", command=self.logout).pack(
            side="bottom", fill="x", pady=(0, 10))
        ttk.Label(bar, text=f"{self.user['username']}\n{self.user['role']}",
                  style="Sidebar.TLabel").pack(side="bottom", anchor="w", padx=16, pady=8)

    def _build_menubar(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Log out", command=self.logout)
        file_menu.add_command(label="Exit", command=self.quit_app)
        menubar.add_cascade(label="File", menu=file_menu)
        go_menu = tk.Menu(menubar, tearoff=0)
        for key, label, _desc, _cls in self.allowed:
            go_menu.add_command(label=label, command=lambda k=key: self.show(k))
        menubar.add_cascade(label="Go to", menu=go_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    # ------------------------------------------------------------ navigation
    def show(self, key):
        """Open a screen (creating it the first time) and hide the others."""
        if not auth.can_open(self.user["role"], key):        # the permission check
            messagebox.showwarning("DPMS", "Your role does not allow you to open this screen.")
            return
        if key not in self.screens:
            screen_class = {k: cls for k, _l, _d, cls in NAV}[key]
            screen = screen_class(self.content, self)
            screen.grid(row=0, column=0, sticky="nsew")
            self.screens[key] = screen
        for other_key, screen in self.screens.items():
            if other_key != key:
                screen.grid_remove()
        screen = self.screens[key]
        screen.grid()
        screen.tkraise()
        if hasattr(screen, "on_show"):
            screen.on_show()

    def about(self):
        messagebox.showinfo("About DPMS",
                            "Digital Patient Management System\nGroup 7\n"
                            "PostgreSQL + Python (Tkinter)\n\n"
                            f"Signed in as {self.user['username']} ({self.user['role']})")

    def logout(self):
        if messagebox.askyesno("Log out", "Log out and return to the sign-in window?"):
            self.logout_requested = True
            self.destroy()

    def quit_app(self):
        if messagebox.askyesno("Exit", "Close the application?"):
            self.destroy()


def main():
    while True:
        user = LoginWindow().run()             # None if the window was closed or login failed
        if user is None:
            break
        app = App(user)
        app.mainloop()
        if not app.logout_requested:           # Exit (or closing the window) ends the program
            break


if __name__ == "__main__":
    main()