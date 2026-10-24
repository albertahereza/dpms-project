"""
test_connection.py - Step 8 check for DPMS (Group 7).
Run from inside the dpms_app folder:   python test_connection.py
"""
import psycopg2

from db import fetch_all, fetch_one, execute, explain_error

EXPECTED = {            # row counts after the Step 5 sample data
    "users": 8, "doctor": 5, "patient": 20, "appointment": 20,
    "medical_record": 14, "prescription": 16, "payment": 20,
}


def count_rows(table):
    # Table names come from the fixed list above, never from user input,
    # so building the text this way is safe. Values always use %s (see Test 3).
    return fetch_one(f"SELECT COUNT(*) AS n FROM {table}")["n"]


def main():
    print("=== DPMS: Python -> PostgreSQL connection test ===\n")

    # Test 1: connect and read basic information
    try:
        info = fetch_one("SELECT version() AS v, current_database() AS db")
    except psycopg2.Error as e:
        print("TEST 1 FAIL  Could not connect.")
        print("  ", explain_error(e))
        print("   Details:", str(e).strip().splitlines()[0])
        return
    print("TEST 1 PASS  Connected to database:", info["db"])
    print("             ", info["v"][:60])

    # Test 2: read every table
    print("\nTEST 2  Row counts")
    for table, expected in EXPECTED.items():
        n = count_rows(table)
        note = "OK" if n == expected else f"(expected {expected}; differs if you added or removed rows)"
        print(f"   {table:<15}{n:>4}   {note}")

    # Test 3: a parameterised query (%s placeholders)
    row = fetch_one("SELECT name, date_of_birth FROM patient WHERE patient_id = %s", (1,))
    print("\nTEST 3  Patient 1 is:", row["name"], "born", row["date_of_birth"])

    hostile = "x'; DROP TABLE patient; --"
    rows = fetch_all("SELECT * FROM patient WHERE name = %s", (hostile,))
    print("        Hostile text found", len(rows), "rows; patient table still has",
          count_rows("patient"), "rows  -> injection blocked")

    # Test 4: a database trigger error caught in Python
    print("\nTEST 4  Trigger rule seen from Python")
    try:
        execute("INSERT INTO patient (name, date_of_birth) VALUES (%s, %s)",
                ("   ", "2000-01-01"))
        print("   FAIL  the blank name was accepted (are the Step 7 triggers installed?)")
    except psycopg2.Error as e:
        print("   PASS  Database refused it:", explain_error(e))
    print("   patient rows after the attempt:", count_rows("patient"))

    print("\nAll tests finished.")


if __name__ == "__main__":
    main()