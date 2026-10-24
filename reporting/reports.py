"""
reports.py - the list of reports, their text insights and their charts (Member 5).

This file has no screen code, so it can be tested on its own. Each Report says:
  which query to run, which roles may see it, how to show the table,
  how to draw the chart, and how to write a one-paragraph text insight.
"""
from dataclasses import dataclass
from typing import Callable

from matplotlib.ticker import FuncFormatter, MaxNLocator

from reporting import report_db

TEAL = "#2E7D6B"
NAVY = "#1F3A5F"
PALETTE = ["#2E7D6B", "#1F3A5F", "#D98E04", "#B3261E", "#6C5CE7", "#5B6573"]


# ---------------------------------------------------------------- formatting
def fmt_money(value):
    return f"{float(value):,.2f}"


def fmt_value(value, kind):
    """Text shown in the table for a value of the given kind: text | int | money."""
    if value is None:
        return ""
    if kind == "money":
        return fmt_money(value)
    if kind == "int":
        return f"{int(value):,}"
    return str(value)


def pct(part, whole):
    return 0.0 if not whole else round(100.0 * float(part) / float(whole), 1)


# ---------------------------------------------------------------- text insights
def insight_appointments_per_doctor(rows):
    total = sum(r["appointments"] for r in rows)
    if not rows or total == 0:
        return "No appointments have been booked yet."
    top, low = rows[0], rows[-1]
    return (f"{total} appointments are booked in total. {top['doctor']} has the most "
            f"({top['appointments']}, {pct(top['appointments'], total)}% of all appointments). "
            f"{low['doctor']} has the fewest ({low['appointments']}).")


def insight_appointments_by_status(rows):
    total = sum(r["total"] for r in rows)
    if not rows or total == 0:
        return "No appointments have been booked yet."
    top = rows[0]
    text = (f"{top['status']} is the most common status: {top['total']} of {total} "
            f"appointments ({pct(top['total'], total)}%).")
    cancelled = sum(r["total"] for r in rows if r["status"] == "Cancelled")
    text += f" The cancellation rate is {pct(cancelled, total)}%."
    return text


def insight_revenue_per_month(rows):
    total = sum(float(r["revenue"]) for r in rows)
    if not rows or total == 0:
        return "No payments have been recorded yet."
    best = max(rows, key=lambda r: float(r["revenue"]))
    return (f"Total revenue is UGX {fmt_money(total)} across {len(rows)} month(s). "
            f"The best month is {best['month']} with UGX {fmt_money(best['revenue'])} "
            f"({pct(best['revenue'], total)}% of the total).")


def insight_revenue_by_method(rows):
    total = sum(float(r["revenue"]) for r in rows)
    if not rows or total == 0:
        return "No payments have been recorded yet."
    top = rows[0]
    return (f"{top['method']} brings in the most revenue: UGX {fmt_money(top['revenue'])} "
            f"from {top['payments']} payment(s), {pct(top['revenue'], total)}% of all revenue.")


def insight_top_patients(rows):
    if not rows:
        return "No payments have been recorded yet."
    top = rows[0]
    together = sum(float(r["total_paid"]) for r in rows)
    return (f"{top['patient']} has paid the most: UGX {fmt_money(top['total_paid'])}. "
            f"The {len(rows)} highest-paying patients paid UGX {fmt_money(together)} together.")


def insight_patients_by_gender(rows):
    total = sum(r["patients"] for r in rows)
    if not rows or total == 0:
        return "No patients have been registered yet."
    top = rows[0]
    text = (f"{total} patients are registered. {top['gender']} is the largest group: "
            f"{top['patients']} ({pct(top['patients'], total)}%).")
    unknown = sum(r["patients"] for r in rows if r["gender"] == "Not recorded")
    if unknown:
        text += f" {unknown} patient(s) have no gender recorded."
    return text


def insight_top_diagnoses(rows):
    if not rows:
        return "No diagnoses have been recorded yet."
    top = rows[0]
    if top["cases"] == 1:
        return ("Every diagnosis listed appears only once so far, so no single "
                "condition stands out yet.")
    return (f"The most common diagnosis is {top['diagnosis']} with {top['cases']} cases "
            f"({pct(top['cases'], sum(r['cases'] for r in rows))}% of the diagnoses listed).")


# ---------------------------------------------------------------- the reports
@dataclass
class Report:
    key: str
    title: str
    roles: tuple                    # which roles may open it
    columns: list                   # [(row key, heading, width, kind)]
    fetch: Callable                 # runs the query
    chart: str                      # bar | barh | pie
    label_key: str                  # row key used for the chart labels
    value_key: str                  # row key used for the chart values
    value_kind: str                 # int | money
    value_label: str                # axis text
    insight: Callable               # writes the text insight


REPORTS = [
    Report("appt_doctor", "Appointments per doctor", ("Admin", "Doctor", "Receptionist"),
           [("doctor", "Doctor", 190, "text"), ("appointments", "Appointments", 100, "int")],
           report_db.appointments_per_doctor, "bar", "doctor", "appointments", "int",
           "Number of appointments", insight_appointments_per_doctor),
    Report("appt_status", "Appointments by status", ("Admin", "Doctor", "Receptionist"),
           [("status", "Status", 190, "text"), ("total", "Appointments", 100, "int")],
           report_db.appointments_by_status, "pie", "status", "total", "int",
           "Appointments", insight_appointments_by_status),
    Report("rev_month", "Revenue per month", ("Admin", "Receptionist"),
           [("month", "Month", 90, "text"), ("payments", "Payments", 80, "int"),
            ("revenue", "Revenue (UGX)", 130, "money")],
           report_db.revenue_per_month, "bar", "month", "revenue", "money",
           "Revenue (UGX)", insight_revenue_per_month),
    Report("rev_method", "Revenue by payment method", ("Admin", "Receptionist"),
           [("method", "Method", 120, "text"), ("payments", "Payments", 80, "int"),
            ("revenue", "Revenue (UGX)", 130, "money")],
           report_db.revenue_by_method, "bar", "method", "revenue", "money",
           "Revenue (UGX)", insight_revenue_by_method),
    Report("top_patients", "Top paying patients", ("Admin",),
           [("patient", "Patient", 170, "text"), ("payments", "Payments", 80, "int"),
            ("total_paid", "Total paid (UGX)", 130, "money")],
           report_db.top_patients_by_payment, "barh", "patient", "total_paid", "money",
           "Total paid (UGX)", insight_top_patients),
    Report("gender", "Patients by gender", ("Admin", "Doctor"),
           [("gender", "Gender", 190, "text"), ("patients", "Patients", 100, "int")],
           report_db.patients_by_gender, "pie", "gender", "patients", "int",
           "Patients", insight_patients_by_gender),
    Report("diagnoses", "Most common diagnoses", ("Admin", "Doctor"),
           [("diagnosis", "Diagnosis", 230, "text"), ("cases", "Cases", 70, "int")],
           report_db.top_diagnoses, "barh", "diagnosis", "cases", "int",
           "Number of cases", insight_top_diagnoses),
]


def reports_for_role(role):
    """The reports a user with this role may open."""
    return [r for r in REPORTS if role in r.roles]


# ---------------------------------------------------------------- charts
def draw_chart(figure, report, rows):
    """Draw the report's chart onto a matplotlib Figure (works on screen and when saved as PNG)."""
    figure.clear()
    ax = figure.add_subplot(111)
    if not rows:
        ax.text(0.5, 0.5, "No data to show yet", ha="center", va="center", fontsize=12)
        ax.axis("off")
        return
    labels = [str(r[report.label_key]) for r in rows]
    values = [float(r[report.value_key]) for r in rows]

    def text_for(v):
        return f"{v:,.0f}" if report.value_kind == "money" else f"{int(v)}"

    def tidy_axis(axis):
        """Whole numbers for counts, thousands separators for money."""
        if report.value_kind == "money":
            axis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{v:,.0f}"))
        else:
            axis.set_major_locator(MaxNLocator(integer=True))

    if report.chart == "pie":
        _wedges, _labels, percents = ax.pie(
            values, labels=labels, colors=PALETTE[:len(values)], startangle=90,
            autopct=lambda p: f"{p:.0f}%", wedgeprops={"edgecolor": "white"})
        for p in percents:
            p.set_color("white")
            p.set_fontweight("bold")
        ax.axis("equal")
    elif report.chart == "barh":
        bars = ax.barh(labels, values, color=TEAL)
        ax.invert_yaxis()                                  # biggest on top
        ax.set_xlabel(report.value_label)
        ax.bar_label(bars, labels=[text_for(v) for v in values], padding=3, fontsize=9)
        ax.set_xlim(0, max(values) * 1.18)
        tidy_axis(ax.xaxis)
    else:
        bars = ax.bar(labels, values, color=TEAL)
        ax.set_ylabel(report.value_label)
        ax.bar_label(bars, labels=[text_for(v) for v in values], padding=3, fontsize=9)
        ax.set_ylim(0, max(values) * 1.15)
        tidy_axis(ax.yaxis)
        if len(labels) > 3 or max(len(x) for x in labels) > 12:
            ax.tick_params(axis="x", labelrotation=30)
            for tick in ax.get_xticklabels():
                tick.set_ha("right")
    ax.set_title(report.title, fontsize=12, fontweight="bold", color=NAVY)
    if report.chart != "pie":
        ax.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()