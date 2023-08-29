from database import db

class OrderTable(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    store_id = db.Column(db.Integer(), db.ForeignKey("stores.id"), nullable=False)

    store = db.relationship("StoreTable", back_populates="orders")
    items = db.relationship("ItemTable", back_populates="orders", secondary="items_orders")