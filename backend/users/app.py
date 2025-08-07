from os import environ
import re
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from model import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
CORS(app, supports_credentials=True)

def verify_info(email, password):
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    
    if re.match(email_regex, email) and len(password) >= 6:
        return True
    else:
        return False

@app.post("/register")
def create_user():
    data = request.get_json()

    if verify_info(data['email'], data['password']):
        try:
            existing_user = User.query.filter_by(email=data['email']).first()

            if existing_user:
                return jsonify(
                    {
                        "code": 400,
                        "data": {
                            "email": data['email']
                        },
                        "message": "Email is already registered."
                    }
                ), 400

            new_user = User(
                username=data['username'],
                email=data['email'],
                password_hash=generate_password_hash(data['password'])
            )

            db.session.add(new_user)
            db.session.commit()

        except Exception as e:
            return jsonify(
                {
                    "code": 500,
                    "data": {
                        "email": data['email']
                    },
                    "message": f"An error occurred creating the user. {e}"
                }
            ), 500
    else:
        return jsonify(
                {
                    "code": 400,
                    "data": {
                        "email": data['email']
                    },
                    "message": "Invalid email or password less than 6 characters"
                }
            ), 400
    
    return jsonify(
        {
            "code": 201,
            "data": {
                "user_id": new_user.user_id,
                "email": new_user.email,
                "username": new_user.username
            }
        }
    ), 201

@app.post("/login")
def login():
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):
            return jsonify(
                {
                    "code": 400,
                    "message": "Email and password are required."
                }
            ), 400

        user = User.query.filter_by(email=data['email']).first()

        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify(
                {
                    "code": 401,
                    "message": "Invalid email or password."
                }
            ), 401

        access_token = jwt.encode({
            "sub": str(user.user_id),
            "name": user.username,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "type": "access"
        }, environ.get('JWT_SECRET_KEY'), algorithm="HS256")

        refresh_token = jwt.encode({
            "sub": str(user.user_id),
            "name": user.username,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            "type": "refresh"
        }, environ.get('JWT_SECRET_KEY'), algorithm="HS256")

        resp = make_response(jsonify(
            {
                "code": 200,
                "access_token": access_token
            }
        ), 200)

        resp.set_cookie(
            "refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="Strict",
            path="/refresh-token"
        )

        return resp

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500

@app.post("/refresh-token")
def refresh_token():
    try:
        old_token = request.cookies.get("refresh_token")

        if not old_token:
            return jsonify(
                {
                    "code": 401,
                    "message": "Missing refresh token."
                }
            ), 401

        payload = jwt.decode(old_token, environ.get("JWT_SECRET_KEY"), algorithms=["HS256"])

        if payload.get("type") != "refresh":
            return jsonify(
                {
                    "code": 400,
                    "message": "Invalid token type"
                }
            ), 400

        user_id = payload["sub"]

        user = User.query.get(user_id)

        if not user:
            return jsonify(
                {
                    "code": 401,
                    "message": "Invalid refresh token user."
                }
            ), 401

        new_access_token = jwt.encode({
            "sub": str(user.user_id),
            "name": user.username,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            "type": "access"
        }, environ.get("JWT_SECRET_KEY"), algorithm="HS256")

        new_refresh_token = jwt.encode({
            "sub": str(user.user_id),
            "name": user.username,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            "type": "refresh"
        }, environ.get("JWT_SECRET_KEY"), algorithm="HS256")

        resp = make_response(jsonify(
            {
                "code": 200,
                "access_token": new_access_token
            }
        ), 200)

        resp.set_cookie(
            "refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="Strict",
            path="/refresh-token"
        )

        return resp

    except jwt.ExpiredSignatureError:
        return jsonify(
            {
                "code": 401,
                "message": "Refresh token expired."
            }
        ), 401

    except jwt.InvalidTokenError:
        return jsonify(
            {
                "code": 401,
                "message": "Invalid refresh token."
            }
        ), 401

@app.post("/logout")
def logout():
    resp = make_response(jsonify(
        {
            "code": 200,
            "message": "Logged out"
        }
    ), 200)
    resp.set_cookie("refresh_token", "", expires=0, path="/refresh-token")
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)