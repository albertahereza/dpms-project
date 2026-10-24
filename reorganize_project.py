"""
reorganize_project.py - ONE-TIME tidy-up of the dpms_app folder (Group 7).

It does three things and nothing else:
  1. MOVES each Python file into a folder for its job.
  2. REWRITES the import lines so every file can still find the others.
  3. CHECKS that every import points at a file that exists.
The code inside the files (and your own config.py password) is not touched.

Run it from inside the dpms_app folder, with the application CLOSED:
    python reorganize_project.py --dry-run     (only shows what it would do)
    python reorganize_project.py               (asks, then does it)
    python reorganize_project.py --undo        (puts everything back from the backup)
"""
import ast
import re
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
BACKUP = ROOT / "backup_before_reorganize"

# folder -> the modules (file names without .py) that belong in it
PACKAGES = {
    "core": ["config", "db", "helpers", "auth"],
    "db_modules": ["users_db", "doctor_db", "patient_db", "appointment_db",
                   "medical_record_db", "prescription_db", "payment_db"],
    "ui": ["ui_common", "login_window"],
    "screens": ["screen_home", "screen_patients", "screen_appointments", "screen_records",
                "screen_prescriptions", "screen_payments", "screen_doctors",
                "screen_users", "screen_reports"],
    "reporting": ["report_db", "reports"],
    "tests": ["test_connection", "test_modules", "test_full_flow"],
}
PACKAGE_OF = {mod: pkg for pkg, mods in PACKAGES.items() for mod in mods}
SKIP_DIRS = {"venv", ".venv", "__pycache__", BACKUP.name, ".git"}

FROM_RE = re.compile(r"^(\s*)from\s+(\w+)\s+import\s+(.*)$")
PLAIN_RE = re.compile(r"^(\s*)import\s+([\w\s,]+?)\s*$")


def python_files():
    """Every .py file in the project (root and the new folders), without venv or backups."""
    found = []
    for path in ROOT.rglob("*.py"):
        parts = set(path.relative_to(ROOT).parts[:-1])
        if parts & SKIP_DIRS or path.name == Path(__file__).name:
            continue
        found.append(path)
    return sorted(found)


# ---------------------------------------------------------------- rewriting imports
def rewrite_line(line):
    """Return the new text for one line (unchanged if it is not a project import)."""
    ending = "\n" if line.endswith("\n") else ""
    text = line.rstrip("\n")

    m = FROM_RE.match(text)
    if m:
        indent, module, rest = m.groups()
        if module in PACKAGE_OF:
            return f"{indent}from {PACKAGE_OF[module]}.{module} import {rest}{ending}"
        return line

    m = PLAIN_RE.match(text)
    if m and " as " not in text:
        indent, names_text = m.groups()
        names = [n.strip() for n in names_text.split(",") if n.strip()]
        project = [n for n in names if n in PACKAGE_OF]
        if not project:
            return line
        others = [n for n in names if n not in PACKAGE_OF]
        grouped = {}
        for n in project:                              # keep the original order, grouped by folder
            grouped.setdefault(PACKAGE_OF[n], []).append(n)
        lines = []
        if others:
            lines.append(f"{indent}import {', '.join(others)}")
        for pkg, mods in grouped.items():
            lines.append(f"{indent}from {pkg} import {', '.join(mods)}")
        return "\n".join(lines) + ending
    return line


def rewrite_file(path):
    old = path.read_text(encoding="utf-8")
    new = "".join(rewrite_line(l) for l in old.splitlines(keepends=True))
    if path.parent.name == "tests":                    # run commands change for the test files
        new = re.sub(r"python (test_\w+)\.py", r"python -m tests.\1", new)
    if new != old:
        path.write_text(new, encoding="utf-8")
        return True
    return False


# ---------------------------------------------------------------- the three actions
def plan():
    moves = []
    for module, pkg in PACKAGE_OF.items():
        src = ROOT / f"{module}.py"
        if src.exists():
            moves.append((src, ROOT / pkg / f"{module}.py"))
    return moves


def verify():
    problems = []
    for path in python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as e:
            problems.append(f"{path.name}: does not compile (line {e.lineno}: {e.msg})")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                if node.module in PACKAGE_OF:
                    problems.append(f"{path.name}: old-style import 'from {node.module} import ...'")
                elif top in PACKAGES:
                    if "." in node.module:
                        target = ROOT / top / (node.module.split(".")[1] + ".py")
                        if not target.exists():
                            problems.append(f"{path.name}: {node.module} does not exist")
                    else:
                        for alias in node.names:
                            if not (ROOT / top / f"{alias.name}.py").exists():
                                problems.append(f"{path.name}: {top}/{alias.name}.py does not exist")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in PACKAGE_OF:
                        problems.append(f"{path.name}: old-style 'import {alias.name}'")
    return problems


def apply(assume_yes):
    moves = plan()
    if not moves:
        print("Nothing to move: the project already looks organised.")
        return
    print("Files that will be moved:")
    for src, dst in moves:
        print(f"  {src.name:28} -> {dst.parent.name}/")
    left = sorted(p.name for p in ROOT.glob("*.py")
                  if p.name not in {s.name for s, _ in moves} | {"main.py", Path(__file__).name})
    if left:
        print("Other .py files stay in this folder (their imports will still be updated):", ", ".join(left))
    if not assume_yes and input("\nType yes to continue: ").strip().lower() != "yes":
        print("Cancelled. Nothing was changed.")
        return

    BACKUP.mkdir(exist_ok=True)                        # 1. safety copy of every root file
    for item in ROOT.iterdir():
        if item.is_file() and item.suffix in {".py", ".txt", ".csv"} and item.name != Path(__file__).name:
            shutil.copy2(item, BACKUP / item.name)
    print(f"\nBackup saved in: {BACKUP.name}/")

    for pkg in PACKAGES:                               # 2. folders and __init__.py files
        (ROOT / pkg).mkdir(exist_ok=True)
        init = ROOT / pkg / "__init__.py"
        if not init.exists():
            init.write_text(f'"""{pkg} package of the DPMS application."""\n', encoding="utf-8")
    for src, dst in moves:                             # 3. move the files
        if dst.exists():
            print(f"  skipped {src.name}: {dst} already exists")
            continue
        shutil.move(str(src), str(dst))

    changed = [p.name for p in python_files() if rewrite_file(p)]   # 4. fix the imports
    print(f"Import lines updated in {len(changed)} file(s).")

    problems = verify()                                # 5. check everything
    if problems:
        print("\nPROBLEMS FOUND (send these to your tutor, or run --undo):")
        for p in problems:
            print("  -", p)
    else:
        print("\nCheck passed: every file compiles and every import points to a real file.")
        print("Start the app as before:   python main.py")


def undo():
    if not BACKUP.exists():
        print("No backup folder found. Nothing to undo.")
        return
    for item in BACKUP.iterdir():
        shutil.copy2(item, ROOT / item.name)
    for pkg, mods in PACKAGES.items():
        folder = ROOT / pkg
        if not folder.exists():
            continue
        for mod in mods:
            (folder / f"{mod}.py").unlink(missing_ok=True)
        (folder / "__init__.py").unlink(missing_ok=True)
        shutil.rmtree(folder / "__pycache__", ignore_errors=True)
        try:
            folder.rmdir()
        except OSError:
            print(f"Folder {pkg}/ still holds other files, so it was kept.")
    print("Restored the original flat layout from the backup.")


if __name__ == "__main__":
    if not (ROOT / "main.py").exists() and not (BACKUP.exists() and "--undo" in sys.argv):
        sys.exit("Run this from inside the dpms_app folder (the one that contains main.py).")
    if "--undo" in sys.argv:
        undo()
    elif "--dry-run" in sys.argv:
        for src, dst in plan():
            print(f"would move {src.name} -> {dst.parent.name}/")
        print("Dry run only. Nothing was changed.")
    else:
        apply("--yes" in sys.argv)