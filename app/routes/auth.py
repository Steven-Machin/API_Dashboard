from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app.extensions import db
from app.models import User, UserSettings

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Simple email-based login for demo purposes."""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if not email:
            flash("Please provide an email address.", "danger")
            return render_template("login.html")

        user = User.query.filter_by(email=email).one_or_none()
        if not user:
            user = User(email=email)
            db.session.add(user)
            db.session.commit()

        UserSettings.ensure_for_user(user)
        login_user(user)
        flash("Welcome back!", "success")
        return redirect(url_for("main.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
