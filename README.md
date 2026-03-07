# AI Study Buddy API

This API provides OCR, RAG-based chat, and TTS (Text-to-Speech) capabilities for a STEM tutoring application.

## Base URL
`https://studybuddyaiapi-afaxhvgdgmdvawad.southeastasia-01.azurewebsites.net/`

---

## Endpoints

### 1. Health Check
Verify the API is online.
- **Method**: `GET`
- **Path**: `/`
- **Response**:
  ```json
  {
    "status": "online",
    "message": "AI Study Buddy API is running"
  }
  ```

### 2. Upload & Process Notes
Upload document/image, extract text via OCR, and identify the core topic.
- **Method**: `POST`
- **Path**: `/api/upload`
- **Request Type**: `multipart/form-data`
- **Request Body**:
  - `file`: (The PDF, JPG, or PNG file containing notes)
- **Response**:
  ```json
  {
    "extracted_notes": "The cleaned text from the document...",
    "topic": "Identification of the core scientific topic"
  }
  ```

### 3. Chat & Audio Generation
Ask a question based on notes. Returns a Hinglish answer and a Base64-encoded audio file.
- **Method**: `POST`
- **Path**: `/api/chat`
- **Request Type**: `application/json`
- **Request Body**:
  ```json
  {
    "question": "What is the third law of thermodynamics?",
    "notes": "Full text of extracted notes from step 2",
    "topic": "Thermodynamics",
    "chat_history": [
      {"role": "user", "content": "Hi there!"},
      {"role": "assistant", "content": "Hello! What can I help you with today?"}
    ]
  }
  ```
- **Response**:
  ```json
  {
    "answer": "The Hinglish response from the AI...",
    "audio_base64": "GkXfo6NChAF..." 
  }
  ```

---

## Development & Deployment
- **Language**: Python 3.11
- **Framework**: Flask
- **Server**: Gunicorn
- **Deployment**: Azure App Service

### Local Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run locally:
   ```bash
   python app.py
   ```
   (Runs on `http://0.0.0.0:5001`)
