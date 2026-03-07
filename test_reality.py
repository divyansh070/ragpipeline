import os
from ocr_handler import extract_text_from_file, clean_ocr_text
from query_pipeline import extract_core_topic, fetch_top_10_and_answer
from tts_handler import speak_english # <--- We imported your new audio module!

def run_reality_check(pdf_path: str, test_question: str):
    print(f"\n🚀 STARTING REALITY CHECK FOR: {pdf_path}")
    
    # ==========================================
    # STAGE 1: OCR & CLEANUP (The Input)
    # ==========================================
    print("\n--- STAGE 1: READING THE NOTES ---")
    raw_text = extract_text_from_file(pdf_path)
    clean_notes = clean_ocr_text(raw_text)
    print(f"✓ Extracted and cleaned {len(clean_notes)} characters of text from the PDF.")
    
    # ==========================================
    # STAGE 2: TOPIC EXTRACTION (The Bridge)
    # ==========================================
    print("\n--- STAGE 2: EXTRACTING CORE TOPIC ---")
    topic = extract_core_topic(clean_notes)
    
    # ==========================================
    # STAGE 3: DATABASE SEARCH & ANSWER (The Brain)
    # ==========================================
    print("\n--- STAGE 3: CONSULTING THE TEXTBOOK & ANSWERING ---")
    print(f"Question: '{test_question}'")
    answer = fetch_top_10_and_answer(topic, test_question, clean_notes)
    
    print("\n====== 🎓 AI STUDY BUDDY FINAL ANSWER ======")
    print(answer)
    print("============================================\n")

    # ==========================================
    # STAGE 4: AUDIO GENERATION (The Voice)
    # ==========================================
    print("--- STAGE 4: GENERATING AUDIO RESPONSE ---")
    audio_output_name = "reality_check_audio.wav"
    
    # Pass the AI's answer straight into Azure Speech
    result_path = speak_english(answer, output_filename=audio_output_name)
    
    if result_path and os.path.exists(result_path):
        print(f"\n🔊 SUCCESS! Audio securely saved to: {os.path.abspath(result_path)}")
        print("-> Go to your project folder and play the file to hear your AI tutor!")
    else:
        print("\n❌ FAILED to generate audio. Please check your SPEECH_KEY in your .env file.")
        
    print("\n✅ REALITY CHECK COMPLETE.\n")

if __name__ == "__main__":
    # 1. Ensure your PDF is in the same folder!
    notes_file = "fluidization_notes.pdf" 
    
    # 2. Set a relevant test question based on the topic
    question = "According to the book and my notes, what are the primary conditions or characteristics of fluidization?"
    
    if os.path.exists(notes_file):
        run_reality_check(notes_file, question)
    else:
        print(f"❌ Error: Could not find '{notes_file}'. Please place it in your project folder!")