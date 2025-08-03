-- CREATE DATABASE
DROP DATABASE IF EXISTS bookstore;
CREATE DATABASE bookstore;
USE bookstore;

-- INSERT TABLES
CREATE TABLE Users (
	user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash TEXT NOT NULL,
    created_at DATE NOT NULL
);

CREATE TABLE Books (
	book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    ISBN VARCHAR(20) NOT NULL,
    authors TEXT,
    publishers VARCHAR(255),
    format VARCHAR(50),
    price DECIMAL(10, 2) NOT NULL,
    quantity INT NOT NULL,
    url TEXT 
);

CREATE TABLE Orders (
	order_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    user_id INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    quantity INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    authors TEXT,
    url TEXT,

    FOREIGN KEY (book_id) REFERENCES Books(book_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);


-- INSERT TEST DATA
-- Test Data for
