from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime
import os

app = Flask(__name__)

# Function to test the database connection
@app.route('/test-db-connection')
def test_db_connection():
    try:
        # Establish a connection to the MySQL database
        connection = mysql.connector.connect(
            user='root',               # MySQL username
            password='',               # MySQL password (empty string for no password)
            host='10.98.144.3',     # Public IP of MySQL database
            database='userdata'        # Your MySQL database name
        )

        # Create a cursor and run a simple query
        cursor = connection.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        # Return a successful response
        return jsonify({"message": "Database connection successful", "result": result}), 200
    except mysql.connector.Error as err:
        # Return the error if the connection fails
        return jsonify({"error": str(err)}), 500

# Function to get a database connection
def get_db_connection():
    connection = mysql.connector.connect(
        user='root',
        password='',
        host="10.98.144.3",
        database='userdata'
    )
    return connection

# Route for inserting data
@app.route('/insert', methods=['POST'])
def insert_data():
    try:
        # Get the JSON data from the request
        data = request.json
        name = data.get('Name')
        adresse = data.get('Adresse')

        if not name or not adresse:
            return jsonify({'error': 'Name and Adresse are required fields'}), 400

        # Get the current datetime
        current_time = datetime.now()

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert the data into the LockUnit table
        query = "INSERT INTO LockUnit (Name, Adresse, DateTime) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, adresse, current_time))

        # Commit the transaction
        conn.commit()

        # Close the connection
        cursor.close()
        conn.close()

        return jsonify({'message': 'Data inserted successfully!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Start the Flask server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
