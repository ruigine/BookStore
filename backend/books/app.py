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

        # Pagination
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 8, type=int)
        offset = (page - 1) * limit

        total_books = query.count()
        books = query.offset(offset).limit(limit).all()

        return jsonify(
            {
                "code": 200,
                "data": [book.json() for book in books],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_books,
                    "has_more": offset + limit < total_books
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

@app.get("/books/<int:book_id>")
def get_book_by_id(book_id):
    try:
        book = db.session.get(Book, book_id)
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
    
@app.put("/books/<int:book_id>/decrement")
def decrement_book_quantity(book_id):
    try:
        data = request.get_json()
        quantity_decrement = data.get("quantity_ordered")

        if quantity_decrement is None or not isinstance(quantity_decrement, int) or quantity_decrement <= 0:
            return jsonify(
                {
                    "code": 400,
                    "message": "Invalid quantity provided. Must be more than 0."
                }
            ), 400

        book = db.session.get(Book, book_id)
        if not book:
            return jsonify(
                {
                    "code": 404,
                    "message": "Book not found."
                }
            ), 404
        
        if quantity_decrement > book.quantity:
            return jsonify(
                {
                    "code": 400,
                    "message": "New quantity should not go below 0."
                }
            ), 400

        book.quantity = book.quantity - quantity_decrement
        db.session.commit()

        return jsonify(
            {
                "code": 200,
                "message": f"Quantity updated to {book.quantity}.",
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
