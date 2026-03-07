import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT")
KEY = os.getenv("DOC_INTEL_KEY")

# Initialize the LLM we know works perfectly for your account
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-lite-latest",
    temperature=0.1 # Keep it low so it focuses on grammar, not creativity
)

def extract_text_from_file(file_path: str) -> str:
    print(f"Scanning {file_path} with Azure OCR...")
    client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))
    
    # Determine the file type automatically
    file_extension = file_path.lower().split('.')[-1]
    content_type = "application/pdf" if file_extension == "pdf" else "application/octet-stream"
    
    with open(file_path, "rb") as f:
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=f,
            output_content_format="markdown", 
            content_type=content_type 
        )
        
    return poller.result().content

def clean_ocr_text(raw_text: str) -> str:
    print("Cleaning up cursive mistakes and bleed-through text...")
    
    prompt = f"""
    You are an expert transcriber. I am providing you with raw OCR text from handwritten engineering notes. 
    
    Your job is to:
    1. Fix obvious cursive spelling mistakes using the surrounding context (e.g., if it says "Dynamic lucrou", context implies it should be "Dynamic error").
    2. Ignore random bleed-through numbers (like standalone 5s or 9s) or gibberish.
    3. IMPORTANT: The OCR sometimes hides valid, handwritten sentences inside HTML tags like . You MUST extract the valid text from inside those tags!
    4. Return ONLY the cleaned, perfectly readable markdown text. Do not add conversational filler.
    
    RAW OCR TEXT:
    {raw_text}
    """
    
    response = llm.invoke(prompt)
    return response.content

if __name__ == "__main__":
    test_file_name = "messy_notes.jpg" # This can now be a .jpg or a .pdf!
    
    try:
        # Step 1: Raw Azure OCR (FIXED FUNCTION NAME HERE)
        raw_text = extract_text_from_file(test_file_name)
        
        # Step 2: AI Cleanup
        clean_text = clean_ocr_text(raw_text)
        
        print("\n====== PERFECTED TEXT ======")
        print(clean_text)
        print("============================\n")
        
    except FileNotFoundError:
        print(f"Error: Could not find '{test_file_name}'.")
    except Exception as e:
        print(f"An error occurred: {e}")