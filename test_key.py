
import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found (masked): {api_key[:5]}...{api_key[-5:]}" if api_key else "GOOGLE_API_KEY NOT FOUND")

if api_key:
    try:
        print("\n--- Testing Chat ---")
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        res = llm.invoke("Hello, are you active?")
        print(f"Chat Success: {res.content[:50]}...")
    except Exception as e:
        print(f"Chat Failed: {e}")

    try:
        print("\n--- Testing Embeddings ---")
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key
        )
        vector = embeddings.embed_query("This is a test.")
        print(f"Embeddings Success: Vector size {len(vector)}")
    except Exception as e:
        print(f"Embeddings Failed: {e}")
else:
    print("Skipping tests due to missing key.")
