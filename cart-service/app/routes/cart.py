from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.cart_item import CartItem
from app.utils.decorators import token_required
from app.utils.view_client import fetch_product, ViewServiceUnavailable

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


@cart_bp.route("", methods=["GET"])
@token_required
def view_cart():
    items = CartItem.query.filter_by(user_id=request.user_id).all()

    enriched = []
    total = 0.0

    try:
        for item in items:
            product = fetch_product(item.product_id)
            if product is None:
                enriched.append({
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "product": None,
                    "subtotal": 0,
                    "unavailable": True,
                })
                continue

            subtotal = product["price"] * item.quantity
            total += subtotal
            enriched.append({
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "product": product,
                "subtotal": subtotal,
                "unavailable": False,
            })
    except ViewServiceUnavailable:
        return jsonify({"error": "View Service is unavailable."}), 503

    return jsonify({"items": enriched, "total": total}), 200


@cart_bp.route("/add", methods=["POST"])
@token_required
def add_to_cart():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not isinstance(product_id, int):
        return jsonify({"error": "product_id is required and must be an integer."}), 400
    if not isinstance(quantity, int) or quantity < 1:
        quantity = 1

    try:
        product = fetch_product(product_id)
    except ViewServiceUnavailable:
        return jsonify({"error": "View Service is unavailable."}), 503

    if product is None:
        return jsonify({"error": "Product not found."}), 404
    if not product.get("is_active", True):
        return jsonify({"error": "Product is no longer available."}), 404

    stock = product["stock"]
    if stock <= 0:
        return jsonify({"error": f"{product['name']} is out of stock."}), 409

    existing = CartItem.query.filter_by(user_id=request.user_id, product_id=product_id).first()

    warning = None
    if existing:
        new_qty = existing.quantity + quantity
        if new_qty > stock:
            warning = f"Only {stock} of {product['name']} available. Quantity capped."
            new_qty = stock
        existing.quantity = new_qty
    else:
        new_qty = min(quantity, stock)
        if new_qty < quantity:
            warning = f"Only {stock} of {product['name']} available. Quantity capped."
        db.session.add(CartItem(user_id=request.user_id, product_id=product_id, quantity=new_qty))

    db.session.commit()

    response = {"message": "Added to cart.", "product_id": product_id, "quantity": new_qty}
    if warning:
        response["warning"] = warning
    return jsonify(response), 200


@cart_bp.route("/items/<int:item_id>", methods=["PATCH"])
@token_required
def update_item(item_id):
    item = CartItem.query.get(item_id)
    if item is None or item.user_id != request.user_id:
        return jsonify({"error": "Cart item not found."}), 404

    data = request.get_json(silent=True) or {}
    quantity = data.get("quantity")

    if not isinstance(quantity, int):
        return jsonify({"error": "quantity must be an integer."}), 400

    if quantity < 1:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Item removed from cart."}), 200

    try:
        product = fetch_product(item.product_id)
    except ViewServiceUnavailable:
        return jsonify({"error": "View Service is unavailable."}), 503

    warning = None
    if product and quantity > product["stock"]:
        warning = f"Only {product['stock']} available. Quantity capped."
        quantity = product["stock"]

    item.quantity = quantity
    db.session.commit()

    response = {"message": "Cart updated.", "quantity": item.quantity}
    if warning:
        response["warning"] = warning
    return jsonify(response), 200


@cart_bp.route("/items/<int:item_id>", methods=["DELETE"])
@token_required
def remove_item(item_id):
    item = CartItem.query.get(item_id)
    if item is None or item.user_id != request.user_id:
        return jsonify({"error": "Cart item not found."}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item removed from cart."}), 200


@cart_bp.route("/clear", methods=["DELETE"])
@token_required
def clear_cart():
    """Empties the current user's entire cart. Called by Buy Service
    right after a successful order is placed, forwarding the same JWT."""
    CartItem.query.filter_by(user_id=request.user_id).delete()
    db.session.commit()
    return jsonify({"message": "Cart cleared."}), 200