from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from shared.auth import jwt_required
from shared.rabbitmq import RabbitMQClient

app = Flask(__name__)
CORS(app)

ORDERS_URL = "http://orders:5003/orders"

@app.route('/health')  
def health():
    return {'status': 'ok'}

@app.post("/placeorder")
@jwt_required
def place_order():
    try:
        data = request.get_json()

        order_payload = {
            "book_id": data["book_id"],
            "user_id": request.user["sub"],
            "price": data["price"],
            "quantity": data["quantity"],
            "status": "pending",
            "title": data["title"],
            "authors": data["authors"],
            "url": data["url"]
        }

        response = requests.post(ORDERS_URL, json=order_payload)
        if response.status_code != 201:
            return jsonify(response.json()), response.status_code

        order_data = response.json()["data"]

        client = RabbitMQClient()
        client.publish(order_data)

        return jsonify(
            {
                "code": 201,
                "data": order_data
            }
        ), 201

    except Exception as e:
        return jsonify(
            {
                "code": 500, "message": f"An error occurred: {str(e)}"
            }
        ), 500
    
@app.get("/checkorder/<int:order_id>")
@jwt_required
def check_order_status(order_id):
    try:
        response = requests.get(f"{ORDERS_URL}/{order_id}")
        if response.status_code != 200:
            return jsonify(response.json()), response.status_code

        order = response.json()["data"]

        if order["user_id"] != int(request.user["sub"]):
            return jsonify({"code": 403, "message": "Forbidden. Order does not belong to this user."}), 403

        return jsonify(
            {
                "code": 200,
                "data": {
                    "order_id": order["order_id"],
                    "status": order["status"]
                }
            }
        ), 200

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500
    
@app.get("/pendingorder/<int:book_id>")
@jwt_required
def get_my_pending_book_order(book_id):
    try:
        user_id = request.user["sub"]
        res = requests.get(f"{ORDERS_URL}/user/{user_id}/book/{book_id}")
        
        return jsonify(res.json()), res.status_code

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)