from flask import Flask, redirect, render_template, request, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from MySQLdb import IntegrityError
from datetime import timedelta
import re
import config

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = 'your_secret_key'
app.permanent_session_lifetime = timedelta(minutes=30)

mysql = MySQL(app)

def is_strong_password(password):
    return re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password)

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

    hashed_password = generate_password_hash(password)
    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO USER_details (email, password) VALUES (%s, %s)", (email, hashed_password))
        mysql.connection.commit()
        flash('Signup successful! Please log in.', 'success')
    except IntegrityError:
        flash('Email already exists. Please log in.', 'danger')
    finally:
        cur.close()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM USER_details WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['is_admin'] = bool(user.get('is_admin', False))
            return redirect(url_for('admin_dashboard' if session['is_admin'] else 'home'))
        else:
            flash("Invalid credentials", "danger")
            return render_template('Login_signup.html')

    return render_template('Login_signup.html')

@app.route('/home')
def home():
    if 'email' in session:
        return render_template('home.html', email=session['email'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/recommendations')
def recommendations():
    return render_template('recommendations.html')

@app.route('/get-recommendations', methods=['POST'])
def get_recommendations():
    try:
        gender = request.form['gender']
        bodytype = request.form['bodytype']
        skintone = request.form['skintone']
        aesthetic_id = int(request.form['aesthetic'])
        occasion_id = int(request.form['occasion'])

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
        cur.close()

        unique_recommendations = []
        seen = set()
        for rec in recommendations:
            key = (rec['Topwear'], rec['Bottomwear'], rec['Footwear'], rec['Accessory'])
            if key not in seen:
                unique_recommendations.append(rec)
                seen.add(key)

        if not unique_recommendations:
            flash('No recommendations found for your selection.', 'info')

        return render_template('recommendations.html', recommendations=unique_recommendations)

    except Exception as e:
        print(f"Error: {str(e)}")
        flash('An error occurred while getting recommendations.', 'danger')
        return render_template('recommendations.html', recommendations=[])

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM USER_details")
    users = cur.fetchall()

    cur.execute("SELECT * FROM ClothingItems")
    clothes = cur.fetchall()

    cur.execute("SELECT COUNT(*) AS count FROM USER_details")
    user_count = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) AS count FROM ClothingItems")
    clothes_count = cur.fetchone()['count']
    cur.close()

    return render_template('admin.html', users=users, clothes=clothes, user_count=user_count, clothes_count=clothes_count)

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if not session.get('is_admin'):
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM USER_details WHERE id = %s", (user_id,))
    mysql.connection.commit()
    cur.close()
    flash("User deleted successfully.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_clothing/<int:clothing_id>')
def delete_clothing(clothing_id):
    if not session.get('is_admin'):
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM ClothingItems WHERE ItemID = %s", (clothing_id,))
    mysql.connection.commit()
    cur.close()
    flash("Clothing item deleted successfully.", "info")
    return redirect(url_for('admin_dashboard'))


@app.route('/save-to-closet', methods=['POST'])
def save_to_closet():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    topwear = request.form['Topwear']
    bottomwear = request.form['Bottomwear']
    footwear = request.form['Footwear']
    accessory = request.form['Accessory']

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO SavedCloset (user_id, Topwear, Bottomwear, Footwear, Accessory)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, topwear, bottomwear, footwear, accessory))
    mysql.connection.commit()
    cur.close()
    flash('Outfit saved to your closet!', 'success')
    return redirect(url_for('recommendations'))

@app.route('/my-closet')
def my_closet():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM SavedCloset WHERE user_id = %s", (user_id,))
    closet_items = cur.fetchall()
    cur.close()
    return render_template('closet.html', closet_items=closet_items)

@app.route('/delete-from-closet/<int:item_id>', methods=['POST'])
def delete_from_closet(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM SavedCloset WHERE id = %s AND user_id = %s", (item_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Item deleted from your closet.', 'info')
    return redirect(url_for('my_closet'))


if __name__ == '__main__':
    app.run(debug=True)
