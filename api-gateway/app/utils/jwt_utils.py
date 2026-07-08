import datetime

import jwt
from flask import current_app


def generate_token(user_id, username):
    """Issues a JWT signed with the shared JWT_SECRET, valid for 24 hours.

    Every downstream service verifies this token independently using the
    same secret, rather than calling back to the Gateway to check it.
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")