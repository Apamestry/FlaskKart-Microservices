from flask import Blueprint, render_template, redirect, url_for, flash

from app.utils.api_client import api_get, GatewayUnavailable, SessionExpired
from app.utils.decorators import login_required_frontend

order_bp = Blueprint("order", __name__, url_prefix="/orders")


@order_bp.route("/")
@login_required_frontend
def history():
    try:
        resp = api_get("/buy/orders")
    except GatewayUnavailable:
        flash("Unable to reach the order service right now.", "danger")
        return render_template("orders/history.html", orders=[])
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    return render_template("orders/history.html", orders=resp.json())


@order_bp.route("/<int:order_id>")
@login_required_frontend
def detail(order_id):
    try:
        resp = api_get(f"/buy/orders/{order_id}")
    except GatewayUnavailable:
        flash("Unable to reach the order service right now.", "danger")
        return redirect(url_for("order.history"))
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    if resp.status_code != 200:
        flash("Order not found.", "warning")
        return redirect(url_for("order.history"))

    return render_template("orders/detail.html", order=resp.json())