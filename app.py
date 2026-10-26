import os
import re
import secrets
import sqlite3
from datetime import timedelta
from functools import wraps

from flask import (
    Flask, abort, flash, g, jsonify, redirect, render_template,
    request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
    DATABASE=os.path.join(app.instance_path, "devchecks.db"),
    PERMANENT_SESSION_LIFETIME=timedelta(weeks=2),  # "Remember me for 2 weeks"
)
os.makedirs(app.instance_path, exist_ok=True)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT,
            username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
            email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


init_db()


# --------------------------------------------------------------------------
# Security helpers (CSRF + login_required)
# --------------------------------------------------------------------------
@app.context_processor
def inject_globals():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return {"csrf_token": session["_csrf"], "current_user": g.get("user")}


@app.before_request
def load_user_and_check_csrf():
    g.user = None
    uid = session.get("user_id")
    if uid is not None:
        g.user = get_db().execute(
            "SELECT id, name, username, email FROM users WHERE id = ?", (uid,)
        ).fetchone()

    if request.method == "POST":
        expected = session.get("_csrf")
        sent = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        if not expected or not sent or not secrets.compare_digest(expected, sent):
            abort(400, "Invalid or missing CSRF token.")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            if request.path == url_for("chat"):
                return jsonify(error="Please sign in again."), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


# --------------------------------------------------------------------------
# Auth routes
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("dashboard" if g.user else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = get_db().execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email address or password.", "error")
            return render_template("login.html", email=email), 401

        session.clear()
        session["user_id"] = user["id"]
        session.permanent = remember
        return redirect(url_for("dashboard"))  # successful login -> dashboard

    return render_template("login.html", email="")


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard"))

    form = {"name": "", "username": "", "email": ""}

    if request.method == "POST":
        form["name"] = request.form.get("name", "").strip()[:100]
        form["username"] = request.form.get("username", "").strip()
        form["email"] = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not USERNAME_RE.match(form["username"]):
            errors.append("Username must be 1-30 characters: letters, numbers, _ or -.")
        if not EMAIL_RE.match(form["email"]):
            errors.append("Enter a valid email address.")
        if not 8 <= len(password) <= 72:
            errors.append("Password must be between 8 and 72 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if not errors:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (name, username, email, password_hash) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        form["name"] or form["username"],
                        form["username"],
                        form["email"],
                        generate_password_hash(password),
                    ),
                )
                db.commit()
            except sqlite3.IntegrityError:
                errors.append("That username or email address is already in use.")
            else:
                flash("Account created. Sign in to continue.", "success")
                return redirect(url_for("login"))

        for err in errors:
            flash(err, "error")
        return render_template("register.html", form=form), 400

    return render_template("register.html", form=form)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------------------------------------------------------------------------
# Dashboard + chatbot
# --------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# Simple rule-based bot. Replace bot_reply() with a real LLM/API call later.
BOT_RULES = [
    (("hello", "hi", "hey"),
     "Hi {name}! I'm the DevChecks assistant. Ask me about projects, checks or reports."),
    (("check", "scan"),
     "Checks will run against your projects and list findings here. This feature is coming soon."),
    (("report", "bug", "finding"),
     "Findings and reports will show up on your dashboard once checks are connected."),
    (("project",),
     "Projects group your checks together. Project management is coming soon."),
    (("password", "account", "profile"),
     "Account settings will live under your profile menu in a future update."),
    (("help", "what can you do"),
     "I can answer questions about DevChecks. Try asking about checks, projects or reports."),
    (("thanks", "thank you"),
     "You're welcome!"),
]


def bot_reply(message: str, user) -> str:
    text = message.lower()
    name = (user["name"] or user["username"]) if user else "there"
    for keywords, reply in BOT_RULES:
        if any(re.search(r"\b" + re.escape(k) + r"\b", text) for k in keywords):
            return reply.format(name=name)
    return "I'm still learning. Try asking about checks, projects or reports."


@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()[:500]
    if not message:
        return jsonify(error="Message is empty."), 400
    return jsonify(reply=bot_reply(message, g.user))


if __name__ == "__main__":
    app.run(debug=True)
