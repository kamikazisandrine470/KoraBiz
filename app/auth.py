import click
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db

bp = Blueprint("auth", __name__)

def load_logged_in_user():
    uid = session.get("user_id")
    g.user = None
    if uid is not None:
        g.user = get_db().execute(
            "SELECT * FROM users WHERE id=? AND is_active=1", (uid,)
        ).fetchone()
        if g.user is None:
            session.clear()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped

def owner_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        if g.user["role"] != "owner":
            flash("Only the Owner can access that page.", "error")
            return redirect(url_for("shop.dashboard"))
        return view(*args, **kwargs)
    return wrapped

@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("shop.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE username=? AND is_active=1", (username,)
        ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect username or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("shop.dashboard"))
    return render_template("auth/login.html")

@bp.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@bp.cli.command("create-owner")
def create_owner():
    db = get_db()
    exists = db.execute("SELECT id FROM users WHERE role='owner' LIMIT 1").fetchone()
    if exists:
        click.echo("An Owner account already exists.")
        return
    username = click.prompt("Choose an Owner username").strip()
    full_name = click.prompt("Enter the Owner's full name").strip()
    password = click.prompt("Choose a password", hide_input=True, confirmation_prompt=True)
    if not username or not full_name or len(password) < 8:
        raise click.ClickException("Username and full name are required; password must be at least 8 characters.")
    try:
        db.execute(
            "INSERT INTO users(username,full_name,password_hash,role) VALUES(?,?,?,'owner')",
            (username, full_name, generate_password_hash(password)),
        )
        db.commit()
        click.echo("Owner account created successfully.")
    except Exception as exc:
        db.rollback()
        raise click.ClickException(f"Could not create Owner: {exc}")

@bp.cli.command("create-attendant")
def create_attendant():
    db = get_db()
    username = click.prompt("Choose attendant username").strip()
    full_name = click.prompt("Enter attendant full name").strip()
    password = click.prompt("Choose a password", hide_input=True, confirmation_prompt=True)
    if not username or not full_name or len(password) < 8:
        raise click.ClickException("Username and full name are required; password must be at least 8 characters.")
    try:
        db.execute(
            "INSERT INTO users(username,full_name,password_hash,role) VALUES(?,?,?,'attendant')",
            (username, full_name, generate_password_hash(password)),
        )
        db.commit()
        click.echo("Attendant account created successfully.")
    except Exception as exc:
        db.rollback()
        raise click.ClickException(f"Could not create attendant: {exc}")
