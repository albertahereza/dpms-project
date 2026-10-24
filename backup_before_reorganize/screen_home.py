"""screen_home.py - the startup menu (home screen) (Member 5)."""
from tkinter import ttk


class HomeScreen(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=30)
        self.app = app
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Digital Patient Management System",
                  style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text=f"Welcome, {self.app.user['username']} ({self.app.user['role']})"
                             "  |  Choose what you want to do",
                  style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 20))

        cards = ttk.Frame(self)
        cards.grid(row=2, column=0, sticky="nsew")
        for col in range(3):
            cards.columnconfigure(col, weight=1, uniform="card")
        for i, (key, label, description) in enumerate(self.app.nav_cards):
            ttk.Button(cards, text=f"{label}\n{description}", style="Card.TButton",
                       command=lambda k=key: self.app.show(k)).grid(
                row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")

        ttk.Button(self, text="Exit", command=self.app.quit_app).grid(
            row=3, column=0, sticky="e", pady=(20, 0))