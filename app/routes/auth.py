"""Authentication routes supporting basic email login, logout, and registration."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User, UserSettings

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login using email and password credentials."""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template("login.html")

        user = User.query.filter_by(email=email).one_or_none()
        if not user:
            flash("Account not found. Please register first.", "danger")
            return render_template("login.html")

        if not user.password_hash or not check_password_hash(
            user.password_hash, password
        ):
            flash("Incorrect email or password.", "danger")
            return render_template("login.html")

        UserSettings.ensure_for_user(user)
        login_user(user)
        flash("Welcome back!", "success")
        return redirect(url_for("main.index"))

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Allow new users to create accounts with hashed passwords."""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        existing_user = User.query.filter_by(email=email).one_or_none()
        if existing_user:
            flash("An account with that email already exists.", "danger")
            return render_template("register.html")

        user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        UserSettings.ensure_for_user(user)
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
