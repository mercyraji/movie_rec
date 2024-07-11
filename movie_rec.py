import sqlite3
from datetime import datetime
import hashlib
import json
from cinemagoer import Cinemagoer
from db import get_db

conn = get_db()
c = conn.cursor()
cg = Cinemagoer()

try:
    with open('database.sql', 'r') as f:
        c.executescript(f.read())
    conn.commit()
except sqlite3.OperationalError:
    pass

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def make_user(username, password, email):
    signup_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hashed_password = hash_password(password)

    try:
        c.execute(
            "INSERT INTO users (username, password, email, sign_up_date) VALUES (?, ?, ?, ?)",
            (username, hashed_password, email, signup_date)
        )
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None

def login_user(username, password):
    hashed_password = hash_password(password)
    c.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    user = c.fetchone()
    if user:
        return user[0]
    else:
        return None

def get_user_info(user_id):
    c.execute('SELECT username, email, sign_up_date FROM users WHERE id = ?', (user_id,))
    found_user = c.fetchone()
    return found_user

def get_reviews(user_id):
    c.execute('''SELECT m.title, r.rating, r.comment, r.review_date 
                 FROM reviews r
                 JOIN movies m ON r.movie_id = m.id
                 WHERE r.user_id = ?''', (user_id,))
    reviews = c.fetchall()
    return reviews

def review_movie(user_id, title, rating, comment):
    review_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    movie_id = get_movie_id(title)

    if not movie_id:
        c.execute("INSERT INTO movies (title) VALUES (?)", (title,))
        conn.commit()
        movie_id = c.lastrowid

    c.execute(
        "INSERT INTO reviews (user_id, movie_id, rating, comment, review_date) VALUES (?, ?, ?, ?, ?)",
        (user_id, movie_id, rating, comment, review_date)
    )
    conn.commit()
    return True

def get_movie_id(title):
    c.execute("SELECT id FROM movies WHERE title = ?", (title,))
    movie = c.fetchone()
    return movie[0] if movie else None

def recommendation_made(user_id):
    c.execute("SELECT COUNT(*) FROM reviews WHERE user_id = ?", (user_id,))
    count = c.fetchone()[0]
    return count > 0

def fetch_reviews(user_id):
    c.execute("""
        SELECT reviews.rating, reviews.comment, reviews.review_date, movies.title
        FROM reviews
        JOIN movies ON reviews.movie_id = movies.id
        WHERE reviews.user_id = ?
    """, (user_id,))
    reviews = c.fetchall()
    return [(review['title'], review['rating'], review['comment'], review['review_date']) for review in reviews]

def print_reviews(user_id):
    reviews = fetch_reviews(user_id)
    for review in reviews:
        print(f"Movie: {review[0]}, Rating: {review[1]}, Comment: {review[2]}, Review Date: {review[3]}")
    return reviews

def ask_trivia(user_id):
    c.execute("""
        SELECT reviews.rating, reviews.comment, reviews.review_date, movies.title
        FROM reviews
        JOIN movies ON reviews.movie_id = movies.id
        WHERE reviews.user_id = ?
    """, (user_id,))
    reviews = c.fetchall()
    movies = [review['title'] for review in reviews]
    return openapi.start_trivia(movies)

def get_wishlist(user_id):
    c.execute('''SELECT m.id, m.title, w.added_date 
                 FROM wishlist w
                 JOIN movies m ON w.movie_id = m.id
                 WHERE w.user_id = ?''', (user_id,))
    wishlist = c.fetchall()
    return [{'id': item['id'], 'title': item['title'], 'added_date': item['added_date']} for item in wishlist]


def add_to_wishlist(user_id, movie_id, title):
    added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        movie_id = get_movie_id(title)
        if not movie_id:
            c.execute("INSERT INTO movies (title) VALUES (?)", (title,))
            conn.commit()
            movie_id = c.lastrowid

        c.execute(
            "INSERT INTO wishlist (user_id, movie_id, added_date) VALUES (?, ?, ?)",
            (user_id, movie_id, added_date)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_from_wishlist(user_id, title):
    movie_id = get_movie_id(title)
    if not movie_id:
        return False

    try:
        c.execute("DELETE FROM wishlist WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
