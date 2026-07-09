from datetime import datetime

from app.extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

    payment_status = db.Column(db.String(20), nullable=False, default="Completed")
    order_status = db.Column(db.String(20), nullable=False, default="Placed")

    shipping_full_name = db.Column(db.String(120), nullable=False)
    shipping_address_line1 = db.Column(db.String(200), nullable=False)
    shipping_address_line2 = db.Column(db.String(200), nullable=True)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_state = db.Column(db.String(100), nullable=False)
    shipping_zip_code = db.Column(db.String(20), nullable=False)
    shipping_phone = db.Column(db.String(20), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")

    def to_dict(self, include_items=True):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "total_amount": float(self.total_amount),
            "payment_status": self.payment_status,
            "order_status": self.order_status,
            "shipping": {
                "full_name": self.shipping_full_name,
                "address_line1": self.shipping_address_line1,
                "address_line2": self.shipping_address_line2,
                "city": self.shipping_city,
                "state": self.shipping_state,
                "zip_code": self.shipping_zip_code,
                "phone": self.shipping_phone,
            },
            "created_at": self.created_at.isoformat(),
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data

    def __repr__(self):
        return f"<Order #{self.id} user={self.user_id} total={self.total_amount}>"