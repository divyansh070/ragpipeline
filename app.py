
import os
import uuid
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import your custom modules
from ocr_handler import extract_text_from_file, clean_ocr_text
from query_pipeline import extract_core_topic, fetch_top_10_and_answer
from tts_handler import speak_english

app = Flask(__name__)
# Enable CORS so your Flutter app can communicate with this API
CORS(app)

# Configure temporary folders for cloud processing
UPLOAD_FOLDER = 'temp_uploads'
AUDIO_FOLDER = 'temp_audio'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

# ==========================================
# HEALTH CHECK (Verify Azure is running)
# ==========================================
@app.route('/')
def health_check():
    return jsonify({"status": "online", "message": "AI Study Buddy API is running"}), 200

# ==========================================
# ENDPOINT 1: UPLOAD & PROCESS NOTES
# ==========================================
@app.route('/api/upload', methods=['POST'])
def handle_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filepath = None
    try:
        filename = secure_filename(file.filename)
        # Unique ID prevents filename collisions between different users
        unique_id = uuid.uuid4().hex
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(filepath)
        
        # OCR Pipeline
        raw_text = extract_text_from_file(filepath)
        clean_notes = clean_ocr_text(raw_text)
        
        # RAG Pipeline (Topic Extraction)
        core_topic = extract_core_topic(clean_notes)
        
        return jsonify({
            "extracted_notes": clean_notes,
            "topic": core_topic
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        # Cleanup: Remove file from Azure disk after processing
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

# ==========================================
# ENDPOINT 2: CHAT & AUDIO GENERATION
# ==========================================
@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.get_json()
    
    # Validation for Flutter payload
    if not data or not all(k in data for k in ('question', 'notes', 'topic')):
        return jsonify({"error": "Missing required fields: question, notes, topic"}), 400
        
    audio_filepath = None
    try:
        user_question = data['question']
        core_topic = data['topic']
        ocr_notes = data['notes']
        chat_history = data.get('chat_history', [])
        
        # 1. Generate Text Answer
        answer = fetch_top_10_and_answer(core_topic, user_question, ocr_notes, chat_history)
        
        # 2. Generate Audio (Pure English)
        unique_audio_name = f"resp_{uuid.uuid4().hex}.wav"
        audio_filepath = os.path.join(app.config['AUDIO_FOLDER'], unique_audio_name)
        result_path = speak_english(answer, output_filename=audio_filepath)
        
        audio_base64 = None
        if result_path and os.path.exists(result_path):
            with open(result_path, "rb") as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        
        return jsonify({
            "answer": answer,
            "audio_base64": audio_base64
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        # Cleanup: Remove audio file after converting to base64
        if audio_filepath and os.path.exists(audio_filepath):
            os.remove(audio_filepath)

if __name__ == '__main__':
    # Local port 5001 to avoid Mac system conflicts
    app.run(host='0.0.0.0', port=5001, debug=True)