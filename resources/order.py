from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database import db
from schemas import OrderSchema, OrderAndItemSchema
from models import StoreTable, OrderTable, ItemTable

blp = Blueprint("Orders", "orders", description="Operations on orders")


@blp.route("/store/<string:store_id>/order")
class OrdersInStore(MethodView):
    @blp.response(200, OrderSchema(many=True))
    def get(self, store_id):
        store = StoreTable.query.get_or_404(store_id)

        return store.orders.all()


    @blp.arguments(OrderSchema)
    @blp.response(201, OrderSchema)
    def post(self,order_data, store_id):
        order = OrderTable(**order_data, store_id=store_id)

        try:
            db.session.add(order)
            db.session.commit()
        except SQLAlchemyError as error:
            abort(
                500,
                message=str(error)
            )
        return order


@blp.route("/item/<string:item_id>/order/<string:order_id>")
class LinkOrdersToItem(MethodView):
    @blp.response(201, OrderSchema)
    def post(self, item_id, order_id):
        item = ItemTable.query.get_or_404(item_id)
        order = OrderTable.query.get_or_404(order_id)

        item.orders.append(order)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Error occurred")

    @blp.response(200, OrderAndItemSchema)
    def delete(self, item_id, order_id):
        item = ItemTable.query.get_or_404(item_id)
        order = OrderTable.query.get_or_404(order_id)

        item.orders.remove(order)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Error occurred")

        return {"message":"Item removed from order"}

@blp.route("/tag/<string:order_id>")
class Tag(MethodView):
    @blp.response(200, OrderSchema)
    def get(self, order_id):
        order = OrderTable.query.get_or_404(order_id)
        return order

    @blp.response(202,description="Deletes a order if no item is ordered with it",example={"message":"Order deleted"})
    @blp.alt_response(404, description="Order not found.")
    @blp.alt_response(400, description="If the order is assigned to one or more items, the order is not deleted")
    def delete(self, order_id):
        order = OrderTable.query.get_or_404(order_id)

        if not order.items:
            db.session.delete(order)
            db.session.commit()
            return {"message":"Order deleted"}

        abort(400,message="Couldn't delete order")