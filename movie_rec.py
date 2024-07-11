import sqlite3
from datetime import datetime
from cinemagoer import Cinemagoer
import openapi
from main2 import get_db
from werkzeug.security import generate_password_hash, check_password_hash

conn = get_db()
c = conn.cursor()
cg = Cinemagoer()

try:
    with open('database.sql', 'r') as f:
        c.executescript(f.read())
    conn.commit()
except sqlite3.OperationalError as e:
    pass


def get_user_info(user):
    # Fetch user information from the database
    c.execute('SELECT username, email, sign_up_date FROM users WHERE id = ?', (user,))
    found_user = c.fetchone()

    return found_user


def get_reviews(user):
    # for flask app
    # Fetch the user’s reviews from the database
    c.execute('''SELECT m.title, r.rating, r.comment, r.review_date 
                     FROM reviews r
                     JOIN movies m ON r.movie_id = m.id
                     WHERE r.user_id = ?''', (user,))
    reviews = c.fetchall()

    return reviews


def make_user(username, password, email):
    #username = input("Enter a username: ")
    #password = input("Enter a password: ")
    #email = input("Enter your email: ")
    hashed_password = generate_password_hash(password)
    signup_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        c.execute(
            "INSERT INTO users (username, password, email, sign_up_date) VALUES (?, ?, ?, ?)",
            (username,
             hashed_password,
             email,
             signup_date))
        conn.commit()
        print("\nSuccessfully Made a New Account!")
        return c.lastrowid
    # Error that is caught, when that information, or any exists.
    except sqlite3.IntegrityError:
        print("\nUsername already exists. You need to login.")
        return None


def login_user(username, password):
    #username = input("Enter your username: ")
    #password = input("Enter your password: ")

    # check if username is valid
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    user_pass = c.fetchone()

    # checks if stored hashed password matches the user-entered password
    if user_pass is not None:
        is_valid_pass = check_password_hash(user_pass[0], password)

        if is_valid_pass:
            # if password is valid, try to retrieve user
            c.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,))
            user = c.fetchone()
            if user:
                print("\nLogin successful!\n")
                return user[0]  # Getting id of user table
            else:
                print("\nInvalid credentials. Please try again.\n")
                return None
    else:
        print("\nInvalid credentials. Please try again.\n")
        return None


def get_movie_id(title):
    c.execute("SELECT id FROM movies WHERE title = ?", (title,))
    movie = c.fetchone()
    return movie[0] if movie else None


def review_movie(user_id, title, rating, comment):
    #title = input("Enter the movie title you want to submit a review for: ")
    review_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    movie_id = get_movie_id(title)

    if not movie_id:
        c.execute("INSERT INTO movies (title) VALUES (?)", (title,))
        conn.commit()
        movie_id = c.lastrowid

    """if cinemagoer.search_movie(title):
        #rating = int(input("Rate the movie out of 5 stars: "))
        #comment = input("Add some comments about the movie: ")
        #review_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        movie_id = cinemagoer.get_movie_id(title)

        # Check if the movie is already in the movies table
        c.execute("SELECT id FROM movies WHERE title = ?", (title,))
        result = c.fetchone()

        if result:
            movie_id = result[0]
        else:
            c.execute("INSERT INTO movies (title) VALUES (?)", (title,))
            conn.commit()
            movie_id = c.lastrowid

        c.execute(
            "INSERT INTO reviews (user_id, movie_id, rating, comment, review_date) VALUES (?, ?, ?, ?, ?)",
            (user_id,
             movie_id,
             rating,
             comment,
             review_date))
        conn.commit()
        print("\nReview submitted!\n")
        return True
    else:
        print("\nThe movie title does not exist in the Cinemagoer API. Please enter a valid movie title.\n")
        return False"""

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


def recommendation_made(user_id):
    c.execute("SELECT COUNT(*) FROM reviews "
              "WHERE user_id = ?", (user_id,))
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

    movies = []
    ratings = []
    comments = []
    review_dates = []

    for review in reviews:
        rating, comment, review_date, movie_title = review
        movies.append(movie_title)
        ratings.append(rating)
        comments.append(comment)
        review_dates.append(review_date)

    return movies, ratings, comments, review_dates


def print_reviews(user_id):
    movies, ratings, comments, review_dates = fetch_reviews(user_id)
    print("\nYour Reviews:\n")
    for movie, rating, comment, review_date in zip(
            movies, ratings, comments, review_dates):
        print(
            f"\tMovie: {movie}, Rating: {rating}, Comment: {comment}, Review Date: {review_date}",
            end='\n')
    print("")
    return movies, ratings, comments, review_dates


def get_recommendation(user_id):
    genres = [
        "Action",
        "Adventure",
        "Comedy",
        "Drama",
        "Fantasy",
        "Horror",
        "Mystery",
        "Romance",
        "Sci-Fi",
        "Thriller"]
    age_ratings = ["G", "PG", "PG-13", "R"]
    year_ranges = ["2000-2010", "2011-2015", "2016-2020", "2021-present"]

    genre = input(
        f"\nSelect a genre from the following list: {', '.join(genres)}: ")
    age_rating = input(
        f"Select an age-appropriateness rating from the following list: {', '.join(age_ratings)}: ")
    year_range = input(
        f"Select a recency range from the following list: {', '.join(year_ranges)}: ")

    if recommendation_made(user_id):
        movies, ratings, _, _ = fetch_reviews(user_id)
        recommendation = openapi.get_movie_recommendation(
            movies, ratings, genre, age_rating, year_range)
        print(f"\nBased on your review history and answers, we recommend you to watch: \n\n{recommendation}\n")
    else:
        print(
            "\nNo movie recommendations available at the moment. Must submit a movie review 🎅",
            end='\n')


def ask_trivia(user_id):
    c.execute("""
        SELECT reviews.rating, reviews.comment, reviews.review_date, movies.title
        FROM reviews
        JOIN movies ON reviews.movie_id = movies.id
        WHERE reviews.user_id = ?
    """, (user_id,))
    reviews = c.fetchall()

    # Only here to use the movies & their titles
    movies = []
    ratings = []
    comments = []
    review_dates = []

    for review in reviews:
        rating, comment, review_date, movie_title = review
        movies.append(movie_title)
        ratings.append(rating)
        comments.append(comment)
        review_dates.append(review_date)

    return openapi.start_trivia(movies)


def main():
    user_id = None
    while not user_id:
        print(
            "\n****** Welcome to FlixFix, Your Personalized Movie Recommender ******",
            end='\n')
        print("\nNew users must register. Returning users must login.")
        print("\n\t1. Register")
        print("\t2. Login")
        action = input(
            "\nPlease enter the number of your choice (1 or 2): ")
        if action == '1':
            user_id = make_user()
        elif action == '2':
            user_id = login_user()

    while True:
        print("What would you like to do next?")
        print("\n\t1. Review a Movie")
        print("\t2. Get a Recommended Movie")
        print("\t3. Get a List of Your Reviews")
        print("\t4. Movie Trivia")
        print("\t5. Quit\n")
        action = input("Please enter the number of your choice (1, 2, 3, 4 or 5): ")
        if action == '1':
            review_movie(user_id)
        elif action == '2':
            get_recommendation(user_id)
        elif action == '3':
            if recommendation_made(user_id):
                print_reviews(user_id)
            else:
                print("\nYou have not made any recommendations yet\n")
        elif action == '4':
            if recommendation_made(user_id):
                ask_trivia(user_id)
            else:
                print("\nYou have not made any recommendations yet\n")
        elif action == '5':
            print("\nThank you for using FlixFix. Goodbye!")
            break


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


if __name__ == "__main__":
    main()
