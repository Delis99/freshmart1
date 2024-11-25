import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="yourpassword",  # Replace with your MySQL password
        database="user_management"
    )
