from app.extensions import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)

    product_id = db.Column(db.Integer, nullable=True, index=True)
    product_name = db.Column(db.String(150), nullable=False)
    price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    @property
    def subtotal(self):
        return self.price_at_purchase * self.quantity

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "price_at_purchase": float(self.price_at_purchase),
            "quantity": self.quantity,
            "subtotal": float(self.subtotal),
        }

    def __repr__(self):
        return f"<OrderItem order={self.order_id} product={self.product_name} qty={self.quantity}>"