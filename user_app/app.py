import os
import re
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_db_connection

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "your-default-secure-secret-key")


UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Home 
@app.route('/')
def index():
    search_query = request.args.get('search', '').strip().lower()
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Search
        if search_query:
            cursor.execute(
                "SELECT * FROM products WHERE LOWER(name) LIKE %s ORDER BY name ASC",
                (f"%{search_query}%",)
            )
        else:
            cursor.execute("SELECT * FROM products ORDER BY name ASC")

        products = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('index.html', products=products)
    except Exception as e:
        return render_template('error.html', message=f"Error fetching products: {str(e)}")

# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        re_password = request.form['re_password']

        # Validate password strength
        password_regex = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(password_regex, password):
            flash("Password must be at least 8 characters long, with an uppercase letter, number, and special character.", "danger")
            return redirect(url_for('register'))

        # Check if passwords match
        if password != re_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (name, last_name, email, hashed_password) VALUES (%s, %s, %s, %s)",
                (name, last_name, email, hashed_password)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            return render_template('error.html', message=f"Error registering: {str(e)}")

    return render_template('register_user.html')

# Login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user['hashed_password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                flash(f"Welcome, {user['name']}!", "success")
                return redirect(url_for('index'))
            else:
                flash("Invalid email or password.", "danger")
        except Exception as e:
            return render_template('error.html', message=f"Error logging in: {str(e)}")

    return render_template('login_user.html')

# Add to Cart Button
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash("Please log in to add products to your cart.", "danger")
        return redirect(url_for('login'))

    try:
        quantity = int(request.form['quantity'])
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        cursor.close()
        conn.close()

        if not product:
            flash("Product not found.", "danger")
            return redirect(url_for('index'))

        if 'cart' not in session:
            session['cart'] = []

        
        for item in session['cart']:
            if item['id'] == product['id']:
                item['quantity'] += quantity
                break
        else:
            session['cart'].append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity
            })

        session.modified = True
        flash("Product added to cart!", "success")
    except Exception as e:
        flash(f"Error adding to cart: {str(e)}", "danger")

    return redirect(url_for('index'))

# Logout 
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)








