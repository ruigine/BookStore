from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Book(db.Model):
    __tablename__ = 'Books'

    book_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ISBN = db.Column(db.String(20), nullable=False)
    authors = db.Column(db.Text, nullable=True)
    publishers = db.Column(db.String(255), nullable=True)
    format = db.Column(db.String(50), nullable=True)
    genre = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    url = db.Column(db.Text, nullable=True)

    def json(self):
        return {
            "book_id": self.book_id,
            "title": self.title,
            "description": self.description,
            "ISBN": self.ISBN,
            "authors": self.authors,
            "publishers": self.publishers,
            "format": self.format,
            "genre": self.genre,
            "price": self.price,
            "quantity": self.quantity,
            "url": self.url,
        }
    
    def __repr__(self):
        return f"<Book {self.book_id} - {self.title}>"