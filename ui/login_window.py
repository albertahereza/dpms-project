"""
login_window.py - the sign-in window shown before the application (Member 2).
LoginWindow().run() returns the signed-in user (a dictionary) or None.
"""
import tkinter as tk
from tkinter import messagebox, ttk

from core import auth
from ui.ui_common import apply_style, friendly

MAX_ATTEMPTS = 3


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DPMS - Sign in")
        self.resizable(False, False)
        apply_style(self)
        self.user = None
        self.attempts = 0
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.show_password = tk.BooleanVar(value=False)
        self.message = tk.StringVar()
        self._build()
        self._center(420, 430)
        self.bind("<Return>", lambda _e: self.on_login())
        self.user_entry.focus_set()

    def _build(self):
        frame = ttk.Frame(self, padding=32)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="DPMS", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Digital Patient Management System\nGroup 7",
                  style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 20))

        ttk.Label(frame, text="Username").grid(row=2, column=0, sticky="w")
        self.user_entry = ttk.Entry(frame, textvariable=self.username, width=34)
        self.user_entry.grid(row=3, column=0, sticky="ew", pady=(2, 12))

        ttk.Label(frame, text="Password").grid(row=4, column=0, sticky="w")
        self.pw_entry = ttk.Entry(frame, textvariable=self.password, show="*", width=34)
        self.pw_entry.grid(row=5, column=0, sticky="ew", pady=(2, 6))
        ttk.Checkbutton(frame, text="Show password", variable=self.show_password,
                        command=self.toggle_password).grid(row=6, column=0, sticky="w")

        ttk.Label(frame, textvariable=self.message, style="Error.TLabel",
                  wraplength=340).grid(row=7, column=0, sticky="w", pady=(12, 8))
        ttk.Button(frame, text="Sign in", style="Accent.TButton",
                   command=self.on_login).grid(row=8, column=0, sticky="ew")
        ttk.Button(frame, text="Exit", command=self.destroy).grid(
            row=9, column=0, sticky="ew", pady=(8, 0))

    def _center(self, width, height):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def toggle_password(self):
        self.pw_entry.config(show="" if self.show_password.get() else "*")

    def on_login(self):
        try:
            user = auth.authenticate(self.username.get(), self.password.get())
        except ValueError as e:                  # an empty box
            self.message.set(str(e))
            return
        except Exception as e:                   # the database is unreachable: not a wrong password
            self.message.set(friendly(e))
            return

        if user is None:
            self.attempts += 1
            self.password.set("")
            left = MAX_ATTEMPTS - self.attempts
            if left <= 0:
                messagebox.showerror("DPMS", "Too many failed attempts. The program will close.")
                self.destroy()
                return
            # one message for both cases, so an attacker cannot tell which part was wrong
            self.message.set(f"Wrong username or password. {left} attempt(s) left.")
            self.pw_entry.focus_set()
            return

        self.user = user
        self.destroy()

    def run(self):
        """Show the window and wait. Returns the user, or None if they closed it or failed."""
        self.mainloop()
        return self.user