from flask import Blueprint, render_template, redirect, url_for, flash, request

from app.utils.api_client import api_get, api_post, api_patch, api_delete, GatewayUnavailable, SessionExpired
from app.utils.decorators import login_required_frontend

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


@cart_bp.route("/")
@login_required_frontend
def view_cart():
    try:
        resp = api_get("/cart")
    except GatewayUnavailable:
        flash("Unable to reach the cart service right now.", "danger")
        return render_template("cart/view.html", items=[], total=0)
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    data = resp.json()
    return render_template("cart/view.html", items=data.get("items", []), total=data.get("total", 0))


@cart_bp.route("/add/<int:product_id>", methods=["POST"])
@login_required_frontend
def add_to_cart(product_id):
    quantity = request.form.get("quantity", 1, type=int) or 1

    try:
        resp = api_post("/cart/add", json={"product_id": product_id, "quantity": quantity})
    except GatewayUnavailable:
        flash("Unable to reach the cart service right now.", "danger")
        return redirect(url_for("main.product_detail", product_id=product_id))
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    data = resp.json()
    if resp.status_code == 200:
        if data.get("warning"):
            flash(data["warning"], "warning")
        else:
            flash("Added to cart.", "success")
    else:
        flash(data.get("error", "Could not add to cart."), "danger")

    return redirect(url_for("main.product_detail", product_id=product_id))


@cart_bp.route("/update/<int:item_id>", methods=["POST"])
@login_required_frontend
def update_item(item_id):
    quantity = request.form.get("quantity", 1, type=int)

    try:
        resp = api_patch(f"/cart/items/{item_id}", json={"quantity": quantity})
    except GatewayUnavailable:
        flash("Unable to reach the cart service right now.", "danger")
        return redirect(url_for("cart.view_cart"))
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    if resp.status_code == 200:
        data = resp.json()
        if data.get("warning"):
            flash(data["warning"], "warning")
    else:
        flash(resp.json().get("error", "Could not update cart."), "danger")

    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove/<int:item_id>", methods=["POST"])
@login_required_frontend
def remove_item(item_id):
    try:
        api_delete(f"/cart/items/{item_id}")
    except GatewayUnavailable:
        flash("Unable to reach the cart service right now.", "danger")
        return redirect(url_for("cart.view_cart"))
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    flash("Item removed from cart.", "info")
    return redirect(url_for("cart.view_cart"))