from database import db

class ItemTable(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Float(precision=2), unique=False, nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), unique=False, nullable=False)
    # stores now associated with corresponding item
    store = db.relationship("StoreTable", back_populates="items")
    orders = db.relationship("OrderTable", back_populates="items",secondary="items_orders")