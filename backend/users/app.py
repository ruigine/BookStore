from os import environ
import re
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from model import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
CORS(app)

def verify_info(email,password):
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    
    if re.match(email_regex, email) and len(password) >= 6:
        return True
    else:
        return False

#To create a new user
@app.post("/register")
def create_user():
    data = request.get_json()

    #Check valid email and password
    if verify_info(data['email'], data['password']):
        #Set userid
        try:
            # Check if user already exists
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

            # Add user into DB
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

@app.get("/login")
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

        token = jwt.encode({
            "sub": user.user_id,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=2)
        }, environ.get('JWT_SECRET_KEY'), algorithm="HS256")

        return jsonify(
            {
                "code": 200,
                "token": token
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
    app.run(host='0.0.0.0', port=5001, debug=True)