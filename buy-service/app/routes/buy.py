from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.utils.decorators import token_required
from app.utils.cart_client import get_cart, clear_cart, CartServiceUnavailable
from app.utils.view_client import (
    decrement_stock, restock, ViewServiceUnavailable, InsufficientStock,
)

buy_bp = Blueprint("buy", __name__, url_prefix="/buy")

REQUIRED_SHIPPING_FIELDS = [
    "full_name", "address_line1", "city", "state", "zip_code", "phone",
]


@buy_bp.route("/checkout", methods=["POST"])
@token_required
def checkout():
    auth_header = request.headers.get("Authorization")
    data = request.get_json(silent=True) or {}

    errors = {}
    for field in REQUIRED_SHIPPING_FIELDS:
        if not (data.get(field) or "").strip():
            errors[field] = "This field is required."
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        cart_data = get_cart(auth_header)
    except CartServiceUnavailable:
        return jsonify({"error": "Cart Service is unavailable."}), 503

    items = cart_data.get("items", [])
    if not items:
        return jsonify({"error": "Your cart is empty."}), 400

    unavailable = [i for i in items if i.get("unavailable")]
    if unavailable:
        return jsonify({
            "error": "Some items in your cart are no longer available. Please remove them first.",
            "unavailable_product_ids": [i["product_id"] for i in unavailable],
        }), 409

    short = [i for i in items if i["quantity"] > i["product"]["stock"]]
    if short:
        return jsonify({
            "error": "Some items no longer have enough stock.",
            "details": [
                {"product_id": i["product_id"], "requested": i["quantity"], "available": i["product"]["stock"]}
                for i in short
            ],
        }), 409

    decremented = []
    for item in items:
        try:
            decrement_stock(item["product_id"], item["quantity"], auth_header)
            decremented.append((item["product_id"], item["quantity"]))
        except InsufficientStock as e:
            for pid, qty in decremented:
                restock(pid, qty, auth_header)
            return jsonify({"error": str(e)}), 409
        except ViewServiceUnavailable:
            for pid, qty in decremented:
                restock(pid, qty, auth_header)
            return jsonify({"error": "View Service is unavailable."}), 503

    total = sum(i["subtotal"] for i in items)

    order = Order(
        user_id=request.user_id,
        total_amount=total,
        payment_status="Completed",
        order_status="Placed",
        shipping_full_name=data["full_name"].strip(),
        shipping_address_line1=data["address_line1"].strip(),
        shipping_address_line2=(data.get("address_line2") or "").strip() or None,
        shipping_city=data["city"].strip(),
        shipping_state=data["state"].strip(),
        shipping_zip_code=data["zip_code"].strip(),
        shipping_phone=data["phone"].strip(),
    )
    db.session.add(order)
    db.session.flush()

    for item in items:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=item["product_id"],
            product_name=item["product"]["name"],
            price_at_purchase=item["product"]["price"],
            quantity=item["quantity"],
        ))

    db.session.commit()

    clear_cart(auth_header)

    return jsonify(order.to_dict()), 201


@buy_bp.route("/orders", methods=["GET"])
@token_required
def order_history():
    orders = (
        Order.query.filter_by(user_id=request.user_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return jsonify([o.to_dict(include_items=False) for o in orders]), 200


@buy_bp.route("/orders/<int:order_id>", methods=["GET"])
@token_required
def order_detail(order_id):
    order = Order.query.get(order_id)
    if order is None or order.user_id != request.user_id:
        return jsonify({"error": "Order not found."}), 404
    return jsonify(order.to_dict()), 200