from functools import wraps

from flask import session, redirect, url_for, flash, request


def login_required_frontend(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("token"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated