from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from auth import jwt_required

app = Flask(__name__)
CORS(app)

ORDERS_URL = "http://orders:5003/orders/user"

@app.get("/myorders")
@jwt_required
def get_my_orders():
    try:
        user_id = request.user["sub"]

        response = requests.get(f"{ORDERS_URL}/{user_id}")
        if response.status_code != 200:
            return jsonify(response.json()), response.status_code

        orders = response.json()["data"]
        return jsonify(
            {
                "code": 200,
                "data": orders
            }
        ), 200

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
