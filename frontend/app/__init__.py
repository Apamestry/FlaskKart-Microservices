from flask import Flask, session

from app.config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.validate()

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.cart import cart_bp
    from app.routes.checkout import checkout_bp
    from app.routes.order import order_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(order_bp)

    @app.context_processor
    def inject_auth_state():
        return {
            "is_logged_in": bool(session.get("token")),
            "current_username": session.get("username"),
        }

    return app