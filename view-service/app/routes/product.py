from flask import Blueprint, request, jsonify, abort

from app.extensions import db
from app.models.product import Product
from app.utils.decorators import token_required

product_bp = Blueprint("product", __name__, url_prefix="/products")


@product_bp.route("", methods=["GET"])
def list_products():
    query = Product.query.filter_by(is_active=True)

    search_term = request.args.get("q", "").strip()
    if search_term:
        query = query.filter(Product.name.ilike(f"%{search_term}%"))

    category = request.args.get("category", "").strip()
    if category:
        query = query.filter(Product.category == category)

    products = query.order_by(Product.created_at.desc()).all()
    return jsonify([p.to_dict() for p in products]), 200


@product_bp.route("/categories", methods=["GET"])
def list_categories():
    rows = (
        db.session.query(Product.category)
        .filter_by(is_active=True)
        .distinct()
        .order_by(Product.category)
        .all()
    )
    return jsonify([row[0] for row in rows]), 200


@product_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product is None or not product.is_active:
        abort(404, description="Product not found.")
    return jsonify(product.to_dict()), 200


@product_bp.route("", methods=["POST"])
@token_required
def create_product():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    price = data.get("price")
    stock = data.get("stock", 0)

    errors = {}
    if not name:
        errors["name"] = "Name is required."
    if price is None or float(price) < 0:
        errors["price"] = "Price must be a non-negative number."
    if not isinstance(stock, int) or stock < 0:
        errors["stock"] = "Stock must be a non-negative integer."

    if errors:
        return jsonify({"errors": errors}), 400

    product = Product(
        name=name,
        description=data.get("description"),
        category=(data.get("category") or "Uncategorized").strip(),
        price=price,
        stock=stock,
        image_filename=data.get("image_filename"),
    )
    db.session.add(product)
    db.session.commit()

    return jsonify(product.to_dict()), 201


@product_bp.route("/<int:product_id>/stock", methods=["PATCH"])
@token_required
def update_stock(product_id):
    """Decrements stock by the given quantity. Called by Buy Service after
    a successful purchase, forwarding the purchasing user's own JWT."""
    product = Product.query.get(product_id)
    if product is None:
        abort(404, description="Product not found.")

    data = request.get_json(silent=True) or {}
    quantity = data.get("quantity")

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "quantity must be a positive integer."}), 400

    if quantity > product.stock:
        return jsonify({
            "error": f"Only {product.stock} in stock, cannot decrement by {quantity}."
        }), 409

    product.stock -= quantity
    db.session.commit()

    return jsonify(product.to_dict()), 200