import sqlite3

DATABASE = 'user_reviews.db'  # Update to your actual database file

def get_db():
    db = sqlite3.connect(DATABASE, check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db
