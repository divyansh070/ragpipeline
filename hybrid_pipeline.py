import os
import uuid
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import TokenTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# ==========================================
# 1. CONFIGURATIONS
# ==========================================
# Load the variables from the .env file
load_dotenv()

# The Free AI Math Engine (LangChain automatically looks for GOOGLE_API_KEY in the environment)
# Your Existing Azure Database
SEARCH_ENDPOINT = "https://imad-studybuddy-rag.search.windows.net"
SEARCH_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY") # <-- Pulls securely from .env
INDEX_NAME = "curriculum-index"

# ==========================================
# 2. INITIALIZE CLIENTS
# ==========================================
# Set up Gemini to generate 768-dimension vectors
gemini_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    task_type="RETRIEVAL_DOCUMENT",  # Optimized for document storage/retrieval
    output_dimensionality=768        # Matches Azure index vector field dimensions
)

search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT, 
    index_name=INDEX_NAME, 
    credential=AzureKeyCredential(SEARCH_KEY)
)

# ==========================================
# 3. CHUNKING & UPLOAD LOGIC
# ==========================================
def process_and_upload(pdf_path):
    print(f"Loading {pdf_path}...")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    text_splitter = TokenTextSplitter(encoding_name="cl100k_base", chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks. Pushing to Azure...")
    
    docs_to_upload = []
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        text = chunk.page_content
        
        # A. Gemini does the vector math (free tier: ~60 req/min → 1.1s delay)
        vector_array = gemini_embeddings.embed_query(text)
        time.sleep(1.1)  # stay within free-tier rate limit
        
        # B. Package exactly as Azure AI Search expects
        docs_to_upload.append({
            "chunk_id": str(uuid.uuid4()), 
            "content": text,
            "content_vector": vector_array
        })
        
        print(f"  Embedded {i+1}/{total} chunks...", end="\r")
        
        # C. Upload in batches of 100 to Azure
        if len(docs_to_upload) % 100 == 0:
            search_client.upload_documents(documents=docs_to_upload)
            print(f"\n  ✓ Uploaded batch of 100 (total processed: {i + 1})")
            docs_to_upload = []

    if docs_to_upload:
        search_client.upload_documents(documents=docs_to_upload)
        
    print(f"Upload complete! 'Ground Truth' is live in Azure.")

# --- EXECUTE ---
if __name__ == "__main__":
    process_and_upload("fludization.pdf") # Point this to your Stanford ML notes