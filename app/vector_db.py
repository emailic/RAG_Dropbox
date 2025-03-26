from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import List, Dict
from ocr_utils import extract_text_from_pdf, chunk_text
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info(f"Starting processing for {document_name}")

    # Extract text
    logger.info("Extracting text from PDF...")
    texts, page_numbers = extract_text_from_pdf(file_path)
    logger.info(f"Extracted text from {len(texts)} pages")

    
    # Chunk text
    logger.info("Chunking text...")
    chunks = chunk_text(texts, page_numbers)
    logger.info(f"Created {len(chunks)} chunks")
    
    # Generate embeddings and store
    index = get_index()
    vectors = []

    logger.info("Generating embeddings...")
    for chunk in chunks:
        # Generate embedding
        # embedding = client.embeddings.create(
        #     input=chunk["text"],
        #     model="text-embedding-3-small"
        # ).data[0].embedding
        embedding = [0.123] * 1536 #mock embedding
        
        # Prepare vector
        vector_id = f"{document_name}_page_{chunk['page']}_chunk_{chunk['chunk_id']}"
        metadata = {
            "text": chunk["text"],
            "page": chunk["page"],
            "document": document_name
        }
        
        vectors.append((vector_id, embedding, metadata))
    
    # Upsert in batches
    logger.info("Upserting to vector database...")

    for i in range(0, len(vectors), 100):  # 100 vectors per upsert
        batch = vectors[i:i+100]
        index.upsert(vectors=batch, namespace=document_name)

def query_document(document_name: str, query: str, top_k: int = 3) -> List[Dict]:
    """Query a specific document namespace in the vector DB"""
    index = get_index()
    
    # Generate query embedding

    # embedding = client.embeddings.create(
    #     input=query,
    #     model="text-embedding-3-small"
    # ).data[0].embedding

    embedding = [0.123456789] * 1536 #mock embedding
    
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