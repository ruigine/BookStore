from flask import Flask, request, jsonify
from flask_cors import CORS
from os import environ
from model import db, Order
from sqlalchemy import desc

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db.init_app(app)

@app.post("/orders")
def create_order():
    try:
        data = request.get_json()
        order = Order(
            book_id=data['book_id'],
            user_id=data['user_id'],
            price=data['price'],
            quantity=data['quantity'],
            status=data['status'],
            title=data['title'],
            authors=data.get('authors'),
            url=data.get('url')
        )
        db.session.add(order)
        db.session.commit()

        return jsonify(
            {
                "code": 201,
                "data": order.json()
            }
        ), 201

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500


@app.put("/orders/<int:order_id>")
def update_order_status(order_id):
    try:
        data = request.get_json()
        order = db.session.get(Order, order_id)

        if not order:
            return jsonify(
                {
                    "code": 404,
                    "message": "Order not found."
                }
            ), 404

        order.status = data['status']
        db.session.commit()

        return jsonify(
            {
                "code": 200,
                "data": order.json()
            }
        ), 200

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500

@app.get("/orders/<int:order_id>")
def get_order(order_id):
    try:
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify(
                {
                    "code": 404,
                    "message": "Order not found."
                }
            ), 404

        return jsonify(
            {
                "code": 200,
                "data": order.json()
            }
        ), 200

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500

@app.get("/orders/user/<int:user_id>")
def get_orders_by_user(user_id):
    try:
        base_query = Order.query.filter_by(user_id=user_id).order_by(desc(Order.order_date))

        page = request.args.get('page', type=int)
        limit = request.args.get('limit', type=int)

        if page is not None or limit is not None:
            page = page or 1
            limit = limit or 4
            offset = (page - 1) * limit

            total_orders = base_query.count()
            paginated_orders = base_query.offset(offset).limit(limit).all()

            return jsonify(
                {
                    "code": 200,
                    "data": [order.json() for order in paginated_orders],
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total_orders,
                        "has_more": offset + limit < total_orders
                    }
                }
            ), 200

        orders = base_query.all()
        return jsonify(
            {
                "code": 200,
                "data": [order.json() for order in orders]
            }
        ), 200

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500

@app.get("/orders/user/<int:user_id>/book/<int:book_id>")
def get_pending_order_by_user_and_book(user_id, book_id):
    try:
        order = Order.query.filter_by(user_id=user_id, status="pending", book_id=book_id).first()

        if not order:
            return jsonify(
                {
                    "code": 200,
                    "hasPending": False
                }
            ), 200

        return jsonify(
            {
                "code": 200,
                "hasPending": True,
                "data": order.json()
            }
        ), 200

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
