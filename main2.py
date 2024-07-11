from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import movie_rec
import sqlite3
import openapi

app = Flask(__name__)
app.config['SECRET_KEY'] = '9bf26e1d684bc092e43722e46066e1af'

# Database setup
DATABASE = 'user_reviews.db'  # Update to your actual database file


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
        return jsonify({'error': 'User not logged in'}), 403

    if request.method == 'POST':
        user_id = session['user_id']
        title = request.form['title']
        rating = int(request.form['rating'])
        comment = request.form['comment']

        # Call review_movie function
        success = movie_rec.review_movie(user_id, title, rating, comment)

        if success:
            return redirect(url_for('index'))  # Redirect to index page on success
        else:
            return render_template('review.html', error='Failed')

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


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")