from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime
import os  # Import os to access environment variables

app = Flask(__name__)

# Database connection function
def get_db_connection():
    connection = mysql.connector.connect(
        user='root',
        password='',  # Since you don't use a password, leave this blank
        host='35.228.218.138',
        database='userdata'
    )
    return connection

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
    port = int(os.environ.get('PORT', 8080))  # Use the PORT environment variable
    app.run(debug=True, host='0.0.0.0', port=port)
