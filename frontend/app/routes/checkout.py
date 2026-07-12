from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.utils.api_client import api_get, api_post, GatewayUnavailable, SessionExpired
from app.utils.decorators import login_required_frontend

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")

REQUIRED_FIELDS = ["full_name", "address_line1", "city", "state", "zip_code", "phone"]


def _get_cart_or_redirect():
    try:
        resp = api_get("/cart")
    except GatewayUnavailable:
        flash("Unable to reach the cart service right now.", "danger")
        return None, redirect(url_for("cart.view_cart"))
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return None, redirect(url_for("auth.login"))

    data = resp.json()
    if not data.get("items"):
        flash("Your cart is empty. Add something before checking out.", "warning")
        return None, redirect(url_for("cart.view_cart"))

    return data, None


@checkout_bp.route("/shipping", methods=["GET", "POST"])
@login_required_frontend
def shipping():
    cart_data, redirect_resp = _get_cart_or_redirect()
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        data = {field: request.form.get(field, "").strip() for field in REQUIRED_FIELDS}
        data["address_line2"] = request.form.get("address_line2", "").strip()

        missing = [f for f in REQUIRED_FIELDS if not data[f]]
        if missing:
            flash("Please fill in all required shipping fields.", "danger")
            return render_template("checkout/shipping.html", shipping=data)

        session["shipping_info"] = data
        return redirect(url_for("checkout.review"))

    return render_template("checkout/shipping.html", shipping=session.get("shipping_info", {}))


@checkout_bp.route("/review")
@login_required_frontend
def review():
    shipping_info = session.get("shipping_info")
    if not shipping_info:
        flash("Please enter your shipping details first.", "info")
        return redirect(url_for("checkout.shipping"))

    cart_data, redirect_resp = _get_cart_or_redirect()
    if redirect_resp:
        return redirect_resp

    return render_template(
        "checkout/review.html",
        items=cart_data["items"],
        total=cart_data["total"],
        shipping=shipping_info,
    )


@checkout_bp.route("/place-order", methods=["POST"])
@login_required_frontend
def place_order():
    shipping_info = session.get("shipping_info")
    if not shipping_info:
        flash("Please enter your shipping details first.", "info")
        return redirect(url_for("checkout.shipping"))

    try:
        resp = api_post("/buy/checkout", json=shipping_info)
    except GatewayUnavailable:
        flash("Unable to reach the checkout service. Please try again.", "danger")
        return redirect(url_for("checkout.review"))
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    if resp.status_code == 201:
        session.pop("shipping_info", None)
        order = resp.json()
        return redirect(url_for("checkout.success", order_id=order["id"]))

    data = resp.json()
    flash(data.get("error", "Something went wrong placing your order."), "danger")
    return redirect(url_for("cart.view_cart"))


@checkout_bp.route("/success/<int:order_id>")
@login_required_frontend
def success(order_id):
    try:
        resp = api_get(f"/buy/orders/{order_id}")
    except GatewayUnavailable:
        flash("Unable to reach the order service.", "danger")
        return redirect(url_for("main.home"))
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    if resp.status_code != 200:
        flash("Order not found.", "warning")
        return redirect(url_for("main.home"))

    return render_template("checkout/success.html", order=resp.json())