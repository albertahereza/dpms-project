"""
report_button.py - NEW FEATURE glue: the "Generate Medical Report" button and its dialogs.

A screen only needs to call add_generate_report_button(...) from its add_extra_buttons().
Everything else (permission check, save dialog, success or error message) happens here.
"""
from tkinter import filedialog, ttk

from core import auth
from reporting import patient_report
from ui.ui_common import friendly, show_error, show_info

BUTTON_TEXT = "Generate Medical Report"


def export_patient_report(screen, patient_id):
    """Fetch the data, ask where to save, write the PDF, and tell the user what happened."""
    user = screen.app.user
    if not auth.can_open(user["role"], "records"):          # same permission as the Medical Records screen
        show_error("Your role is not allowed to generate medical reports.")
        return

    try:
        data = patient_report.fetch_patient_report_data(int(patient_id))
    except Exception as e:
        show_error(friendly(e))
        return
    if data is None:
        show_error("That patient no longer exists.")
        return

    path = filedialog.asksaveasfilename(
        parent=screen,
        title="Save medical report",
        defaultextension=".pdf",
        initialfile=patient_report.default_filename(data),
        filetypes=[("PDF document", "*.pdf")])
    if not path:                                            # the user pressed Cancel
        return

    try:
        protected = patient_report.write_patient_report_pdf(data, path, generated_by=user["username"])
    except ImportError:
        show_error("The PDF library is not installed.\n\nOpen the terminal and run:\n"
                   "python -m pip install fpdf2")
    except OSError as e:                                    # folder missing, no permission, file open elsewhere
        show_error("The file could not be saved there. Choose another folder, or close the "
                   f"file if it is open in a PDF viewer.\n\nDetails: {e}")
    except Exception as e:
        show_error(friendly(e))
    else:
        note = "" if protected else "\n\n(The PDF was saved, but it could not be locked as read-only.)"
        show_info(f"Medical report saved successfully:\n{path}{note}", "Report saved")


def add_generate_report_button(bar, screen, get_patient_id):
    """
    Put the button on a screen's button bar.
      bar            the frame given to add_extra_buttons(self, bar)
      screen         the screen itself (it has .app.user)
      get_patient_id a function returning the selected patient's id, or None if nothing is selected
    The button is not created for roles that may not open Medical Records (for example Receptionist).
    """
    if not auth.can_open(screen.app.user["role"], "records"):
        return None

    def on_click():
        patient_id = get_patient_id()
        if patient_id is None:
            show_error("Click a row in the table first, then press " + BUTTON_TEXT + ".")
            return
        export_patient_report(screen, patient_id)

    button = ttk.Button(bar, text=BUTTON_TEXT, command=on_click)
    button.pack(side="left", padx=(12, 6))
    return button