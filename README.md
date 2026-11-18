# KoraBiz

A beginner-friendly Flask + SQLite retail shop management MVP for one shop in Rwanda.

## Features
- Owner and attendant accounts, hashed passwords, login and logout
- Product and category management
- Stock-in and stock adjustment history
- Sales with server-side totals and stock checks
- Expense recording
- Dashboard and date-based reports
- RWF currency display

## Requirements
- Python 3.10 or newer
- Windows, macOS or Linux

## Windows setup (PowerShell)
Open this folder in VS Code. Choose **Terminal > New Terminal** and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app run.py init-db
python -m flask --app run.py create-owner
python run.py
```

Open http://127.0.0.1:5000

The first Owner account is created by the `create-owner` command. Passwords are hashed.

## GitHub
If this is being copied into your existing KoraBiz repository, first back up the old folder. Copy the contents of this folder into your repository's KoraBiz folder, replacing matching application files but keeping `.git` and `.venv`. Then:

```powershell
git status
git add .
git commit -m "Build KoraBiz retail management MVP"
git push
```

Do not add `.venv`, `instance`, or secrets to Git.

## Important limitations
This is a school-project MVP, not a production-ready financial system. Before public deployment, add CSRF protection, HTTPS, secure cookie settings, backups, stronger audit controls, and independent security testing. Test all workflows with sample data first.


## Built-in help chatbot
The app includes a small rule-based help assistant for common questions about products, stock, sales, expenses, reports and login. It runs locally in Flask, requires no API key or paid service, and does not read or modify shop records. It is not a generative-AI chatbot.
