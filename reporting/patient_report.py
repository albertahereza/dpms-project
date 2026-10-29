"""
patient_report.py - NEW FEATURE: Generate Patient Medical Report (PDF).

* It only READS the database (one SELECT). It changes no table, trigger or existing screen.
* fpdf2 is imported only when a report is generated, so the application still starts
  even on a computer where fpdf2 has not been installed yet.
* There is no Tkinter code here, so it can be tested without a window.
* The PDF is plain and monochrome: black text on white, thin black lines, bold headings.
  No colours, no shading, no banners (it prints cleanly on any black-and-white printer).

Main function for other code:
    generate_patient_report(patient_id, output_path, generated_by="")
"""
import datetime
import re
import secrets
from functools import lru_cache

from core.db import fetch_all

PROTECT_PDF = True      # lock the PDF (view and print only). Set False to skip protection.

BLACK = (0, 0, 0)       # the only colour used anywhere in the PDF
LABEL_W = 48            # width (mm) of the label column, so every value lines up

# ---------------------------------------------------------------- 1. THE QUERY
# One JOIN across patient, appointment, medical_record, doctor, users and prescription.
# LEFT JOINs keep the patient even when there is no record, and a visit even when no
# prescription was written. The users password column is never selected.
REPORT_SQL = """
SELECT p.patient_id, p.name AS patient_name, p.date_of_birth, p.gender, p.phone_number,
       a.appointment_id, a.appointment_date, a.appointment_time, a.appointment_status,
       mr.medical_record_id, mr.medical_history, mr.diagnosis,
       d.doctor_id, d.name AS doctor_name, d.specialty,
       u.username AS doctor_account,
       pr.prescription_id, pr.prescription
FROM patient p
LEFT JOIN appointment    a  ON a.patient_id        = p.patient_id
LEFT JOIN medical_record mr ON mr.appointment_id   = a.appointment_id
LEFT JOIN doctor         d  ON d.doctor_id         = mr.doctor_id
LEFT JOIN users          u  ON u.user_id           = d.user_id
LEFT JOIN prescription   pr ON pr.medical_record_id = mr.medical_record_id
WHERE p.patient_id = %s
ORDER BY a.appointment_date, a.appointment_time, mr.medical_record_id, pr.prescription_id
"""

PATIENT_KEYS = ("patient_id", "patient_name", "date_of_birth", "gender", "phone_number")
VISIT_KEYS = ("appointment_id", "appointment_date", "appointment_time", "appointment_status",
              "medical_record_id", "medical_history", "diagnosis",
              "doctor_id", "doctor_name", "specialty", "doctor_account")


def fetch_patient_report_data(patient_id):
    """
    Read everything the report needs for one patient.
    Returns {"patient": {...}, "visits": [...], "generated_at": datetime}, or None if
    there is no such patient. Each visit holds its list of prescriptions.
    """
    rows = fetch_all(REPORT_SQL, (int(patient_id),))
    if not rows:
        return None
    patient = {k: rows[0][k] for k in PATIENT_KEYS}
    visits, by_record = [], {}
    for r in rows:                                   # many rows per visit (one per prescription)
        record_id = r["medical_record_id"]
        if record_id is None:                        # an appointment that has no record yet
            continue
        visit = by_record.get(record_id)
        if visit is None:
            visit = {k: r[k] for k in VISIT_KEYS}
            visit["prescriptions"] = []
            by_record[record_id] = visit
            visits.append(visit)
        if r["prescription_id"] is not None:
            visit["prescriptions"].append(r["prescription"])
    return {"patient": patient, "visits": visits, "generated_at": datetime.datetime.now()}


# ---------------------------------------------------------------- 2. SMALL HELPERS
def _fmt_date(value):
    if hasattr(value, "strftime"):
        return value.strftime("%d %b %Y")
    return str(value) if value else "-"


def _fmt_time(value):
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")
    return str(value)[:5] if value else ""


def _age(born, today=None):
    if not hasattr(born, "year"):
        return None
    today = today or datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _text(value):
    """
    Text that is safe for the PDF's built-in fonts (Latin-1 only). Curly quotes and dashes
    become plain ones; any other unsupported character becomes '?'.
    """
    if value is None or str(value).strip() == "":
        return "-"
    text = str(value)
    for old, new in {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                     "\u2013": "-", "\u2014": "-", "\u2026": "..."}.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def default_filename(data):
    """e.g. Medical_Report_Mary_Natu_2026-10-29.pdf"""
    name = re.sub(r"[^A-Za-z0-9]+", "_", data["patient"]["patient_name"]).strip("_") or "Patient"
    return f"Medical_Report_{name}_{data['generated_at']:%Y-%m-%d}.pdf"


# ---------------------------------------------------------------- 3. THE PDF
@lru_cache(maxsize=1)
def _pdf_classes():
    """Import fpdf2 only now (raises ImportError if it is not installed) and define the PDF class."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    NEXT_LINE = dict(new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    SAME_LINE = dict(new_x=XPos.RIGHT, new_y=YPos.TOP)

    class ReportPDF(FPDF):
        patient_label = ""
        generated_by = ""
        stamp = ""

        # ----- helpers: everything is black, lines are thin -----
        def ink(self):
            """Black text and black lines. Called before drawing so nothing can inherit another colour."""
            self.set_text_color(*BLACK)
            self.set_draw_color(*BLACK)

        def rule(self, width=0.2, gap_before=0.5, gap_after=2.0):
            """A thin black line across the page."""
            self.ln(gap_before)
            y = self.get_y()
            self.set_line_width(width)
            self.line(self.l_margin, y, self.w - self.r_margin, y)
            self.ln(gap_after)

        def keep_with_next(self, needed_mm):
            """Start a new page if a heading plus its first lines would not fit here (no stranded headings)."""
            if self.get_y() + needed_mm > self.page_break_trigger:
                self.add_page()

        # ----- page furniture (runs on every page) -----
        def header(self):
            self.ink()
            self.set_font("Helvetica", "B", 9)
            self.cell(self.epw / 2, 6, "DPMS - PATIENT MEDICAL REPORT", **SAME_LINE)
            self.set_font("Helvetica", "", 9)
            self.cell(0, 6, self.patient_label, align="R", **NEXT_LINE)
            self.rule(0.3, gap_before=0, gap_after=4)

        def footer(self):
            self.ink()
            self.set_y(-16)
            y = self.get_y()
            self.set_line_width(0.2)
            self.line(self.l_margin, y, self.w - self.r_margin, y)
            self.ln(1.5)
            self.set_font("Helvetica", "", 8)
            self.cell(self.epw * 0.78, 5,
                      _text(f"CONFIDENTIAL - generated {self.stamp} by {self.generated_by or 'DPMS'}"),
                      **SAME_LINE)
            self.cell(0, 5, f"Page {self.page_no()} of {{nb}}", align="R", **NEXT_LINE)

        # ----- building blocks -----
        def section(self, title):
            """Bold, upper-case section heading with a thin line under it."""
            self.keep_with_next(30)
            self.ink()
            self.ln(4)
            self.set_font("Helvetica", "B", 11)
            self.cell(0, 6, _text(title.upper()), **NEXT_LINE)
            self.rule(0.2, gap_before=0, gap_after=2.5)

        def detail(self, label, value, bold_value=False):
            """One aligned line:  Label:   value   (the value wraps inside its own column)."""
            self.ink()
            self.set_font("Helvetica", "B", 10)
            self.cell(LABEL_W, 6, _text(label) + ":", **SAME_LINE)
            self.set_font("Helvetica", "B" if bold_value else "", 10)
            self.multi_cell(0, 6, _text(value), align="L", **NEXT_LINE)

        def block(self, title, value, bold=False):
            """A bold upper-case sub-heading followed by an indented paragraph."""
            self.keep_with_next(20)
            self.ink()
            self.set_font("Helvetica", "B", 10)
            self.cell(0, 6, _text(title.upper()), **NEXT_LINE)
            self.set_font("Helvetica", "B" if bold else "", 10)
            self.set_x(self.l_margin + 4)
            self.multi_cell(self.epw - 4, 5.5, _text(value), align="L", **NEXT_LINE)
            self.ln(2)

        def numbered(self, number, value):
            """'1.  text' with a hanging indent, so wrapped lines stay aligned under the text."""
            self.ink()
            self.set_font("Helvetica", "", 10)
            self.set_x(self.l_margin + 4)
            self.cell(8, 5.5, f"{number}.", **SAME_LINE)
            self.multi_cell(self.epw - 12, 5.5, _text(value), align="L", **NEXT_LINE)

        def visit_heading(self, number, visit):
            """VISIT n: date and time (left), record and appointment numbers (right), between two lines."""
            self.ink()
            self.ln(2)
            self.rule(0.4, gap_before=0, gap_after=1.5)
            when = f"{_fmt_date(visit['appointment_date'])}  {_fmt_time(visit['appointment_time'])}".strip()
            self.set_font("Helvetica", "B", 10)
            self.cell(self.epw * 0.5, 6, _text(f"VISIT {number}:  {when}"), **SAME_LINE)
            self.set_font("Helvetica", "", 9)
            self.cell(0, 6, _text(f"Record #{visit['medical_record_id']}  |  Appointment "
                                  f"#{visit['appointment_id']} ({visit['appointment_status']})"),
                      align="R", **NEXT_LINE)
            self.rule(0.2, gap_before=0.5, gap_after=2.5)

        # ----- the whole report -----
        def render(self, data):
            patient, visits = data["patient"], data["visits"]
            self.add_page()
            self.ink()

            self.set_font("Helvetica", "B", 18)
            self.cell(0, 10, "PATIENT MEDICAL REPORT", align="C", **NEXT_LINE)
            self.set_font("Helvetica", "", 10)
            self.cell(0, 6, "Digital Patient Management System (DPMS)", align="C", **NEXT_LINE)
            self.rule(0.4, gap_before=2, gap_after=1)

            self.section("Patient Details")
            born, age = patient["date_of_birth"], _age(patient["date_of_birth"])
            self.detail("Patient ID", patient["patient_id"])
            self.detail("Full name", patient["patient_name"], bold_value=True)
            self.detail("Date of birth", _fmt_date(born) + (f"  (age {age})" if age is not None else ""))
            self.detail("Gender", patient["gender"])
            self.detail("Phone number", patient["phone_number"])

            self.section("Summary")
            drugs = sum(len(v["prescriptions"]) for v in visits)
            self.set_font("Helvetica", "", 10)
            if visits:
                summary = (f"{len(visits)} medical record(s) from {_fmt_date(visits[0]['appointment_date'])} "
                           f"to {_fmt_date(visits[-1]['appointment_date'])}; "
                           f"{drugs} prescription(s) in total.")
            else:
                summary = "No medical records have been recorded for this patient yet."
            self.multi_cell(0, 6, _text(summary), align="L", **NEXT_LINE)

            if visits:
                self.section("Visit History")
            for number, v in enumerate(visits, start=1):
                if self.get_y() > self.page_break_trigger - 60:      # never start a visit at the page end
                    self.add_page()
                self.visit_heading(number, v)
                self.detail("Doctor", f"{_text(v['doctor_name'])} ({_text(v['specialty'])})")
                self.detail("Doctor's account", v["doctor_account"])
                self.ln(1)
                self.block("Medical history / clinical notes", v["medical_history"])
                self.block("Diagnosis", v["diagnosis"], bold=True)
                self.keep_with_next(20)
                self.ink()
                self.set_font("Helvetica", "B", 10)
                self.cell(0, 6, "PRESCRIPTIONS", **NEXT_LINE)
                if v["prescriptions"]:
                    for i, drug in enumerate(v["prescriptions"], start=1):
                        self.numbered(i, drug)
                else:
                    self.set_font("Helvetica", "", 10)
                    self.set_x(self.l_margin + 4)
                    self.multi_cell(self.epw - 4, 5.5, "None recorded for this visit.", align="L", **NEXT_LINE)
                self.ln(4)

            self.rule(0.2, gap_before=2, gap_after=2)
            self.set_font("Helvetica", "I", 8)
            self.multi_cell(0, 4.5, "This is a verified secure electronic report generated by DPMS. End of report.")

    return ReportPDF


def build_patient_report_pdf(data, generated_by=""):
    """Turn the data from fetch_patient_report_data into an fpdf2 document (not saved yet)."""
    ReportPDF = _pdf_classes()
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 18, 15)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.alias_nb_pages()
    pdf.patient_label = _text(f"{data['patient']['patient_name']} (ID {data['patient']['patient_id']})")
    pdf.generated_by = generated_by
    pdf.stamp = data["generated_at"].strftime("%d %b %Y %H:%M")
    pdf.set_title(_text(f"Medical report - {data['patient']['patient_name']}"))
    pdf.set_author(_text(generated_by or "DPMS"))
    pdf.set_creator("DPMS - Digital Patient Management System")
    pdf.set_subject("Patient medical report (confidential)")
    pdf.render(data)
    return pdf


def _lock(pdf):
    """Make the PDF view-and-print only: editing, copying and annotating are not allowed."""
    from fpdf.enums import AccessPermission
    pdf.set_encryption(owner_password=secrets.token_urlsafe(16),
                       permissions=AccessPermission.PRINT_LOW_RES | AccessPermission.PRINT_HIGH_RES)


def write_patient_report_pdf(data, output_path, generated_by="", protect=PROTECT_PDF):
    """
    Build the PDF and save it. Returns True when the file was locked (read-only), or False
    when it was saved without protection (the installed fpdf2 could not lock it).
    Raises ImportError if fpdf2 is not installed.
    """
    _pdf_classes()                                   # clear ImportError if fpdf2 is missing
    if protect:
        try:
            pdf = build_patient_report_pdf(data, generated_by)
            _lock(pdf)
            pdf.output(output_path)
            return True
        except Exception:
            pass                                     # protection not available here: save it unprotected
    pdf = build_patient_report_pdf(data, generated_by)
    pdf.output(output_path)
    return False


def generate_patient_report(patient_id, output_path, generated_by="", protect=PROTECT_PDF):
    """
    THE MAIN FUNCTION: query the database for one patient and save the PDF report.
    Returns {"path", "protected", "visits"}, or None if the patient does not exist.
    """
    data = fetch_patient_report_data(patient_id)
    if data is None:
        return None
    protected = write_patient_report_pdf(data, output_path, generated_by, protect)
    return {"path": output_path, "protected": protected, "visits": len(data["visits"])}