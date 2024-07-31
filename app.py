from flask import Flask, request, send_file, render_template
import fitz  # PyMuPDF for PDF handling
from gtts import gTTS
from pydub import AudioSegment
from io import BytesIO
import os

app = Flask(__name__)

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        pdf_document = fitz.open(pdf_path)
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        pdf_document.close()
    except Exception as e:
        raise RuntimeError(f"An error occurred while extracting text from PDF: {e}")
    return text

def chunk_text(text, max_length=1000):
    """Split text into chunks of a maximum length."""
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def convert_text_to_mp3(text, mp3_path):
    """Convert text to MP3, handling large texts by chunking."""
    try:
        chunks = chunk_text(text)
        combined = AudioSegment.empty()

        for chunk in chunks:
            with BytesIO() as buffer:
                tts = gTTS(chunk, lang='en')
                tts.write_to_fp(buffer)
                buffer.seek(0)  # Go to the start of the BytesIO buffer
                chunk_audio = AudioSegment.from_file(buffer, format="mp3")
                combined += chunk_audio

        combined.export(mp3_path, format="mp3")
        return True
    except Exception as e:
        raise RuntimeError(f"An error occurred while converting text to MP3: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and file.filename.endswith('.pdf'):
        pdf_path = 'uploaded_file.pdf'
        file.save(pdf_path)
        
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            return "No text found in the PDF", 400
        
        mp3_path = 'converted_file.mp3'
        success = convert_text_to_mp3(text, mp3_path)
        if success:
            return send_file(mp3_path, as_attachment=True)
        else:
            return "Failed to convert PDF to MP3", 500
    return "Unsupported file type", 400

if __name__ == "__main__":
    app.run(debug=False)
