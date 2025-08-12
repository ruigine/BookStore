from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from shared.auth import jwt_required

app = Flask(__name__)
CORS(app)

ORDERS_URL = "http://orders:5003/orders/user"

@app.get("/myorders")
@jwt_required
def get_my_orders():
    try:
        user_id = request.user["sub"]

        page = request.args.get('page')
        limit = request.args.get('limit')
        query_string = ''

        if page is not None and limit is not None:
            query_string = f"?page={page}&limit={limit}"
        elif page is not None:
            query_string = f"?page={page}"
        elif limit is not None:
            query_string = f"?limit={limit}"
        
        url = f"{ORDERS_URL}/{user_id}"
        if query_string:
            url += query_string

        response = requests.get(url)
        
        if response.status_code != 200:
            return jsonify(response.json()), response.status_code

        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
