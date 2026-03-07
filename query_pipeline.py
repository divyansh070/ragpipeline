

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

load_dotenv()

# ==========================================
# 1. SETUP CLOUD CLIENTS
# ==========================================
SEARCH_ENDPOINT = "https://imad-studybuddy-rag.search.windows.net"
SEARCH_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
INDEX_NAME = "curriculum-index"

search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=AzureKeyCredential(SEARCH_KEY))
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
gemini_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    task_type="RETRIEVAL_QUERY",
    output_dimensionality=768
)

# ==========================================
# STAGE 1: ANALYZE NOTES
# ==========================================
def extract_core_topic(ocr_notes_text: str) -> str:
    prompt = f"Read these notes and extract the core scientific topic. Return ONLY a 3-7 word search query.\n\nNOTES:\n{ocr_notes_text}"
    return llm.invoke(prompt).content.strip()

# ==========================================
# STAGE 2: FETCH CHUNKS & CONVERSE (WITH MEMORY)
# ==========================================
def fetch_top_10_and_answer(core_topic: str, user_question: str, ocr_notes: str, chat_history: list = None) -> str:
    """
    Takes the new question, fetches textbook context, and uses past chat history 
    to maintain a natural, ongoing conversation.
    """
    if chat_history is None:
        chat_history = []
        
    print(f"-> Fetching top 10 chunks for question: '{user_question}'")
    
    # 1. Vector Search
    combined_search_query = f"{core_topic} - {user_question}"
    query_vector = gemini_embeddings.embed_query(combined_search_query)
    
    vector_query = VectorizedQuery(vector=query_vector, k_nearest_neighbors=10, fields="content_vector")
    results = search_client.search(search_text=None, vector_queries=[vector_query], select=["content"])
    
    textbook_context = "\n".join([f"--- CHUNK {i+1} ---\n{res['content']}" for i, res in enumerate(results)])
    
    # 2. Build the System Persona & Context
    system_instructions = f"""
    You are an expert, encouraging STEM tutor. You are having an ongoing conversation with a student.
    
    RULES:
    - Base your answers on the provided notes and textbook excerpts.
    - If the student refers to something you said previously, use the chat history to understand the context.
    - Use conversational Hindi syntax but keep scientific terms in English (Hinglish).
    
    STUDENT'S NOTES:
    {ocr_notes}
    
    TOP 10 TEXTBOOK EXCERPTS:
    {textbook_context}
    """
    
    # 3. Assemble the conversation sequence
    messages = [SystemMessage(content=system_instructions)]
    
    # Inject the past memory into the LLM
    for msg in chat_history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content")))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg.get("content")))
            
    # Add the brand new question at the end
    messages.append(HumanMessage(content=user_question))
    
    # 4. Generate the conversational response
    print("-> Generating conversational Hinglish response...")
    response = llm.invoke(messages)
    return response.content