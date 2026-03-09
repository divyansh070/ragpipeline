import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

load_dotenv()

# DIAGNOSTIC: Check if keys are loaded
openrouter_key = os.getenv("OPENROUTER_API_KEY")
google_key = os.getenv("GOOGLE_API_KEY")

if not openrouter_key:
    print("[ERROR] OPENROUTER_API_KEY not found!")
else:
    print(f"[DEBUG] OpenRouter Key active (starts with: {openrouter_key[:10]}...)")

if not google_key:
    print("[ERROR] GOOGLE_API_KEY not found! Embeddings will fail.")
else:
    print(f"[DEBUG] Gemini Key active for embeddings (starts with: {google_key[:5]}...)")

# ==========================================
# 1. SETUP CLOUD CLIENTS
# ==========================================
SEARCH_ENDPOINT = "https://imad-studybuddy-rag.search.windows.net"
SEARCH_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
INDEX_NAME = "curriculum-index"

search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=AzureKeyCredential(SEARCH_KEY))

# OpenRouter Configuration
OR_BASE_URL = "https://openrouter.ai/api/v1"

# Define LLMs using OpenRouter model IDs for reliable chat
primary_llm = ChatOpenAI(
    model="google/gemini-2.0-flash-001",
    openai_api_key=openrouter_key,
    base_url=OR_BASE_URL,
    temperature=0.2
)

fallbacks = [
    ChatOpenAI(model="google/gemini-flash-1.5", openai_api_key=openrouter_key, base_url=OR_BASE_URL, temperature=0.2),
    ChatOpenAI(model="google/gemini-pro-1.5", openai_api_key=openrouter_key, base_url=OR_BASE_URL, temperature=0.2),
    ChatOpenAI(model="anthropic/claude-3-haiku", openai_api_key=openrouter_key, base_url=OR_BASE_URL, temperature=0.2)
]
llm = primary_llm.with_fallbacks(fallbacks)

# Embeddings (Crucial for search)
# Note: Using native Google SDK for embeddings as OpenRouter doesn't support them
gemini_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=google_key,
    task_type="RETRIEVAL_QUERY",
    output_dimensionality=768
)

# ==========================================
# STAGE 1: ANALYZE NOTES
# ==========================================
def _get_text_content(res) -> str:
    """Helper to ensure we get a string from the LLM response content."""
    content = res.content
    if isinstance(content, list):
        return "".join([c if isinstance(c, str) else str(c.get("text", "")) for c in content])
    return str(content)

def extract_core_topic(ocr_notes_text: str) -> str:
    prompt = f"Read these notes and extract the core scientific topic. Return ONLY a 3-7 word search query.\n\nNOTES:\n{ocr_notes_text}"
    return _get_text_content(llm.invoke(prompt)).strip()

def generate_summary(ocr_notes_text: str) -> str:
    prompt = f"Provide a brief, encouraging, 1-2 sentence summary of these notes, acting as a helpful tutor. Speak purely in English.\n\nNOTES:\n{ocr_notes_text}"
    return _get_text_content(llm.invoke(prompt)).strip()

def generate_flash_notes(ocr_notes_text: str) -> str:
    prompt = f"Create a set of concise, high-impact flash notes from the following text. Use bullet points and focus on key concepts and definitions.\n\nTEXT:\n{ocr_notes_text}"
    return _get_text_content(llm.invoke(prompt)).strip()

def generate_quiz(ocr_notes_text: str) -> list:
    import json
    prompt = f"""
    Generate 5 multiple-choice questions based on the following notes. 
    Each question should have 4 options and 1 correct answer.
    Return the output ONLY as a raw JSON list of objects. Do not include markdown formatting like ```json.
    Each object must have:
    - "question": string
    - "options": list of 4 strings
    - "answer": string (must match one of the options)

    NOTES:
    {ocr_notes_text}
    """
    response = llm.invoke(prompt)
    content = _get_text_content(response).strip()
    
    # Clean up markdown if the LLM ignores instructions
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    
    try:
        return json.loads(content.strip())
    except Exception as e:
        print(f"[ERROR] Failed to parse quiz JSON: {e}")
        return []

def generate_flowchart(ocr_notes_text: str) -> str:
    prompt = f"""
    Create a Mermaid.js flowchart representing the key process, hierarchy, or relationship described in the following notes.
    Keep it simple and readable. Return ONLY the mermaid code starting with 'graph TD' or 'flowchart TD'.
    Do not include markdown code blocks.

    NOTES:
    {ocr_notes_text}
    """
    return _get_text_content(llm.invoke(prompt)).strip()

# ==========================================
# STAGE 2: FETCH CHUNKS & CONVERSE (WITH MEMORY)
# ==========================================
def fetch_top_10_and_answer(core_topic: str, user_question: str, ocr_notes: str, chat_history: list = None, screenshot_text: str = None) -> str:
    if chat_history is None:
        chat_history = []
        
    print(f"-> Fetching textbook context for: '{user_question}'")
    
    # 1. Vector Search
    combined_search_query = f"{core_topic} - {user_question}"
    query_vector = gemini_embeddings.embed_query(combined_search_query)
    
    vector_query = VectorizedQuery(vector=query_vector, k_nearest_neighbors=10, fields="content_vector")
    results = search_client.search(search_text=None, vector_queries=[vector_query], select=["content"])
    
    textbook_context = "\n".join([f"--- CHUNK {i+1} ---\n{res['content']}" for i, res in enumerate(results)])
    
    # 2. Build system instructions
    screenshot_context = f"\n    CURRENT IMAGE CONTENT (Prioritize this for the current question):\n    {screenshot_text}\n" if screenshot_text else ""
    
    system_instructions = f"""
    You are an expert, encouraging STEM tutor. You are having an ongoing conversation with a student.
    
    RULES:
    - Base your answers on the provided notes and textbook excerpts.
    - If the student refers to something you said previously, use the chat history to understand the context.
    - Respond in the same language as the student's question.
    - If a 'CURRENT IMAGE CONTENT' is provided, the student is likely asking about that specific image/screenshot. Focus your answer on it while maintaining technical accuracy.
    
    STUDENT'S ORIGINAL NOTES:
    {ocr_notes}
    {screenshot_context}
    
    TOP 10 TEXTBOOK EXCERPTS:
    {textbook_context}
    """
    
    # 3. Assemble message sequence
    messages = [SystemMessage(content=system_instructions)]
    
    for msg in chat_history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content")))
        elif msg.get("role") in ["assistant", "ai"]:
            messages.append(AIMessage(content=msg.get("content")))
            
    messages.append(HumanMessage(content=user_question))
    
    # 4. Generate response
    print("-> Generating tutor response via OpenRouter...")
    response = llm.invoke(messages)
    return _get_text_content(response)