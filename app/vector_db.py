from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import List, Dict
from ocr_utils import extract_text_from_pdf, chunk_text
import time

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INDEX_NAME = "dropbox-rag"

def get_index():
    """Get or create Pinecone index"""
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        # Wait for index to be ready
        time.sleep(1)
    return pc.Index(INDEX_NAME)

def check_document_exists(document_name: str) -> bool:
    """Check if document is already in the vector database"""
    index = get_index()
    stats = index.describe_index_stats()
    return stats['namespaces'].get(document_name, {}).get('vector_count', 0) > 0

def process_and_store_document(document_name: str, file_path: str):
    """Process a document and store its chunks in the vector DB"""
    # Extract text
    texts, page_numbers = extract_text_from_pdf(file_path)
    
    # Chunk text
    chunks = chunk_text(texts, page_numbers)
    
    # Generate embeddings and store
    index = get_index()
    vectors = []
    
    for chunk in chunks:
        # Generate embedding
        # embedding = client.embeddings.create(
        #     input=chunk["text"],
        #     model="text-embedding-3-small"
        # ).data[0].embedding
        embedding = "This is am mock embedding"
        
        # Prepare vector
        vector_id = f"{document_name}_page_{chunk['page']}_chunk_{chunk['chunk_id']}"
        metadata = {
            "text": chunk["text"],
            "page": chunk["page"],
            "document": document_name
        }
        
        vectors.append((vector_id, embedding, metadata))
    
    # Upsert in batches
    for i in range(0, len(vectors), 100):  # 100 vectors per upsert
        batch = vectors[i:i+100]
        index.upsert(vectors=batch, namespace=document_name)

def query_document(document_name: str, query: str, top_k: int = 3) -> List[Dict]:
    """Query a specific document namespace in the vector DB"""
    index = get_index()
    
    # Generate query embedding
    embedding = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    ).data[0].embedding
    
    # Query the specific document namespace
    results = index.query(
        vector=embedding,
        top_k=top_k,
        namespace=document_name,
        include_metadata=True
    )
    
    # Format results
    return [{
        "text": match.metadata["text"],
        "page": match.metadata["page"],
        "score": match.score
    } for match in results.matches]