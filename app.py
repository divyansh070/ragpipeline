
import os
import uuid
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import your custom modules
from ocr_handler import extract_text_from_file, clean_ocr_text
from query_pipeline import extract_core_topic, fetch_top_10_and_answer, generate_summary
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
    audio_filepath = None
    try:
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(filepath)
        
        # 1. OCR Pipeline (Sequential)
        raw_text = extract_text_from_file(filepath)
        clean_notes = clean_ocr_text(raw_text)
        
        # 2. Parallel Processing for Topic, Summary, and TTS
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            # Fire off topic extraction
            topic_future = executor.submit(extract_core_topic, clean_notes)
            # Fire off summary generation
            summary_future = executor.submit(generate_summary, clean_notes)
            
            # Wait for results
            core_topic = topic_future.result()
            summary = summary_future.result()

        # 3. Audio Generation (Starts as soon as summary is ready)
        unique_audio_name = f"summary_{uuid.uuid4().hex}.wav"
        audio_filepath = os.path.join(app.config['AUDIO_FOLDER'], unique_audio_name)
        result_path = speak_english(summary, output_filename=audio_filepath)

        audio_base64 = None
        if result_path and os.path.exists(result_path):
            with open(result_path, "rb") as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        
        return jsonify({
            "extracted_notes": clean_notes,
            "topic": core_topic,
            "summary": summary,
            "audio_base64": audio_base64
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        # Cleanup
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        if audio_filepath and os.path.exists(audio_filepath):
            os.remove(audio_filepath)

# ==========================================
# ENDPOINT 1.5: OCR ONLY (FOR CHAT IMAGES)
# ==========================================
@app.route('/api/ocr', methods=['POST'])
def handle_ocr():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filepath = None
    try:
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(filepath)
        
        # OCR Pipeline ONLY
        raw_text = extract_text_from_file(filepath)
        clean_notes = clean_ocr_text(raw_text)
        
        return jsonify({
            "extracted_text": clean_notes
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        # Cleanup
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
        
    try:
        user_question = data['question']
        core_topic = data['topic']
        ocr_notes = data['notes']
        chat_history = data.get('chat_history', [])
        screenshot_text = data.get('screenshot_text')
        
        # Generate Text Answer
        answer = fetch_top_10_and_answer(core_topic, user_question, ocr_notes, chat_history, screenshot_text)
        
        # Return only the text to keep this endpoint fast
        return jsonify({
            "answer": answer
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Local port 5001 to avoid Mac system conflicts
    app.run(host='0.0.0.0', port=5001, debug=True)