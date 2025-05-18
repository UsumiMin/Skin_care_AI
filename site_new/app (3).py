# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
COLAB_WEBHOOK_URL = "https://7798-34-57-149-87.ngrok-free.app/"  

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filename)

    try:
        with open(filename, 'rb') as f:
            files = {'photo': f}
            response = requests.post(COLAB_WEBHOOK_URL, files=files)

        os.remove(filename)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Ошибка Colab'}), 500
    except Exception as e:
        if os.path.exists(filename):
            os.remove(filename)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)