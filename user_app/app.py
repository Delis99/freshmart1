import os
import re
import logging
import mysql
from flask import Blueprint
from datetime import timedelta
from flask_session import Session
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_db_connection


user_bp = Blueprint('user', __name__)

@user_bp.route('/')
def index_employee():
    return "Welcome to the Employee App!"




app = Flask(__name__)
app.config['DEBUG'] = True

app.secret_key = os.getenv("SECRET_KEY", "your-default-secure-secret-key")

# Configure session
app.permanent_session_lifetime = timedelta(days=7)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


UPLOAD_FOLDER = 'user_app/static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.before_request
def make_session_permanent():
    session.permanent = True

# Index page
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
    






@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Collect data from the form
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        re_password = request.form['re_password']
        contact = request.form['contact']

        # Validate password strength
        password_regex = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(password_regex, password):
            flash("Password must contain at least 8 characters, one uppercase letter, one number, and one special character.", "danger")
            return redirect(url_for('register_user'))

        # Check if passwords match
        if password != re_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register_user'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if email already exists
            cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
            email_exists = cursor.fetchone()

            if email_exists:
                flash("Email already exists. Please use a different email.", "danger")
                cursor.close()
                conn.close()
                return redirect(url_for('register_user'))

            # Insert new user data
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (name, last_name, email, hashed_password, contact) VALUES (%s, %s, %s, %s, %s)",
                (first_name, last_name, email, hashed_password, contact)
            )
            conn.commit()
            cursor.close()
            conn.close()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            app.logger.error(f"Error during registration: {str(e)}")
            flash(f"Error registering: {str(e)}", "danger")
            return redirect(url_for('register_user'))

    return render_template('register_user.html')


@app.route('/check_email', methods=['POST'])
def check_email():
    email = request.json.get('email')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        email_exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return {"exists": email_exists}, 200
    except Exception as e:
        app.logger.error(f"Error checking email: {str(e)}")
        return {"error": str(e)}, 500










#Login
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

            if user and check_password_hash(user['hashed_password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                flash(f"Welcome, {user['name']}!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password.", "danger")
                return render_template('login_user.html')

        except Exception as e:
            flash(f"Error logging in: {str(e)}", "danger")
            return render_template('login_user.html')

        finally:
            cursor.close()
            conn.close()

    return render_template('login_user.html')


# Add to Cart Button
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    quantity = int(request.form['quantity'])

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if the product is already in the cart
        cursor.execute("SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        existing_item = cursor.fetchone()

        if existing_item:
            # Update the cart with the new quantity
            cursor.execute("UPDATE cart SET quantity = quantity + %s WHERE user_id = %s AND product_id = %s", (quantity, user_id, product_id))
        else:
            # Add the new item to the cart
            cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)", (user_id, product_id, quantity))

        conn.commit()
        flash("Item added to your cart!", "success")

    except Exception as e:
        flash(f"Error adding item to cart: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('home'))



#Home page
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch user details
        cursor.execute("SELECT name, last_name, email, contact FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            flash("User not found.", "danger")
            return redirect(url_for('login'))

        # Fetch products
        search_query = request.args.get('search', '')
        if search_query:
            cursor.execute("SELECT * FROM products WHERE quantity > 0 AND name LIKE %s", ('%' + search_query + '%',))
        else:
            cursor.execute("SELECT * FROM products WHERE quantity > 0")
        products = cursor.fetchall()

        # Fetch cart details
        cursor.execute("""
            SELECT p.name, c.quantity, p.price 
            FROM cart AS c
            JOIN products AS p ON c.product_id = p.id
            WHERE c.user_id = %s
        """, (user_id,))
        cart_items = cursor.fetchall()

        # Calculate cart totals
        cart_count = sum(item['quantity'] for item in cart_items)
        total_cost = sum(item['quantity'] * item['price'] for item in cart_items)

    except Exception as e:
        flash(f"Error fetching data: {str(e)}", "danger")
        return render_template('error.html', message="An error occurred while loading the home page.")

    finally:
        cursor.close()
        conn.close()

    return render_template('home.html',
                           name=user['name'],
                           last_name=user['last_name'],
                           email=user['email'],
                           contact=user['contact'],
                           products=products,
                           cart_items=cart_items,
                           cart_count=cart_count,
                           total_cost=total_cost)



# View Cart
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Join `cart` and `products` to fetch detailed product information
        query = """
            SELECT 
                c.id AS cart_id, 
                p.id AS product_id, 
                p.name, 
                p.price, 
                p.weight, 
                p.image_url, 
                c.quantity
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s
        """
        cursor.execute(query, (user_id,))
        cart_items = cursor.fetchall()

        # Calculate totals
        total_price = sum(item['price'] * item['quantity'] for item in cart_items)
        total_weight = sum(item['weight'] * item['quantity'] for item in cart_items)
        unique_items = len(cart_items)
        delivery_charge = 5 if total_weight > 20 else 0
        final_total = total_price + delivery_charge

    except Exception as e:
        flash(f"Error retrieving cart: {e}", "danger")
        cart_items = []
        total_price = 0
        total_weight = 0
        unique_items = 0
        delivery_charge = 0
        final_total = 0

    finally:
        cursor.close()
        conn.close()

    return render_template(
        'cart_user.html',
        cart_items=cart_items,
        unique_items=unique_items,
        total_price=total_price,
        total_weight=total_weight,
        delivery_charge=delivery_charge,
        final_total=final_total
    )


@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cart_id = int(request.form['cart_id'])  # Use cart_id to identify the item in the cart
    quantity = int(request.form['quantity'])

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update the quantity of the item in the cart
        cursor.execute("UPDATE cart SET quantity = %s WHERE id = %s AND user_id = %s", (quantity, cart_id, user_id))
        conn.commit()
        flash("Cart updated successfully", "success")

    except Exception as e:
        flash(f"Error updating cart: {e}", "danger")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('cart'))


@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Remove the product from the cart for the logged-in user
        cursor.execute("DELETE FROM cart WHERE product_id = %s AND user_id = %s", (product_id, user_id))
        conn.commit()
        flash("Item removed from cart", "success")

    except Exception as e:
        flash(f"Error removing item from cart: {e}", "danger")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('cart'))












@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        session['user_id'] = 1  # Simulate login for testing

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch saved details for the dropdown
    cursor.execute("""
        SELECT DISTINCT first_name, last_name, street_address, city, state, zip_code, 
               phone_number, card_number, expiry_date, cvv 
        FROM orders WHERE user_id = %s AND card_number IS NOT NULL
    """, (user_id,))
    saved_addresses = cursor.fetchall()

    # Fetch cart items
    cursor.execute("""
        SELECT p.id AS product_id, p.name, p.price, c.quantity, p.weight, p.image_url, (p.price * c.quantity) AS total
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))
    cart_items = cursor.fetchall()

    # Calculate totals
    total_weight = sum(item['weight'] * item['quantity'] for item in cart_items)
    total_price = sum(item['total'] for item in cart_items)
    delivery_charge = 5 if total_weight > 20 else 0
    final_total = total_price + delivery_charge

    if request.method == 'POST':
        # Fetch form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        street_address = request.form['street_address']
        city = request.form['city']
        state = request.form['state']
        zip_code = request.form['zip_code']
        phone_number = request.form['phone_number']
        card_number = request.form['card_number']
        reenter_card_number = request.form['reenter_card_number']
        expiry_date = request.form['expiry_date']
        cvv = request.form['cvv']
        save_details = 'save_details' in request.form  # Check if the save checkbox is checked

        # Ensure the card numbers match
        if card_number != reenter_card_number:
            flash("Card numbers do not match. Please try again.", "danger")
            return redirect(url_for('checkout'))

        # Prepare the order summary
        order_summary = ", ".join([f"{item['name']} x {item['quantity']}" for item in cart_items])

        try:
            # Insert the order into the orders table
            cursor.execute("""
                INSERT INTO orders (
                    user_id, first_name, last_name, street_address, city, state, 
                    zip_code, phone_number, card_number, expiry_date, cvv,
                    order_summary, total_price, delivery_charge, final_total
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, first_name, last_name, street_address, city, state, zip_code,
                  phone_number, card_number if save_details else None,
                  expiry_date if save_details else None,
                  cvv if save_details else None,
                  order_summary, total_price, delivery_charge, final_total))

            # Decrease product quantities based on the order
            for item in cart_items:
                cursor.execute("""
                    UPDATE products SET quantity = quantity - %s WHERE id = %s
                """, (item['quantity'], item['product_id']))

            # Clear the user's cart
            cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))

            conn.commit()
            flash("Order placed successfully, and cart cleared!", "success")
        except Exception as e:
            flash(f"Error placing order: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

            # Redirect to the thank-you page
        return redirect(url_for('thank_you_for_checkout'))

    cursor.close()
    conn.close()

    return render_template(
        'checkout.html',
        cart_items=cart_items,
        total_price=total_price,
        total_weight=total_weight,
        delivery_charge=delivery_charge,
        final_total=final_total,
        saved_addresses=saved_addresses
    )


















@app.route('/thank_you_for_checkout')
def thank_you_for_checkout():
    return render_template('thank_you_for_checkout.html')




@app.route('/feedback', methods=['GET', 'POST'])
def submit_feedback():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        feedback = request.form['feedback']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO feedback (name, email, feedback) 
                VALUES (%s, %s, %s)
            """, (name, email, feedback))
            conn.commit()
            return render_template('feedback_user.html', success=True)  # Pass success flag
        except Exception as e:
            return render_template('feedback_user.html', error=True)  # Pass error flag
        finally:
            cursor.close()
            conn.close()

    return render_template('feedback_user.html')








# Logout 
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)