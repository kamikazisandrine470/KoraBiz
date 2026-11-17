# KoraBiz

KoraBiz is a web-based management system for one small general retail shop in Rwanda.

## Technology

- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python and Flask
- Database: SQLite
- Currency: Rwandan francs (RWF)

## Current progress

The first development stage creates the Flask application structure and SQLite database schema. The login, product, inventory, sales, expense, reporting, and dashboard features will be implemented in later stages.

## Run on Windows

Open PowerShell in this KoraBiz folder.

1. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

2. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Install Flask:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Create the database:

   ```powershell
   flask --app run.py init-db
   ```

5. Start the application:

   ```powershell
   python run.py
   ```

6. Open `http://127.0.0.1:5000` in your browser.

The SQLite database is created automatically in the `instance` folder when you run the database initialization command.

## Important

The development secret key in `app/__init__.py` is only a local placeholder. It must be replaced with a private secret before deployment. Do not commit passwords, secret keys, or the local database file to GitHub.
