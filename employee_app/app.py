from itertools import product
import os
import re
import json 
import logging
from flask import Flask, config, render_template, jsonify, request, redirect, url_for, session, flash
import mysql
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import get_flashed_messages
from db_connection import get_db_connection
from flask import Flask

app = Flask(__name__)


app.secret_key = os.getenv("SECRET_KEY", "your-default-secure-secret-key")


logging.basicConfig(level=logging.DEBUG)


# Employee Registration 
@app.route('/register', methods=['GET', 'POST'])
def register_employee():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        re_password = request.form['re_password']

        # Validate password strength
        password_regex = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(password_regex, password):
            flash("Password must contain at least 8 characters, one uppercase letter, one number, and one special character.", "danger")
            return redirect(url_for('register_employee'))

        # Check if passwords match
        if password != re_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register_employee'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO employees (first_name, last_name, email, hashed_password) VALUES (%s, %s, %s, %s)",
                (first_name, last_name, email, hashed_password)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login_employee'))
        except Exception as e:
            app.logger.error(f"Error during registration: {str(e)}")
            flash(f"Error registering: {str(e)}", "danger")
            return redirect(url_for('register_employee'))

    return render_template('register_employee.html')


# Employee Login 
@app.route('/login', methods=['GET', 'POST'])
def login_employee():
    get_flashed_messages()
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM employees WHERE email = %s", (email,))
            employee = cursor.fetchone()
            cursor.close()
            conn.close()

            if employee and check_password_hash(employee['hashed_password'], password):
                session['employee_id'] = employee['id']
                session['employee_name'] = employee['first_name']
                session['employee_last_name'] = employee['last_name']
                session['employee_email'] = employee['email']
                session['employee_role'] = employee['role']
                flash(f"Welcome back, {employee['first_name']}!", "success")
                return redirect(url_for('portal_employee'))
            else:
                flash("Invalid email or password.", "danger")
        except Exception as e:
            app.logger.error(f"Error during login: {str(e)}")
            flash(f"Error logging in: {str(e)}", "danger")

    return render_template('login_employee.html')

# Employee Dashboard
@app.route('/')
def index_employee():
    return render_template('index_employee.html')


# Employee Portal
@app.route('/portal')
def portal_employee():
    try:
        if 'employee_id' not in session:
            flash("You must be logged in to view the portal.", "warning")
            return redirect(url_for('login_employee')) 

        # Retrieve employee data from session
        employee_id = session.get('employee_id')

        # Fetch the employee details from the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT first_name, last_name, email, role FROM employees WHERE id = %s", (employee_id,))
        employee = cursor.fetchone()
        cursor.close()
        conn.close()

        if employee:
            # Pass employee data to the portal template
            return render_template('portal_employee.html', 
                                   name=employee['first_name'], 
                                   last_name=employee['last_name'],
                                   email=employee['email'], 
                                   role=employee['role'])
        else:
            flash("Employee not found.", "danger")
            return redirect(url_for('login_employee'))

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('login_employee')) 
    



# Folder to store uploaded product images
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Manage Inventory 
@app.route('/manage_inventory', methods=['GET', 'POST'])
def manage_inventory():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        if 'product_name' in request.form:
            # Handle Add/Update Product
            product_name = request.form['product_name']
            price = float(request.form['price'])
            weight = float(request.form['weight'])
            quantity = int(request.form['stock_quantity'])
            image = request.files.get('product_image')

            # Save image if uploaded
            image_url = None
            if image and image.filename:
                filename = secure_filename(image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)
                image_url = f"{UPLOAD_FOLDER}/{filename}"

            # Insert into the database
            try:
                cursor.execute(
                    "INSERT INTO products (name, price, weight, quantity, image_url) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (product_name, price, weight, quantity, image_url)
                )
                conn.commit()
                flash("Product added successfully!", "success")
            except Exception as e:
                flash(f"Error adding product: {str(e)}", "danger")

        elif 'search_product_name' in request.form:
            # Handle Update Quantity
            search_product_name = request.form['search_product_name']
            additional_quantity = int(request.form['additional_quantity'])

            # Update quantity for the given product
            try:
                cursor.execute(
                    "UPDATE products SET quantity = quantity + %s WHERE name = %s",
                    (additional_quantity, search_product_name)
                )
                conn.commit()
                if cursor.rowcount > 0:
                    flash("Quantity updated successfully!", "success")
                else:
                    flash("Product not found.", "warning")
            except Exception as e:
                flash(f"Error updating quantity: {str(e)}", "danger")

    # Fetch all products to display in the table
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('manage_inventory.html', products=products)


@app.route('/delete_product/<int:product_id>', methods=['GET'])
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete product from the database
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        flash("Product deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting product: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('manage_inventory'))





@app.route('/search_product', methods=['GET'])
def search_product():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    search_query = request.args.get('search_query', '')
    search_results = []
    
    if search_query:
        # Search input button
        cursor.execute("SELECT * FROM products WHERE name LIKE %s", (f"%{search_query}%",))
        search_results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('manage_inventory.html', products=search_results)


# Logout Route
@app.route('/logout')
def logout():
    session.clear()  # Clear session to log the user out
    flash("You have been logged out.", "info")
    return redirect(url_for('index_employee'))


if __name__ == '__main__':
    app.run(debug=True)
