from flask import Flask, redirect, render_template, request, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import config
from MySQLdb import IntegrityError  # Add this import
from datetime import timedelta

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = 'your_secret_key'  # Replace with a secure key
app.permanent_session_lifetime = timedelta(minutes=30)  # Set session timeout to 30 minutes

mysql = MySQL(app)

import re

def is_strong_password(password):
    return re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password)

# Route for login/signup page
@app.route('/')
def login_page():
    return render_template('Login_signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']

    if not is_strong_password(password):
        flash('Password must be at least 8 characters long and include at least 1 uppercase letter, 1 number, and 1 special character.', 'danger')
        return redirect(url_for('login_page'))

    hashed_password = generate_password_hash(password)  # Hash the password

    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO USER_Details (email, password) VALUES (%s, %s)", (email, hashed_password))
        mysql.connection.commit()
        flash('Signup successful! Please log in.', 'success')
    except IntegrityError:
        flash('Email already exists. Please log in.', 'danger')
    finally:
        cur.close()

    return redirect(url_for('login_page'))


# Route for home page
@app.route('/home')
def home():
    if 'email' in session:  # Check if the user is logged in
        return render_template('home.html', email=session['email'])  # Render home.html
    else:
        return redirect(url_for('login_page'))  # Redirect to login if not logged in

# Route for logout
@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login_page'))

@app.route('/recommendations')
def recommendations():
    return render_template('recommendations.html')

@app.route('/get-recommendations', methods=['POST'])
def get_recommendations():
    # Process form data here
    gender = request.form['gender']
    height = request.form['height']
    weight = request.form['weight']
    skintone = request.form['skintone']
    bodytype = request.form['bodytype']
    aesthetic = request.form['aesthetic']
    occasion = request.form['occasion']

    # Example: Return a response or render a new template
    return f"Recommendations for {gender}, {height}, {weight}, {skintone}, {bodytype}, {aesthetic}, {occasion}"

@app.route('/recomendations')
def redirect_to_recommendations():
    return redirect(url_for('recommendations'))

if __name__ == '__main__':
    app.run(debug=True)


