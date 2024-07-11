from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
import movie_rec
import sqlite3
import openapi
from cinemagoer import Cinemagoer
import cinemagoer

app = Flask(__name__)
app.config['SECRET_KEY'] = '9bf26e1d684bc092e43722e46066e1af'

# Database setup
DATABASE = 'database.db'  # Update to your actual database file

cg = Cinemagoer()


def get_db():
    # gets user db
    db = sqlite3.connect(DATABASE, check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db


# home pg
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        user_id = movie_rec.make_user(username, password, email)

        if user_id:
            session['user_id'] = user_id
            return redirect(url_for('index'))
        else:
            return jsonify({'error': 'Invalid input'}), 400

    return render_template('register.html')


@app.route('/log-in', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_id = movie_rec.login_user(username, password)

        if user_id:
            session['user_id'] = user_id
            return redirect(url_for('index'))
        else:
            return jsonify({'error': 'Account doesn\'t exists or info is wrong'}), 400

    return render_template('login.html')


@app.route('/log-out')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/submit-review', methods=['GET','POST'])
def submit_review():
    if 'user_id' not in session:
        return redirect(url_for('log-in'))

    if request.method == 'POST':
        user_id = session['user_id']
        title = request.form['title']
        rating = int(request.form['rating'])
        comment = request.form['comment']

        # Call review_movie function
        success = movie_rec.review_movie(user_id, title, rating, comment)

        if success:
            return redirect(url_for('index'))  # Redirect to index page on success

    return render_template('review.html')


@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('log-in'))

    user_id = session['user_id']
    curr_user = movie_rec.get_user_info(user_id)

    return render_template('profile.html', user=curr_user)


@app.route('/profile/my_reviews', methods=['GET'])
def my_reviews():
    if 'user_id' not in session:
        return redirect(url_for('log-in'))

    user_id = session['user_id']
    user_reviews = movie_rec.get_reviews(user_id)

    return render_template('user_reviews.html', reviews=user_reviews)


@app.route('/trivia', methods=['GET','POST'])
def trivia():
    if 'user_id' not in session:
        return redirect(url_for('log-in'))

    user_id = session['user_id']
    trivia_questions = movie_rec.ask_trivia(user_id)

    if request.method == 'POST':

        user_answers = request.form

        score = 0
        for i, question in enumerate(trivia_questions):
            """if user_answers.get(f'question_{i}').strip().upper() in trivia_questions['correct_answer'].split(' ')[0]:
               score += 1"""
            user_answer = user_answers.get(f'question_{i}')
            if user_answer == trivia_questions['correct_answer']:
                score += 1

        return render_template('trivia_result.html',
                               correct_answers=trivia_questions, total_questions=len(trivia_questions))

    return render_template('trivia.html', questions=trivia_questions)


@app.route('/get-recommendation', methods=['GET','POST'])
def get_recommendation():
    if 'user_id' not in session:
        return redirect(url_for('log-in'))

    user_id = session['user_id']

    if not movie_rec.recommendation_made(user_id):
        flash("You need to submit a review before getting recommendations.")
        return redirect(url_for('submit_review'))

    if request.method == 'POST':
        genre = request.form['genre']
        age_rating = request.form['age_rating']
        year_range = request.form['year_range']

        movies, ratings, _, _ = movie_rec.fetch_reviews(user_id)
        recommendations = openapi.get_movie_recommendation(movies, ratings, genre, age_rating, year_range)

        # Parse recommendations into a list of dictionaries
        recommendations_list = recommendations.split('\n')
        parsed_recommendations = []
        for rec in recommendations_list:
            if rec and ' - ' in rec:
                title, description = rec.split(' - ', 1)
                parsed_recommendations.append({'title': title.strip(), 'description': description.strip()})

        # Extract just the movie titles
        movie_titles = [rec['title'] for rec in parsed_recommendations]
        movie_ids = []
        for movie in movie_titles:
            movie_ids.append(cinemagoer.get_movie_id(movie))

        return render_template('recommendations.html', recommendations=parsed_recommendations)

    genres = ["Action", "Adventure", "Comedy", "Drama", "Fantasy", "Horror", "Mystery", "Romance", "Sci-Fi", "Thriller"]
    age_ratings = ["G", "PG", "PG-13", "R"]
    year_ranges = ["2000-2010", "2011-2015", "2016-2020", "2021-present"]
    return render_template('recommend.html', genres=genres, age_ratings=age_ratings, year_ranges=year_ranges)


@app.route('/search', methods=['GET'])
def search_movies():
    query = request.args.get('query')
    if not query:
        return render_template('search.html', movies=[])

    user_id = session.get('user_id')
    wishlist_movie_ids = []
    if user_id:
        wishlist_movies = movie_rec.get_wishlist(user_id)
        wishlist_movie_ids = [movie['id'] for movie in wishlist_movies]

    movies = cg.search_movie(query)
    search_results = [{
        'id': movie.movieID,
        'title': movie['title'],
        'year': movie.get('year', 'N/A'),
        'image_url': movie.get('cover url', '/static/default_movie.png'),
        'in_wishlist': movie.movieID in wishlist_movie_ids
    } for movie in movies]

    return render_template('search.html', movies=search_results)


@app.route('/wishlist', methods=['GET'])
def view_wishlist():
    if 'user_id' not in session:
        return redirect(url_for('log-in'))

    user_id = session['user_id']
    wishlist = movie_rec.get_wishlist(user_id)

    return render_template('wishlist.html', wishlist=wishlist)


@app.route('/wishlist/add', methods=['POST'])
def add_to_wishlist():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 403

    user_id = session['user_id']
    data = request.get_json()  # This line ensures JSON data is parsed correctly
    movie_id = data['id']
    title = data['title']

    success = movie_rec.add_to_wishlist(user_id, movie_id, title)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False}), 400


@app.route('/wishlist/remove', methods=['POST'])
def remove_from_wishlist():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 403

    user_id = session['user_id']
    data = request.get_json()  # This line ensures JSON data is parsed correctly
    movie_id = data['id']
    title = data['title']

    success = movie_rec.remove_from_wishlist(user_id, title)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False}), 400


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
