from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt
from models import ItemTable
from sqlalchemy.exc import SQLAlchemyError
from database import db
from schemas import ItemSchema, ItemUpdateSchema

blp = Blueprint("Items", "items", description="Operations on items")


@blp.route("/item/<string:item_id>")
class Item(MethodView):
    @jwt_required()
    @blp.response(200, ItemSchema)
    def get(self, item_id):
        # if the searched item not found, then 404 message displays
        item = ItemTable.query.get_or_404(item_id)
        return item

    @jwt_required()
    def delete(self, item_id):
        item = ItemTable.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()

        return {"message": "Item deleted."}, 200

    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def put(self, item_data, item_id):
        item = ItemTable.query.get(item_id)

        if item:
            item.price = item_data["price"]
            item.name = item_data["name"]
        else:
            item = ItemTable(id=item_id, **item_data)

        db.session.add(item)
        db.session.commit()

        return item


@blp.route("/item")
class ItemList(MethodView):
    @jwt_required()
    @blp.response(200, ItemSchema(many=True))
    def get(self):
        return ItemTable.query.all()

    @jwt_required()
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data):
        item = ItemTable(**item_data)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting item.")

        return item