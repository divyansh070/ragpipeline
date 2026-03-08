import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from langchain_openai import ChatOpenAI

load_dotenv()

# OpenRouter Configuration
openrouter_key = os.getenv("OPENROUTER_API_KEY")
OR_BASE_URL = "https://openrouter.ai/api/v1"

# DIAGNOSTIC: Check if keys are loaded
if not openrouter_key:
    print("[ERROR] OPENROUTER_API_KEY not found!")
else:
    print(f"[DEBUG] OpenRouter Key active (starts with: {openrouter_key[:10]}...)")

ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT")
KEY = os.getenv("DOC_INTEL_KEY")

# Initialize LLM with fallbacks from OpenRouter
primary_llm = ChatOpenAI(
    model="google/gemini-2.0-flash-001",
    openai_api_key=openrouter_key,
    base_url=OR_BASE_URL,
    temperature=0.1
)

fallbacks = [
    ChatOpenAI(model="google/gemini-flash-1.5", openai_api_key=openrouter_key, base_url=OR_BASE_URL, temperature=0.1),
    ChatOpenAI(model="anthropic/claude-3-haiku", openai_api_key=openrouter_key, base_url=OR_BASE_URL, temperature=0.1)
]
llm = primary_llm.with_fallbacks(fallbacks)

def extract_text_from_file(file_path: str) -> str:
    print(f"Scanning {file_path} with Azure OCR...")
    client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))
    
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
    prompt = f"""
    You are an expert transcriber. I am providing you with raw OCR text from handwritten engineering notes. 
    
    Your job is to:
    1. Fix obvious cursive spelling mistakes using the surrounding context.
    2. Ignore random bleed-through numbers or gibberish.
    3. IMPORTANT: Extract valid text from inside HTML tags if they contain valid sentences.
    4. Return ONLY the cleaned, perfectly readable markdown text.
    
    RAW OCR TEXT:
    {raw_text}
    """
    
    response = llm.invoke(prompt)
    content = response.content
    if isinstance(content, list):
        return "".join([c if isinstance(c, str) else str(c.get("text", "")) for c in content])
    return str(content)