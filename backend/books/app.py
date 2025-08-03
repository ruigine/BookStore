from flask import Flask, request, jsonify
from flask_cors import CORS
from model import db, Book
from os import environ
from sqlalchemy import or_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
CORS(app)

@app.get("/books")
def get_books():
    try:
        query = Book.query

        # Genre filter (e.g., ?genre=Fantasy)
        genre = request.args.get('genre')
        if genre:
            query = query.filter(Book.genre == genre)

        # Price range filter (e.g., ?min_price=10&max_price=50)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        if min_price is not None:
            query = query.filter(Book.price >= min_price)
        if max_price is not None:
            query = query.filter(Book.price <= max_price)

        # Search term in title (e.g., ?search=wizard)
        search = request.args.get('search')
        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                Book.title.ilike(search_term),
                Book.authors.ilike(search_term),
                Book.ISBN.ilike(search_term)
            ))

        books = query.all()

        return jsonify(
            {
                "code": 200,
                "data": [book.json() for book in books]
            }
        ), 200

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred: {str(e)}"
            }
        ), 500

@app.get("/books/<int:book_id>")
def get_book_by_id(book_id):
    try:
        book = Book.query.get(book_id)
        if not book:
            return jsonify(
                {
                    "code": 404,
                    "message": "Book was not found."
                }
            ), 404

        return jsonify(
            {
                "code": 200,
                "data": book.json()
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
    app.run(host="0.0.0.0", port=5002, debug=True)
