import os
from datetime import timedelta
from flask import Blueprint
from flask_session import Session
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_db_connection


delivery_bp = Blueprint('delivery', __name__)

@delivery_bp.route('/')
def index_employee():
    return "Welcome to the Employee App!"

app = Flask(__name__)
app.secret_key = 'yourpassword'

# Configure session
app.permanent_session_lifetime = timedelta(days=7)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

DELIVERY_IMAGES_DIR = os.path.join( 'delivery_app/static/delivery_images')
os.makedirs(DELIVERY_IMAGES_DIR, exist_ok=True)

@app.before_request
def make_session_permanent():
    session.permanent = True



@app.route('/')
def home():
    return redirect(url_for('delivery_login'))




@app.route('/delivery/register', methods=['GET', 'POST'])
def delivery_register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        re_password = request.form['re_password']

        if password != re_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('delivery_register'))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            query = """
                INSERT INTO delivery_persons (first_name, last_name, email, phone_number, hashed_password)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (first_name, last_name, email, phone_number, hashed_password))
            conn.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for('delivery_login'))
        except Exception as err:
            flash(f"Error: {err}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template('delivery_register.html')


@app.route('/delivery/login', methods=['GET', 'POST'])
def delivery_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM delivery_persons WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user['hashed_password'], password):
            session['driver_id'] = user['id']
            session['delivery_person_name'] = f"{user['first_name']} {user['last_name']}"
            flash("Login successful!", "success")
            return redirect(url_for('delivery_home'))
        else:
            flash("Invalid email or password.", "danger")

    return render_template('delivery_login.html')


@app.route('/delivery_home', methods=['GET', 'POST', 'DELETE'])
def delivery_home():
    driver_id = session.get('driver_id')
    if not driver_id:
        return redirect(url_for('delivery_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT *, DATE_FORMAT(created_at, '%M %d, %Y %h:%i %p') AS formatted_date
        FROM orders
        WHERE status = 'Ready for Delivery' OR (status = 'Order Pickup On the Way' AND driver_id = %s)
        ORDER BY created_at DESC
    """
    cursor.execute(query, (driver_id,))
    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('delivery_home.html', orders=orders)


@app.route('/accept_order', methods=['POST'])
def accept_order():
    driver_id = session.get('driver_id')
    if not driver_id:
        return jsonify({'message': 'Unauthorized access. Please log in.'}), 401

    data = request.get_json()
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({'message': 'Invalid order ID.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Assign the order to the driver and ensure no other driver can accept it
        query = """
            UPDATE orders
            SET driver_id = %s, status = 'Order Pickup On the Way'
            WHERE id = %s AND driver_id IS NULL AND status = 'Ready for Delivery'
        """
        cursor.execute(query, (driver_id, order_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'message': 'Order already accepted by another driver or not ready.'}), 400

        return jsonify({'message': 'Order accepted successfully.'}), 200
    except Exception as e:
        return jsonify({'message': f'Error accepting order: {e}'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    driver_id = session.get('driver_id')
    if not driver_id:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({'message': 'Invalid order ID'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            UPDATE orders
            SET driver_id = NULL, status = 'Ready for Delivery'
            WHERE id = %s AND driver_id = %s
        """
        cursor.execute(query, (order_id, driver_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'message': 'Order not found or not assigned to you.'}), 404

        return jsonify({'message': 'Order successfully canceled'})
    except Exception as e:
        return jsonify({'message': f'Error canceling order: {e}'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/deliver-order/<int:order_id>', methods=['POST'])
def deliver_order(order_id):
    driver_id = session.get('driver_id')
    if not driver_id:
        return jsonify({'message': 'Unauthorized access. Please log in.'}), 401

    # Fetch uploaded delivery image
    delivery_image = request.files.get('delivery_image')
    if not delivery_image:
        return jsonify({'message': 'Delivery image is required.'}), 400

    # Ensure the directory exists
    image_dir = os.path.join('delivery_app','static', 'delivery_images')
    os.makedirs(image_dir, exist_ok=True)

    # Save the uploaded image
    image_filename = f"{order_id}_{secure_filename(delivery_image.filename)}"
    image_path = os.path.join(image_dir, image_filename)
    try:
        delivery_image.save(image_path)
    except Exception as e:
        return jsonify({'message': f'Error saving image: {str(e)}'}), 500

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Atomically check and fetch the order assigned to this driver
        cursor.execute("""
            SELECT * FROM orders WHERE id = %s AND driver_id = %s AND status = 'Order Pickup On the Way'
        """, (order_id, driver_id))
        order = cursor.fetchone()

        if not order:
            return jsonify({'message': 'Order not found, unauthorized, or already delivered.'}), 404

        # Insert the order into `history_orders`
        cursor.execute("""
            INSERT INTO history_orders (
                id, user_id, first_name, last_name, street_address, city, state, zip_code,
                phone_number, order_summary, total_price, delivery_charge, final_total,
                status, delivery_image, delivered_at, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """, (
            order['id'], order['user_id'], order['first_name'], order['last_name'], order['street_address'],
            order['city'], order['state'], order['zip_code'], order['phone_number'], order['order_summary'],
            order['total_price'], order['delivery_charge'], order['final_total'], 'Delivered', image_path,
            order['created_at']
        ))

        # Delete the order from the `orders` table
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        conn.commit()

        return jsonify({'message': 'Order marked as delivered and archived successfully.'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Error delivering order: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()








@app.route('/delivery/logout')
def delivery_logout():
    session.pop('driver_id', None)
    session.pop('delivery_person_name', None)
    flash("You have logged out.", "success")
    return redirect(url_for('delivery_login'))

if __name__ == '__main__':
    app.run(debug=True)














