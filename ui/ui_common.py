
"""
ui_common.py - shared look and the reusable CrudScreen base class (Member 5).

Every data screen (patients, appointments, ...) is a small subclass of CrudScreen.
CrudScreen draws the form, the buttons and the table. A subclass only says
WHICH fields and columns it has. The four "hook" methods that talk to the
database modules (load_rows, create_row, update_row, delete_row) are filled in
during Step 11. Until then the screens open and look right but say
"not connected yet".
"""
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import messagebox, ttk

BG = "#F4F6F9"
SIDEBAR = "#1F3A5F"
ACCENT = "#2E7D6B"
DANGER = "#B3261E"
TEXT = "#1B2430"


# ---------------------------------------------------------------- look and feel
def apply_style(root):
    """Set colours and fonts for every ttk widget in the program."""
    root.configure(bg=BG)
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", font=("Segoe UI", 10), background=BG, foreground=TEXT)
    s.configure("TFrame", background=BG)
    s.configure("TLabel", background=BG)
    s.configure("TLabelframe", background=BG)
    s.configure("TLabelframe.Label", background=BG, foreground=SIDEBAR,
                font=("Segoe UI", 10, "bold"))
    s.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground=SIDEBAR)
    s.configure("Sub.TLabel", foreground="#5B6573")
    s.configure("Status.TLabel", foreground="#5B6573")
    s.configure("Error.TLabel", foreground=DANGER)
    s.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
    s.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#DDE3EC")
    s.configure("TButton", padding=6)
    s.configure("Accent.TButton", background=ACCENT, foreground="white")
    s.map("Accent.TButton", background=[("active", "#256B5B")])
    s.configure("Danger.TButton", background=DANGER, foreground="white")
    s.map("Danger.TButton", background=[("active", "#8E1F19")])
    s.configure("Sidebar.TFrame", background=SIDEBAR)
    s.configure("Sidebar.TLabel", background=SIDEBAR, foreground="white")
    s.configure("Nav.TButton", background=SIDEBAR, foreground="white",
                anchor="w", padding=(16, 10), borderwidth=0)
    s.map("Nav.TButton", background=[("active", "#2E5183")])
    s.configure("Card.TButton", font=("Segoe UI", 11, "bold"), padding=20)


# ---------------------------------------------------------------- message boxes
def show_error(message):
    messagebox.showerror("DPMS", message)


def show_info(message, title="DPMS"):
    messagebox.showinfo(title, message)


def ask_yes_no(message):
    return messagebox.askyesno("DPMS", message)


def friendly(exc):
    """Turn any error into text a user can read (uses db.explain_error for database errors)."""
    if isinstance(exc, ValueError):
        return str(exc)
    try:
        from core.db import explain_error
        return explain_error(exc)
    except Exception:
        return str(exc)


def choice(item_id, label):
    """Build a combo box item such as '3 - Grace Atim'."""
    return f"{item_id} - {label}"


def choice_id(text):
    """Combo box items look like '3 - Grace Atim'. This returns the '3'."""
    return text.split(" - ")[0].strip() if text else ""


def choice_int(text, label):
    """The ID of a chosen combo item as a number. Raises a clear error if nothing is chosen."""
    value = choice_id(text)
    if not value:
        raise ValueError(f"{label} is required.")
    return int(value)


# ---------------------------------------------------------------- descriptions
@dataclass
class Field:
    """One input on the form."""
    key: str                       # matches the database column / module argument name
    label: str                     # text shown beside the input
    kind: str = "entry"            # entry | combo | text | readonly | password
    values: list = field(default_factory=list)   # choices for a combo box
    required: bool = False


@dataclass
class Column:
    """One column of the table."""
    key: str
    heading: str
    width: int = 120


# ---------------------------------------------------------------- the base screen
class CrudScreen(ttk.Frame):
    """A form + buttons + table screen. Subclasses fill in the class variables below."""

    title = "Screen"
    subtitle = ""
    fields = []              # list of Field
    columns = []             # list of Column
    id_key = ""              # key of the readonly ID field
    searchable = False       # show a search box?
    can_delete = True        # show the Delete button?
    defaults = {}            # starting values after Clear, e.g. {"appointment_status": "Scheduled"}

    def __init__(self, parent, app):
        super().__init__(parent, padding=14)
        self.app = app
        self.vars = {}             # field key -> StringVar
        self.inputs = {}           # field key -> widget
        self.rows = []             # rows currently in the table (list of dicts)
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self._build()
        self.clear_form()

    # ------------------------------------------------------------ building the screen
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)          # the table row stretches
        ttk.Label(self, text=self.title, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text=self.subtitle, style="Sub.TLabel").grid(
            row=1, column=0, sticky="w", pady=(0, 8))
        self._build_form().grid(row=2, column=0, sticky="ew")
        self._build_buttons().grid(row=3, column=0, sticky="ew", pady=8)
        self._build_table().grid(row=4, column=0, sticky="nsew")
        ttk.Label(self, textvariable=self.status_var, style="Status.TLabel").grid(
            row=5, column=0, sticky="w", pady=(6, 0))

    def _label(self, f):
        return f.label + (" *" if f.required else "")

    def _build_form(self):
        box = ttk.LabelFrame(self, text="Details  (* = required)", padding=10)
        box.columnconfigure(1, weight=1)
        box.columnconfigure(3, weight=1)
        row, col = 0, 0
        for f in self.fields:
            if f.kind == "text":                       # a big multi-line box on its own row
                if col != 0:
                    row, col = row + 1, 0
                ttk.Label(box, text=self._label(f)).grid(
                    row=row, column=0, sticky="nw", padx=(0, 8), pady=4)
                widget = tk.Text(box, height=3, width=60, wrap="word",
                                 font=("Segoe UI", 10), relief="solid", borderwidth=1)
                widget.grid(row=row, column=1, columnspan=3, sticky="ew", pady=4)
                row += 1
            else:                                      # two inputs per row
                self.vars[f.key] = tk.StringVar()
                ttk.Label(box, text=self._label(f)).grid(
                    row=row, column=col, sticky="w", padx=(0, 8), pady=4)
                widget = self._make_input(box, f)
                widget.grid(row=row, column=col + 1, sticky="ew", padx=(0, 18), pady=4)
                col += 2
                if col == 4:
                    row, col = row + 1, 0
            self.inputs[f.key] = widget
        return box

    def _make_input(self, parent, f):
        var = self.vars[f.key]
        if f.kind == "combo":
            return ttk.Combobox(parent, textvariable=var, values=f.values,
                                state="readonly", width=30)
        if f.kind == "readonly":
            return ttk.Entry(parent, textvariable=var, state="readonly", width=32)
        if f.kind == "password":
            return ttk.Entry(parent, textvariable=var, show="*", width=32)
        return ttk.Entry(parent, textvariable=var, width=32)

    def _build_buttons(self):
        bar = ttk.Frame(self)
        ttk.Button(bar, text="Add New", style="Accent.TButton",
                   command=self.on_add).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Update Selected", command=self.on_update).pack(side="left", padx=(0, 6))
        if self.can_delete:
            ttk.Button(bar, text="Delete Selected", style="Danger.TButton",
                       command=self.on_delete).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Clear Form", command=self.clear_form).pack(side="left", padx=(0, 6))
        self.add_extra_buttons(bar)
        if self.searchable:
            ttk.Button(bar, text="Show All", command=self.on_show_all).pack(side="right")
            ttk.Button(bar, text="Search", command=self.refresh).pack(side="right", padx=6)
            entry = ttk.Entry(bar, textvariable=self.search_var, width=26)
            entry.pack(side="right")
            entry.bind("<Return>", lambda _e: self.refresh())
            ttk.Label(bar, text="Search:").pack(side="right", padx=(0, 6))
        return bar

    def add_extra_buttons(self, bar):
        """Subclasses may add more buttons to the button bar."""

    def _build_table(self):
        frame = ttk.Frame(self)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(frame, columns=[c.key for c in self.columns],
                                 show="headings", selectmode="browse")
        for c in self.columns:
            self.tree.heading(c.key, text=c.heading)
            self.tree.column(c.key, width=c.width, anchor="w")
        ysb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        return frame

    # ------------------------------------------------------------ reading and writing the form
    def get_values(self):
        """All form values as a dictionary of text, e.g. {'name': 'Mary Natu', ...}."""
        out = {}
        for f in self.fields:
            if f.kind == "text":
                out[f.key] = self.inputs[f.key].get("1.0", "end").strip()
            else:
                out[f.key] = self.vars[f.key].get().strip()
        return out

    def set_values(self, values):
        """Fill the form from a dictionary (missing keys become empty)."""
        for f in self.fields:
            text = values.get(f.key)
            text = "" if text is None else str(text)
            if f.kind == "text":
                self.inputs[f.key].delete("1.0", "end")
                self.inputs[f.key].insert("1.0", text)
            else:
                self.vars[f.key].set(text)

    def set_choices(self, key, items):
        """Fill a combo box, e.g. set_choices('patient', ['1 - Mary Natu', ...])."""
        self.inputs[key]["values"] = items

    def clear_form(self):
        self.set_values(self.defaults)
        selected = self.tree.selection() if hasattr(self, "tree") else ()
        if selected:
            self.tree.selection_remove(*selected)

    def form_values_from_row(self, row):
        """Turn a table row into form values. Subclasses override this when they differ."""
        return row

    def check_required(self, values):
        for f in self.fields:
            if f.required and not values.get(f.key):
                return f"{f.label} is required."
        return None

    # ------------------------------------------------------------ table
    def show_value(self, value):
        return "" if value is None else str(value)

    def refresh(self):
        """Reload the table from the database."""
        message = None
        try:
            self.rows = self.load_rows(self.search_var.get().strip())
            message = f"{len(self.rows)} record(s) shown."
        except NotImplementedError:
            self.rows = []
            message = "Not connected to the database yet (this is done in Step 11)."
        except Exception as e:
            self.rows = []
            message = "Could not load the data."
            show_error(friendly(e))
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, row in enumerate(self.rows):
            self.tree.insert("", "end", iid=str(i),
                             values=[self.show_value(row.get(c.key)) for c in self.columns])
        self.status_var.set(message)

    def on_show(self):
        """Called by main.py each time the screen is opened."""
        try:
            self.load_choices()
        except Exception as e:
            self.rows = []
            self.status_var.set("Could not reach the database.")
            show_error(friendly(e))
            return
        self.refresh()

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if selected:
            self.set_values(self.form_values_from_row(self.rows[int(selected[0])]))

    def on_show_all(self):
        self.search_var.set("")
        self.refresh()

    # ------------------------------------------------------------ button handlers
    def selected_id(self):
        return self.vars[self.id_key].get().strip()

    def not_connected(self):
        show_info("This button will work after Step 11 connects this screen "
                  "to its database module.", "Not connected yet")

    def finish(self, message):
        """After a successful change: clear the form, reload choices and the table, show a message."""
        self.clear_form()
        try:
            self.load_choices()
        except Exception:
            pass                      # refresh() below reports any database problem
        self.refresh()
        self.status_var.set(message)

    def on_add(self):
        values = self.get_values()
        problem = self.check_required(values)
        if problem:
            show_error(problem)
            return
        try:
            self.create_row(values)
        except NotImplementedError:
            self.not_connected()
            return
        except Exception as e:
            show_error(friendly(e))
            return
        self.finish("Record added.")

    def on_update(self):
        values = self.get_values()
        row_id = self.selected_id()
        if not row_id:
            show_error("Click a row in the table first, then change the details.")
            return
        problem = self.check_required(values)
        if problem:
            show_error(problem)
            return
        try:
            self.update_row(row_id, values)
        except NotImplementedError:
            self.not_connected()
            return
        except Exception as e:
            show_error(friendly(e))
            return
        self.finish("Record updated.")

    def on_delete(self):
        row_id = self.selected_id()
        if not row_id:
            show_error("Click a row in the table first.")
            return
        if not ask_yes_no("Delete the selected record? This cannot be undone."):
            return
        try:
            self.delete_row(row_id)
        except NotImplementedError:
            self.not_connected()
            return
        except Exception as e:
            show_error(friendly(e))
            return
        self.finish("Record deleted.")

    # ------------------------------------------------------------ hooks (Step 11)
    def load_choices(self):
        """Fill the combo boxes (patients, doctors, ...). Most screens do not need it."""

    def load_rows(self, search_text):
        """Return a list of dictionaries for the table."""
        raise NotImplementedError

    def create_row(self, values):
        raise NotImplementedError

    def update_row(self, row_id, values):
        raise NotImplementedError

    def delete_row(self, row_id):
        raise NotImplementedError