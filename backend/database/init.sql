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
    genre VARCHAR(50) NOT NULL,
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
-- Test Data for Books
INSERT INTO Books (title, description, ISBN, authors, publishers, format, price, quantity, url, genre)
VALUES
-- Fantasy
("The Dragon's Flame", 'An epic fantasy adventure.', '9781234567890', 'A. R. Winters', 'Mythos Press', 'Hardcover', 19.99, 10, 'https://example.com/dragon', 'Fantasy'),

-- Fantasy (again)
('Shadowbound', 'A dark fantasy about a cursed warrior seeking redemption.', '9781234567800', 'Mira Thorne', 'Obsidian Ink', 'Paperback', 18.40, 11, 'https://example.com/shadowbound', 'Fantasy'),

-- Fantasy (again v2)
('The Elven Path', 'A tale of magic and prophecy.', '9781234567895', 'Lyra Moon', 'Mystic Pages', 'Paperback', 17.25, 15, 'https://example.com/elven', 'Fantasy'),

-- Fantasy (again v3)
('Empire of Stars', 'An epic fantasy saga spanning realms and centuries.', '9781234567890', 'Kaelen Rivers', 'Starlit Press', 'Hardcover', 34.99, 6, 'https://example.com/empireofstars', 'Fantasy'),

-- Romance
('Love in Paris', 'A romantic journey through the City of Light.', '9781234567891', 'Clara Heart', 'Amour House', 'Paperback', 12.50, 8, 'https://example.com/paris', 'Romance'),

-- Romance (again)
('Hearts and Horizons', 'Two souls rediscover love.', '9781234567894', 'J. K. Bennett', 'Golden Love', 'Hardcover', 21.00, 5, 'https://example.com/hearts', 'Romance'),

-- Mystery
('Whispers of the Past', 'A gripping mystery novel set in Victorian London.', '9781234567892', 'E. J. Black', 'Fog & Flame', 'Ebook', 9.99, 12, 'https://example.com/whispers', 'Mystery'),

-- Sci-Fi
('Quantum Realms', 'Exploring the edges of time and space.', '9781234567893', 'Dex Vaughn', 'Nebula Reads', 'Paperback', 14.99, 7, 'https://example.com/quantum', 'Science Fiction'),

-- Sci-Fi (again)
('Galactic Drift', 'An interstellar war breaks out.', '9781234567896', 'R. T. Clarke', 'SpaceLine', 'Ebook', 6.50, 20, 'https://example.com/galactic', 'Science Fiction'),

-- Non-fiction
('Mindset Shift', 'Change your thinking, change your life.', '9781234567897', 'Carol Dweck', 'Growth Publications', 'Paperback', 11.45, 9, 'https://example.com/mindset', 'Self-Help'),

-- Mystery
('The Forgotten Clue', 'Unraveling an unsolved case.', '9781234567898', 'Nina Grey', 'CrimeTime Books', 'Hardcover', 16.75, 6, 'https://example.com/forgotten', 'Mystery'),

-- Children's
('Adventures of Bobo', "A monkey's jungle quest.", '9781234567899', 'Leo Bright', 'Tiny Readers', 'Board Book', 8.90, 14, 'https://example.com/bobo', 'Children');
