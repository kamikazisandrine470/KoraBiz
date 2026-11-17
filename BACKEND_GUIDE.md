# KoraBiz backend guide

The backend already lives in the `app/` package. Do not create a second `backend/` folder:
- `app/__init__.py` creates the Flask application and registers routes.
- `app/auth.py` handles login, logout, password hashing, owner/attendant roles and account creation commands.
- `app/shop.py` handles dashboard, products, stock-in, sales, expenses and reports.
- `app/db.py` opens and closes SQLite connections and initializes the schema.
- `app/schema.sql` defines the database tables and constraints.
- `app/templates/` contains the HTML pages.
- `app/static/style.css` contains the website design.
- `run.py` starts the application.

## First run on Windows PowerShell

From the folder containing `run.py`:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app run.py init-db
python -m flask --app run.py create-owner
python run.py
```

Then visit http://127.0.0.1:5000/login.

The Owner creation command asks for a username, full name and password. Use a password of at least 8 characters. Do not share it or commit it to GitHub.

## Important
This is a school-project development version. Before real business use, add CSRF protection, secure production cookie settings, database backups, audit review and independent security testing.
