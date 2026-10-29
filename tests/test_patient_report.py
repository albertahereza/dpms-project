"""
test_patient_report.py - checks the new Generate Medical Report feature (needs fpdf2).
Run from inside the dpms_app folder:   python -m tests.test_patient_report
It only READS the database and writes PDFs into a temporary folder that is deleted afterwards.
"""
import tempfile
from pathlib import Path

from reporting import patient_report

failures = 0


def check(label, condition, detail=""):
    global failures
    print(("PASS  " if condition else "FAIL  ") + label + (f"   {detail}" if detail else ""))
    if not condition:
        failures += 1


def main():
    print("=== DPMS: Generate Medical Report test ===\n")
    with tempfile.TemporaryDirectory() as folder:
        # a patient with a medical record and prescriptions (Mary Natu, patient 1 in the sample data)
        data = patient_report.fetch_patient_report_data(1)
        check("patient 1 is found", data is not None)
        if data:
            check("the query returns the visit(s) with a record", len(data["visits"]) >= 1,
                  f"{len(data['visits'])} visit(s)")
            check("prescriptions are grouped under their visit",
                  any(v["prescriptions"] for v in data["visits"]))
            check("no password data is in the result", "password" not in str(data).lower())
            path = Path(folder) / patient_report.default_filename(data)
            result = patient_report.generate_patient_report(1, str(path), generated_by="test")
            check("generate_patient_report saves a file", path.exists() and result is not None)
            check("the file is a real PDF", path.exists() and path.read_bytes()[:5] == b"%PDF-")
            check("the PDF is not empty", path.exists() and path.stat().st_size > 1500,
                  f"{path.stat().st_size if path.exists() else 0} bytes")
            print("        protected (read-only):", result and result["protected"])

        # a patient with no appointments at all (Charles Mugabi, patient 20)
        empty = Path(folder) / "empty.pdf"
        result = patient_report.generate_patient_report(20, str(empty))
        check("a patient with no records still gets a PDF", empty.exists() and result["visits"] == 0)

        # a patient that does not exist
        check("an unknown patient returns None", patient_report.fetch_patient_report_data(999999) is None)
    print("\nFAILED TESTS:", failures if failures else "none  -> the report feature works")


if __name__ == "__main__":
    main()