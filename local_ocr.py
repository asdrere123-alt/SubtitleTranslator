# ============================================================
# Local OCR Server for Enigma2 Subtitle Translator
# ============================================================
#
# Prerequisite Installation (Windows/Mac/Linux):
# 1. Install Tesseract-OCR Engine:
#    - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
#    - Mac:     brew install tesseract
#    - Linux:   sudo apt install tesseract-ocr
# 
# 2. Install Python Dependencies:
#    pip install flask flask-cors pytesseract pillow
#
# Usage:
# Run this script on your laptop/PC:
#    python local_ocr.py
#
# Then, in your Enigma2 receiver's plugin settings, set "Local Server URL" to:
#    http://<YOUR_LAPTOP_IP>:8000/ocr
# ============================================================

import base64
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image

import sys
import os

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------
# Automating Tesseract path detection for Windows
# ---------------------------------------------------------
if sys.platform.startswith('win'):
    common_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Users\\' + os.getlogin() + r'\AppData\Local\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
    ]
    found = False
    for path in common_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            found = True
            break
    if not found:
        print("⚠️ Warning: Tesseract not found in common Windows paths.")
        print("Please ensure Tesseract is installed or add it to your PATH.")
# ---------------------------------------------------------

@app.route('/ocr', methods=['POST'])
def process_ocr():
    try:
        data = request.get_json()
        if not data or 'image_base64' not in data:
            return jsonify({"error": "No image_base64 provided"}), 400

        # Parse the base64 string
        img_b64 = data['image_base64']
        
        # Remove header like "data:image/jpeg;base64," if the plugin sent it (though ours doesn't natively)
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]

        # Decode image
        image_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(image_bytes))

        # Perform OCR (Extracting English text optimally for subtitles)
        # psm 6 assumes a single uniform block of text
        text = pytesseract.image_to_string(img, lang='eng', config='--psm 6').strip()
        
        print(f"✅ Extracted Text: {text}")

        # Send back to Enigma2
        return jsonify({
            "success": True,
            "text": text
        }), 200

    except Exception as e:
        print(f"❌ Error during OCR: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "text": ""
        }), 500

if __name__ == '__main__':
    print("🚀 Local OCR Server is starting...")
    print("📡 Listening on ALL network interfaces at port 8000")
    print("📺 Configure your Enigma2 receiver URL to: http://<YOUR_LAPTOP_IP>:8000/ocr")
    # host='0.0.0.0' makes it accessible to the Enigma2 receiver on the local network
    app.run(host='0.0.0.0', port=8000, threaded=True)
