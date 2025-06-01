import os
import requests
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Конфигурация
CLOUDFLARE_WORKER_URL = "https://gemini-proxy.batyainzdanii.workers.dev/"
AUTH_TOKEN = "SDvd84$sk55_fspkp"  # Должен совпадать с токеном в Worker
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_to_gemini_via_worker(image_path, prompt):
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": encoded_image
                        }
                    }
                ]
            }]
        }

        # Явное создание сессии
        session = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": str(AUTH_TOKEN)  # Явное преобразование
        }
        
        print("Отправляемые заголовки:", headers)  # Логирование
        
        response = session.post(
            CLOUDFLARE_WORKER_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        return {
            "error": f"Worker error: {response.status_code}",
            "response_text": response.text
        }

    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}
    


@app.route('/analyze', methods=['POST'])
def analyze_skin():  # Убрали async, так как используем синхронные запросы
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(filepath)
        prompt = request.form.get('prompt', 
            "Проанализируй мою кожу по этой фотографии и дай рекомендации по уходу.")
        
        gemini_response = send_to_gemini_via_worker(filepath, prompt)
        
        if "error" in gemini_response:
            return jsonify(gemini_response), 500

        # Адаптируйте под структуру ответа от вашего Worker
        response_data = {
            "skin_type": gemini_response.get("skin", [{}])[0].get("skin_type", "Не определен"),
            "problems": gemini_response.get("skin", [{}])[1].get("problems", []),
            "recommendations": gemini_response.get("skin", [{}])[2].get("recomendation", [])
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000)