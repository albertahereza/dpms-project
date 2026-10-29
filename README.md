# DPMS - Digital Patient Management System

A clinic system built with **PostgreSQL** (database) and **Python / Tkinter** (application).
It handles patients, doctors, appointments, medical records, prescriptions, payments, login with roles, and reports with charts.

## How this project is shared (read this first)

| What | Where it lives |
|---|---|
| The code and the SQL scripts | **GitHub** (this repository). Everyone gets the same copy. |
| The actual database and its data | **On each person's own computer**, inside their own PostgreSQL. It is **not** on GitHub. |
| pgAdmin | A free tool each person installs. It only lets you *look at* your PostgreSQL. It is **not** sent to anyone. |
| Your PostgreSQL password | **Only in your head and in `core/config_local.py`** on your computer. Never uploaded. |

So every member builds their own database from the SQL scripts, using one command. Nothing else needs to be sent.

---

## First-time setup (about 20 minutes)

### 1. Install these (once)
1. **Python 3.10 or newer** from python.org. On the first screen tick **"Add python.exe to PATH"**. Keep **tcl/tk and IDLE** ticked.
2. **PostgreSQL** (it includes **pgAdmin 4**) from postgresql.org. **Write down the password you choose for the user `postgres`.** Keep the default port `5432`.
3. **Git** from git-scm.com (accept the defaults).
4. **VS Code** from code.visualstudio.com, with its **Python** extension.

### 2. Tell Git who you are (once)
Open **PowerShell** and type (use your own name and your GitHub email):
```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 3. Get the project
Accept the invitation you received by email from GitHub. Then, in PowerShell, go to a normal folder (for example `C:\Projects`, **not OneDrive**) and run:
```
cd C:\Projects
git clone https://github.com/OWNER/REPO-NAME.git
cd REPO-NAME
code .
```
(`OWNER/REPO-NAME` is the address of this repository. Copy it from the green **Code** button on GitHub.)

### 4. Create your Python environment
In the VS Code terminal (**Terminal > New Terminal**):
```
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
You should now see `(venv)` at the start of the line. If PowerShell refuses to run the activate script, run this once and try again:
```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 5. Give the project YOUR password
1. In the folder `core`, copy the file `config_local.example.py` and name the copy **`config_local.py`**.
2. Open `config_local.py` and replace `PUT-YOUR-POSTGRES-PASSWORD-HERE` with your own PostgreSQL password. Save.

This file is ignored by Git, so your password is never uploaded.

### 6. Build your database
```
python setup_database.py
```
This creates the database `dpms_db` on **your** PostgreSQL and fills it with the sample data. You should see `Database ready.` at the end.

### 7. Check that everything works
```
python -m tests.test_connection
python -m tests.test_full_flow
python main.py
```
The full test should end with `41 of 41 tests passed`. Then `main.py` opens the sign-in window.

**Demo logins** (password for all: `Clinic@2026`)

| Username | Role |
|---|---|
| `admin01` | Admin (sees everything) |
| `reception01`, `reception02` | Receptionist |
| `dr.okello`, `dr.nansubuga`, `dr.mugisha`, `dr.achieng`, `dr.kato` | Doctor |

### Optional: look at your database in pgAdmin
Open pgAdmin, right-click **Servers > Register > Server**. Name: anything. Connection tab: Host `localhost`, Port `5432`, Username `postgres`, your password. Then open **Databases > dpms_db**.

---

## Working together (every day)

**The golden rules**
1. **Pull before you start:** `git pull`.
2. **Never work directly on `main`.** Make a branch for each job.
3. **Small changes, clear messages.**
4. **Never upload passwords.** `core/config_local.py` is already ignored. Do not remove it from `.gitignore`.
5. **If the database changes, the change must be a `.sql` file in the `sql` folder.** Changing a table only in pgAdmin changes only *your* computer. Your teammates will not get it.

**The routine for one change**
```
git switch main
git pull
git switch -c fix/short-name-of-your-job
```
...edit the files, test with `python main.py`, then:
```
git status
git add .
git commit -m "Short sentence saying what you changed"
git push -u origin fix/short-name-of-your-job
```
Then on GitHub click **Compare & pull request**, write what you changed, and click **Create pull request**. Ask a teammate to look at it. When they approve, click **Merge pull request**. After that, **everyone** runs:
```
git switch main
git pull
```

**If someone changed the database scripts**, rebuild your local database from the new scripts (this deletes your local data, which is fine for this project):
```
python setup_database.py --reset
```

## Project folders

| Folder | Contents |
|---|---|
| `core/` | Settings, the database connection, login logic |
| `db_modules/` | One Python file per table (add, list, update, delete) |
| `ui/` | Shared interface code and the sign-in window |
| `screens/` | One file per screen |
| `reporting/` | Report queries, insights and charts |
| `tests/` | Automated tests |
| `sql/` | The SQL scripts that build the database |
| `docs/` | ERD, data dictionary, test plan and demo guide |

## Common problems

| Problem | Fix |
|---|---|
| `No password found` | Do step 5: create `core/config_local.py` |
| `password authentication failed` | The password in `config_local.py` is not your PostgreSQL password |
| `connection refused` | PostgreSQL is not running (Windows: Services > postgresql > Start), or the port is not 5432 |
| `ModuleNotFoundError: psycopg2` or `matplotlib` | Activate the venv (step 4) and run the pip command again |
| `No module named 'core'` | Run commands from the main project folder, the one that contains `main.py` |
| `database "dpms_db" already exists` | It is already built. To start again: `python setup_database.py --reset` |
| `git push` is rejected | Someone pushed first. Run `git pull`, then push again |
