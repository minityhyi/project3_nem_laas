from flask import Flask, requests
import os

class CSVuploader:
    def __inint__(self, upload_folder='uploads', allowed extensions=None):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions if allowed_extensions is not None else{'csv'}

        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def save_file(self, file):

        if file and selv.allowed_file(file.filename):
                filepath = os.path.join(self.upload_folder, file.filename)
                file.save(filepath)
                return filepath
        return None

class FlaskApp:

    def __init__(self):
        self.app = Flask(__name__)
        self.uploader = CSVUploader()

        self.app.add_url_rule('/upload', 'upload_file', self.upload_file, methods=['POST'])

    def upload_file(self):

        if 'file' not in request.files:
           return "No file part", 400

        file = request.files['file']

        if file.filename == '':
            return "No selected file", 400

        saved_file = self.uploader.save_file(file)
        if saved_file:
            return f"File saved as {saved_file}", 200
        else:
            return "Invalid file type", 400

    def run(self, host='0.0.0.0', port=5000):
        self.app.run(host=host, port=port)

if __name__=='__main__':
    flask_app = FlaskApp()
    flask_app.run()