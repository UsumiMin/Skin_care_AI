import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import google.generativeai as genai
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Конфигурация
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Настройка прокси для всех запросов через requests
os.environ["HTTP_PROXY"] = 'http://Wzph9KtNFa:CCdLpKEpdC@45.150.35.92:38902'
os.environ["HTTPS_PROXY"] = 'http://Wzph9KtNFa:CCdLpKEpdC@45.150.35.92:38902'

# Инициализация Gemini с кастомной сессией
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY", "AIzaSyBd77njV451Td_k5ncchyWiqtsoMXMsSwI"),
    transport="rest"
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class AiModel:
    __generation_config__ = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json"
    }
    
    def __init__(self, instruction_filename, model_name="gemini-1.5-flash"):
        with open(instruction_filename, encoding='UTF-8') as instruction_file:
            system_instruction = instruction_file.read()

        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=self.__generation_config__,
            system_instruction=system_instruction
        )

class VisionModel(AiModel):
    __instruction_filename__ = "skin_mod.txt"
    
    def __init__(self):
        super().__init__(self.__instruction_filename__)

    def proc_img(self, myfile, prompt=""):
        try:
            result = self.model.generate_content(
                [myfile, "\n\n", prompt]
            )
            return result.text
        except Exception as e:
            app.logger.error(f"Error in proc_img: {str(e)}")
            raise

    def get_description(self, photo_filename, prompt=""):
        try:
            myfile = genai.upload_file(photo_filename)
            response = self.proc_img(myfile, prompt)
            return response
        except Exception as e:
            app.logger.error(f"Error in get_description: {str(e)}")
            raise

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_skin():
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
        
        model = VisionModel()
        response = model.get_description(filepath, prompt)
        
        os.remove(filepath)
        
        try:
            json_response = json.loads(response)
            return jsonify({
                "skin_type": json_response['skin'][0]['skin_type'],
                "problems": json_response['skin'][1]['problems'],
                "recommendations": json_response['skin'][2]['recomendation']
            })
        except json.JSONDecodeError:
            return jsonify({"response": response}), 200
            
    except Exception as e:
        app.logger.error(f"Error in analyze_skin: {str(e)}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)