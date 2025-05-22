from flask import Flask, redirect, render_template, request, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import config
from MySQLdb import IntegrityError  # Add this import
from datetime import timedelta
import pandas as pd

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = 'your_secret_key'  # Replace with a secure key
app.permanent_session_lifetime = timedelta(minutes=30)  # Set session timeout to 30 minutes

mysql = MySQL(app)  
# Load CSV


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
        return redirect(url_for('login'))

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

    return redirect('/home')  # Redirect to the home page after signup

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT password FROM USER_Details WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user['password'], password):  # Validate password
        session['email'] = email  # Log the user in by storing their email in the session
        flash('Login successful!', 'success')
        return redirect(url_for('home'))  # Redirect to the home page
    else:
        flash('Invalid email or password. Please try again.', 'danger')
        return redirect(url_for('login'))  # Redirect back to the login page

@app.route('/login_auth', methods=['POST'])
def login_auth():
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT password FROM USER_Details WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user['password'], password):
        session['email'] = email
        flash('Login successful!', 'success')
        return redirect(url_for('home'))
    else:
        flash('Invalid email or password. Please try again.', 'danger')
        return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('Login_signup.html')

# Route for home page
@app.route('/home')
def home():
    if 'email' in session:  # Check if the user is logged in
        return render_template('home.html', email=session['email'])  # Render home.html
    else:
        return redirect(url_for('login'))  # Redirect to login if not logged in

# Route for logout
@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/recommendations')
def recommendations():
    return render_template('recommendations.html')

@app.route('/get-recommendations', methods=['POST'])
def get_recommendations():
    try:
       

        # Get form data with debug prints
        gender = request.form['gender']
        bodytype = request.form['bodytype']
        skintone = request.form['skintone']
        aesthetic_id = int(request.form['aesthetic'])
        occasion_id = int(request.form['occasion'])

        print(f"Form data received: {request.form}")

        cur = mysql.connection.cursor()
        query = """
            SELECT DISTINCT
                o.Topwear, o.Bottomwear, o.Footwear, o.Accessory,
                o.Gender, o.BodyType, o.SkinTone,
                a.AestheticName, oc.OccasionName
            FROM OutfitRecommendations o
            JOIN Aesthetics a ON o.AestheticID = a.AestheticID
            JOIN Occasions oc ON o.OccasionID = oc.OccasionID
            WHERE o.Gender = %s
              AND o.BodyType = %s
              AND o.SkinTone = %s
              AND o.AestheticID = %s
              AND o.OccasionID = %s
        """
        
        cur.execute(query, (gender, bodytype, skintone, aesthetic_id, occasion_id))
        recommendations = cur.fetchall()
        
        # After recommendations = cur.fetchall()
        unique_recommendations = []
        seen = set()
        for rec in recommendations:
            key = (rec['Topwear'], rec['Bottomwear'], rec['Footwear'], rec['Accessory'])
            if key not in seen:
                unique_recommendations.append(rec)
                seen.add(key)
        
        cur.close()
        
        print(f"Query executed. Found {len(recommendations)} results")
        
        columns = ['Topwear', 'Bottomwear', 'Footwear', 'Accessory', 
                   'Gender', 'BodyType', 'SkinTone', 'AestheticName', 'OccasionName']
        print("Recommendations:", recommendations)
        
        if not recommendations:
            flash('No recommendations found for your selection.', 'info')
        
        return render_template('recommendations.html', recommendations=unique_recommendations, form_data={'gender': gender, 'bodytype': bodytype, 'skintone': skintone, 'aesthetic': aesthetic_id, 'occasion': occasion_id})
    
    except Exception as e:
        print(f"Error in get_recommendations: {str(e)}")
        flash('An error occurred while getting recommendations.', 'error')
        return render_template('recommendations.html', recommendations=[])

if __name__ == '__main__':
    app.run(debug=True)


