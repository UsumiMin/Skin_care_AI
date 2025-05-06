from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
import json
import google.generativeai as genai
import asyncio
import os


genai.configure(api_key="AIzaSyBd77njV451Td_k5ncchyWiqtsoMXMsSwI")

class AiModel:
    __generation_config__ = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json"
    }
    
    def __init__(self, instruction_filename="skin_mod.txt", model_name="gemini-1.5-flash"):
        with open(instruction_filename, encoding='UTF-8') as f:
            system_instruction = f.read()
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=self.__generation_config__,
            system_instruction=system_instruction
        )

class VisionModel(AiModel):
    async def analyze_skin(self, image_data):
        try:
            with open("temp_upload.jpg", "wb") as f:
                f.write(image_data)
            
            uploaded_file = genai.upload_file("temp_upload.jpg")
            response = await self.model.generate_content_async(
                [uploaded_file]
            )
            os.remove("temp_upload.jpg")
            return response.text  # Возвращаем обычный текст, а не JSON
        except Exception as e:
            return json.dumps({"error": str(e)})  # Возвращаем текст ошибки

class ServerHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        self._loop = asyncio.new_event_loop()
        if self.path == "/":
            self._set_headers(content_type="text/html")
            with open('C:/Users/User/Documents/skin/site/index.html', 'rb') as f:
                self.wfile.write(f.read())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        if self.path == "/upload":
            try:
                content_type = self.headers.get("Content-Type", "")
                if not content_type.startswith("multipart/form-data"):
                    raise ValueError("Invalid content type")
                
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={"REQUEST_METHOD": "POST"}
                )
                
                if "photo" not in form:
                    raise ValueError("No photo uploaded")
                
                file_item = form["photo"]
                if not file_item.file:
                    raise ValueError("Empty file")
                
                image_data = file_item.file.read()
                print("Received image size:", len(image_data), "bytes")
                
                loop = asyncio.get_event_loop()
                asyncio.set_event_loop(loop)
                model = VisionModel()
                result = loop.run_until_complete(model.analyze_skin(image_data))
                self._set_headers()
                self.wfile.write(result.encode())
                
                
            except Exception as e:
                print("Server error:", str(e))
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Invalid endpoint"}).encode())

def run_server():
    port = 8000
    server = HTTPServer(("", port), ServerHandler)
    print(f"Server running on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    print("Server stopped")

if __name__ == "__main__":
    run_server()
