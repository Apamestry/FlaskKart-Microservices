from functools import wraps

import jwt
from flask import request, jsonify, current_app


def token_required(f):
    """Verifies the Bearer token in the Authorization header using JWT_SECRET.

    On success, attaches request.user_id and request.username for the route
    to use. This same decorator (verifying independently, not by calling the
    Gateway) is copied into every other service so each one trusts the token's
    signature rather than trusting network origin alone.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header."}), 401

        token = auth_header.split(" ", 1)[1].strip()

        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        request.user_id = payload["user_id"]
        request.username = payload["username"]
        return f(*args, **kwargs)

    return decorated