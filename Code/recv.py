from flask import Flask, request, jsonify
import os
import mysql.connector
from datetime import datetime
import csv

class CSVUploader:
    def __init__(self, upload_folder='uploads', allowed_extensions=None):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions if allowed_extensions is not None else{'csv'}

        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def save_file(self, file):

        if file and self.allowed_file(file.filename):
                filepath = os.path.join(self.upload_folder, file.filename)
                file.save(filepath)
                return filepath
        return None

class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.uploader = CSVUploader()
        self.app.add_url_rule('/upload', 'upload_file', self.upload_file, methods=['POST'])
        self.device_id = None

    def get_db_connection(self):
        connection = mysql.connector.connect(
            user='root',
            password='',
            host='35.228.218.138',
            database='userdata'
        )
        return connection
    
    def is_device_valid(self, device_id):
        #Tjek om device ID eksisterer og er aktivt i DeviceRegistry table.
        try:
            conn = self.get_db_connection
            cursor = conn.cursor()
            query = "SELECT Status FROM DeviceRegistry WHERE DeviceID = %s"
            cursor.execute(query, (device_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result is not None and result[0] == 'active'
        except Exception as e:
            print(f"Error validating device ID: {e}")
            return False
    
    def upload_file(self):

        if 'file' not in request.files:
           return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        device_id = request.headers.get('DeviceID')
        if not self.device_id:
            return jsonify({"error": "DeviceID is missing in the request headers"}), 400
        
        if not self.is_device_valid(device_id):
            return jsonify({"error": "Invalid or inactive device ID"}), 403

        saved_file = self.uploader.save_file(file)
        if saved_file:
            try:
                with open(saved_file, newline='') as csvfile:
                    csv_reader = csv.DictReader(csvfile)
                    conn = self.get_db_connection()
                    cursor = conn.cursor()

                    for row in csv_reader:
                        name = row.get('Name')
                        address = row.get('Adresse')
                        date_time = row.get('DateTime', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        
                        if name and address:
                            query = "INSERT INTO LockUnit (Name, Adresse, DateTime) VALUES (%s, %s, %s)"
                            cursor.execute(query,(name, address, date_time))
                    
                    conn.commit()
                    cursor.close()
                    conn.close()
                
                return jsonify({"message": "Data inserted successfully from CSV!"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def run(self):
        port = int(os.environ.get("PORT", 8080))
        self.app.run(host='0.0.0.0', port=port)

if __name__=='__main__':
    flask_app = FlaskApp()
    flask_app.run()