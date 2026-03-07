import os
import json
import urllib.request
from dotenv import load_dotenv

# 1. Load the API key from your .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: Could not find GOOGLE_API_KEY in your .env file.")
    exit()

print("Connecting to Google's servers to check your API key permissions...\n")

# 2. Hit the Google API directly (bypassing LangChain)
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        
        print("=========================================")
        print(" CHAT/TEXT MODELS AVAILABLE TO YOU ")
        print("=========================================")
        
        # 3. Filter for models that can answer questions (generateContent)
        for model in data.get('models', []):
            methods = model.get('supportedGenerationMethods', [])
            if 'generateContent' in methods:
                # Print the exact string needed for your code
                print(f"✅ {model['name'].replace('models/', '')}")
                
        print("=========================================")
        
except urllib.error.HTTPError as e:
    print(f"API Error: {e.code} - {e.reason}")
    print("Double check that your API key is correct in the .env file.")
except Exception as e:
    print(f"Connection failed: {e}")