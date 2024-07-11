from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from cinemagoer import Cinemagoer
from datetime import datetime
import sqlite3
import hashlib
import json

import movie_rec

app = Flask(__name__)
app.config['SECRET_KEY'] = '9bf26e1d684bc092e43722e46066e1af'

cg = Cinemagoer()

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Execute SQL script
    try:
        with open('database.sql', 'r') as f:
            c.executescript(f.read())
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Error during database initialization: {e}")
    finally:
        conn.close()

# Initialize the database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_id = movie_rec.login_user(username, password)

        if user_id:
            session['user_id'] = user_id
            return redirect(url_for('index'))
        else:
            return jsonify({'error': 'Account doesn\'t exist or info is wrong'}), 400

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/submit-review', methods=['GET', 'POST'])
def submit_review():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    if request.method == 'POST':
        user_id = session['user_id']
        title = request.form['title']
        rating = int(request.form['rating'])
        comment = request.form['comment']

        success = movie_rec.review_movie(user_id, title, rating, comment)

        if success:
            return redirect(url_for('index'))
        else:
            return render_template('review.html', error='Failed')

    return render_template('review.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    curr_user = movie_rec.get_user_info(user_id)

    return render_template('profile.html', user=curr_user)

@app.route('/profile/my_reviews')
def my_reviews():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_reviews = movie_rec.get_reviews(user_id)

    return render_template('user_reviews.html', reviews=user_reviews)

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
        return redirect(url_for('login'))

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


@app.route('/trivia', methods=['GET', 'POST'])
def trivia():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    trivia_questions = movie_rec.ask_trivia(user_id)

    if request.method == 'POST':
        user_answers = request.form
        score = 0
        for i, question in enumerate(trivia_questions):
            user_answer = user_answers.get(f'question_{i}')
            if user_answer == trivia_questions['correct_answer']:
                score += 1

        return render_template('trivia_result.html', correct_answers=trivia_questions, total_questions=len(trivia_questions))

    return render_template('trivia.html', questions=trivia_questions)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
