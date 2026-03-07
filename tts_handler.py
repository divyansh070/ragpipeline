import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

# Pull the Speech Key from your .env file
SPEECH_KEY = os.getenv("SPEECH_KEY")

# Hardcoding the region to Southeast Asia to match your Azure deployment
SPEECH_REGION = "southeastasia" 

def speak_english(text: str, output_filename="study_buddy_response.wav") -> str:
    """
    Synthesizes pure English text into an audio file.
    Returns the file path if successful, or None if it fails.
    """
    if not SPEECH_KEY:
        print("Error: SPEECH_KEY is missing from environment variables.")
        return None

    print("-> Generating English audio via Azure Speech (Southeast Asia)...")
    
    try:
        # 1. Setup the Speech Configuration
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        
        # 2. Select a natural-sounding English voice
        # "en-IN-PrabhatNeural" is a great, clear Indian-English male voice. 
        # (Alternatives: "en-US-AriaNeural" for US female, "en-IN-NeerjaNeural" for Indian female)
        speech_config.speech_synthesis_voice_name = "en-IN-PrabhatNeural" 
        
        # 3. Setup the Audio Output Configuration (save to file)
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filename)
        
        # 4. Initialize the Synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        # 5. Execute the TTS request
        result = synthesizer.speak_text_async(text).get()
        
        # 6. Verify the result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"-> Success! Audio saved to {output_filename}")
            return output_filename
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonErrorDetails)
            print(f"-> Speech synthesis canceled or failed: {cancellation_details}")
            return None
            
    except Exception as e:
        print(f"-> Exception during speech synthesis: {e}")
        return None

# ==========================================
# LOCAL TESTING BLOCK
# ==========================================
if __name__ == "__main__":
    print("====== TEXT TO SPEECH TEST ======")
    test_text = "The primary conditions of fluidization involve suspending solid particles in a gas or liquid, transforming them into a fluid-like state."
    
    # Save the test file in the current directory
    output_path = speak_english(test_text, "test_english_audio.wav")
    
    if output_path:
        print(f"Test passed! Open '{output_path}' to hear the voice.")
    else:
        print("Test failed. Check your SPEECH_KEY and Azure region.")
    print("=================================")