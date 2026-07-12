from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.utils.api_client import api_post, GatewayUnavailable

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html", username=username, email=email)

        try:
            resp = api_post("/auth/register", json={
                "username": username, "email": email, "password": password,
            })
        except GatewayUnavailable:
            flash("Unable to reach the server right now. Please try again.", "danger")
            return render_template("auth/register.html", username=username, email=email)

        if resp.status_code == 201:
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("auth.login"))

        errors = resp.json().get("errors", {})
        for field, message in errors.items():
            flash(f"{field.capitalize()}: {message}", "danger")
        return render_template("auth/register.html", username=username, email=email)

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        try:
            resp = api_post("/auth/login", json={"email": email, "password": password})
        except GatewayUnavailable:
            flash("Unable to reach the server right now. Please try again.", "danger")
            return render_template("auth/login.html", email=email)

        if resp.status_code == 200:
            data = resp.json()
            session["token"] = data["token"]
            session["user_id"] = data["user"]["id"]
            session["username"] = data["user"]["username"]

            flash(f"Welcome back, {data['user']['username']}!", "success")

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("main.home"))

        flash("Invalid email or password.", "danger")
        return render_template("auth/login.html", email=email)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for("main.home"))