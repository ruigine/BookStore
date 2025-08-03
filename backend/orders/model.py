from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Order(db.Model):
    __tablename__ = 'Orders'

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    authors = db.Column(db.Text, nullable=True)
    url = db.Column(db.Text, nullable=True)
    order_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    def __init__(self, book_id, user_id, price, quantity, status, title, authors, url):
        self.book_id = book_id
        self.user_id = user_id
        self.price = price
        self.quantity = quantity
        self.status = status
        self.title = title
        self.authors = authors
        self.url = url

    def json(self):
        return {
            "order_id": self.order_id,
            "book_id": self.book_id,
            "user_id": self.user_id,
            "price": self.price,
            "quantity": self.quantity,
            "status": self.status,
            "title": self.title,
            "authors": self.authors,
            "url": self.url,
            "order_date": self.order_date
        }
    
    def __repr__(self):
        return f"<Order {self.order_id} - {self.title}>"