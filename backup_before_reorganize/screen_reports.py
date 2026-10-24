"""
screen_reports.py - the Reports screen: table + text insight + chart (Member 5).
Which reports appear depends on the signed-in role (see reports.py).
"""
import csv
import tkinter as tk
from tkinter import filedialog, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import reports
from ui_common import friendly, show_error, show_info


class ReportsScreen(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=14)
        self.app = app
        self.available = reports.reports_for_role(app.user["role"])
        self.current = None                     # the Report being shown
        self.rows = []                          # its rows
        self.choice_var = tk.StringVar()
        self.insight_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self._build()

    # ------------------------------------------------------------ layout
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        ttk.Label(self, text="Reports and Charts", style="Title.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Label(self, text="Pick a report. You get a table, a written insight and a chart.",
                  style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 8))

        bar = ttk.Frame(self)
        bar.grid(row=2, column=0, sticky="ew")
        ttk.Label(bar, text="Report:").pack(side="left", padx=(0, 6))
        self.combo = ttk.Combobox(bar, textvariable=self.choice_var, state="readonly", width=38,
                                  values=[r.title for r in self.available])
        self.combo.pack(side="left")
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self.run_report())
        ttk.Button(bar, text="Run report", style="Accent.TButton",
                   command=self.run_report).pack(side="left", padx=8)
        ttk.Button(bar, text="Save chart (PNG)", command=self.save_chart).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Export table (CSV)", command=self.export_csv).pack(side="left")

        box = ttk.LabelFrame(self, text="Key insight", padding=10)
        box.grid(row=3, column=0, sticky="ew", pady=10)
        box.columnconfigure(0, weight=1)
        ttk.Label(box, textvariable=self.insight_var, wraplength=900,
                  justify="left").grid(row=0, column=0, sticky="w")

        body = ttk.Frame(self)
        body.grid(row=4, column=0, sticky="nsew")
        body.columnconfigure(0, weight=2, uniform="body")
        body.columnconfigure(1, weight=3, uniform="body")
        body.rowconfigure(0, weight=1)

        table_frame = ttk.Frame(body)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, show="headings", selectmode="browse")
        ysb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")

        chart_frame = ttk.Frame(body)
        chart_frame.grid(row=0, column=1, sticky="nsew")
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)
        self.figure = Figure(figsize=(5.6, 4.4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        ttk.Label(self, textvariable=self.status_var, style="Status.TLabel").grid(
            row=5, column=0, sticky="w", pady=(6, 0))

    # ------------------------------------------------------------ behaviour
    def on_show(self):
        """Called each time the screen opens: choose the first report if none is chosen, then run it."""
        if not self.available:
            self.status_var.set("Your role has no reports.")
            return
        if not self.choice_var.get():
            self.choice_var.set(self.available[0].title)
        self.run_report()

    def run_report(self):
        report = next((r for r in self.available if r.title == self.choice_var.get()), None)
        if report is None:
            return
        try:
            rows = report.fetch()
        except Exception as e:
            show_error(friendly(e))
            return
        self.current, self.rows = report, rows
        self.fill_table(report, rows)
        self.insight_var.set(report.insight(rows))
        reports.draw_chart(self.figure, report, rows)
        self.canvas.draw()
        self.status_var.set(f"{report.title}: {len(rows)} row(s).")

    def fill_table(self, report, rows):
        self.tree["columns"] = [c[0] for c in report.columns]
        for key, heading, width, kind in report.columns:
            self.tree.heading(key, text=heading)
            self.tree.column(key, width=width, anchor="w" if kind == "text" else "e")
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert("", "end", values=[reports.fmt_value(row[c[0]], c[3])
                                                for c in report.columns])

    def save_chart(self):
        if self.current is None:
            show_error("Run a report first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save chart", defaultextension=".png",
            initialfile=self.current.key + ".png", filetypes=[("PNG image", "*.png")])
        if path:
            self.figure.savefig(path, dpi=150)
            show_info(f"Chart saved to:\n{path}")

    def export_csv(self):
        if self.current is None:
            show_error("Run a report first.")
            return
        path = filedialog.asksaveasfilename(
            title="Export table", defaultextension=".csv",
            initialfile=self.current.key + ".csv", filetypes=[("CSV file", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([c[1] for c in self.current.columns])
            for row in self.rows:
                writer.writerow([row[c[0]] for c in self.current.columns])
        show_info(f"Table exported to:\n{path}")