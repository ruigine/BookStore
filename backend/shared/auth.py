import jwt
from flask import request, jsonify
from functools import wraps
from os import environ

SECRET_KEY = environ.get('JWT_SECRET_KEY')
def verify_jwt(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            return {"error": "Invalid token type"}
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify(
                {
                    "code": 401, "message": "Missing Authorization header"
                }
            ), 401

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid scheme")
        except Exception:
            return jsonify(
                {
                    "code": 401, "message": "Invalid Authorization format"
                }
            ), 401

        result = verify_jwt(token)
        if isinstance(result, dict) and result.get("error"):
            return jsonify(
                {
                    "code": 401, "message": result["error"]
                }
            ), 401

        request.user = result
        return f(*args, **kwargs)

    return decorated