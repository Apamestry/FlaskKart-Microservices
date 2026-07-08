from flask import Blueprint, request, jsonify
from email_validator import validate_email, EmailNotValidError

from app.extensions import db
from app.models.user import User
from app.utils.jwt_utils import generate_token
from app.utils.decorators import token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    errors = {}

    if len(username) < 3 or len(username) > 80:
        errors["username"] = "Username must be between 3 and 80 characters."
    elif User.query.filter_by(username=username).first():
        errors["username"] = "That username is already taken."

    if not email:
        errors["email"] = "Email is required."
    else:
        try:
            validate_email(email, check_deliverability=False)
            if User.query.filter_by(email=email).first():
                errors["email"] = "An account with that email already exists."
        except EmailNotValidError:
            errors["email"] = "Enter a valid email address."

    if len(password) < 8:
        errors["password"] = "Password must be at least 8 characters."

    if errors:
        return jsonify({"errors": errors}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "Account created successfully.",
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401

    token = generate_token(user.id, user.username)

    return jsonify({
        "token": token,
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    user = User.query.get(request.user_id)
    if user is None:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"id": user.id, "username": user.username, "email": user.email}), 200