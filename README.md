# 🎯 Subtitle Translator - Public Edition

AI-powered subtitle translation for Enigma2 receivers.

## 🚀 Features
- **High-Speed Translation**: Instant text translation via Groq/Gemini.
- **Advanced OCR**: Memory-optimized capture (zero disk wear).
- **Multi-Provider Support**: Choose from Groq, Gemini, OCR.space, and more.
- **Local OCR Support**: Run Tesseract on your PC to offload processing.

## 📥 Installation

```bash
wget -O - --no-check-certificate https://raw.githubusercontent.com/asdrere123-alt/SubtitleTranslator/main/install.sh | /bin/sh
```

## 🔑 API Keys
This is a public version. You must provide your own API keys. You can add them in the plugin settings menu or manually edit the configuration file at:
` /etc/subtitle_keys.conf `

### File Format:
```conf
# You can add MULTIPLE keys for Groq and Gemini (one per line)
# They will be used in rotation to bypass daily limits
GROQ_KEY=gsk_key1_here
GROQ_KEY=gsk_key2_here
GEMINI_KEY=AIzaSy_key1_here
GEMINI_KEY=AIzaSy_key2_here

OCRSPACE_KEY=your_key_here
APININJAS_KEY=your_apininjas_key_here
```

## 💻 Local OCR Setup
To use Local OCR (Tesseract):
1. Copy `local_ocr.py` to your computer.
2. Install dependencies: `pip install flask flask-cors pytesseract pillow`.
3. Install Tesseract-OCR on your OS.
4. Run: `python local_ocr.py`.
5. In plugin settings, set "Local Server URL" to `http://<YOUR_PC_IP>:8000/ocr`.

## 🤝 Credits
Developed by **Ahmed Ibrahim (@asdrere123-alt)**.
