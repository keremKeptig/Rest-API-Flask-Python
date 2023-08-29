from database import db

class StoreTable(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    # items now associated with corresponding store
    # lazy = dynamic, means don't add to database now
    # cascade because if we delete store, all items should be deleted that are associated with that store
    items = db.relationship("ItemTable", back_populates="store", lazy="dynamic", cascade="all, delete")
    tags = db.relationship("TagTable", back_populates="store", lazy="dynamic")