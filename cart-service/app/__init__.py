from flask import Flask, jsonify

from app.config import Config
from app.extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.validate()

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models  # noqa: F401

    from app.routes.cart import cart_bp
    app.register_blueprint(cart_bp)

    @app.route("/health")
    def health():
        return jsonify({"service": "cart-service", "status": "ok"})

    return app