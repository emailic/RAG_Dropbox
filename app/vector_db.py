from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import List, Dict
from text_extraction_utils import extract_text_from_pdf,extract_text_from_docx, extract_text_from_pptx, chunk_text
from fastapi import HTTPException

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
    if document_name.lower().endswith('.pdf'):
        logger.info("Extracting text from PDF document...")
        corpus = extract_text_from_pdf(file_path)
    elif document_name.lower().endswith('.docx'):
        logger.info("Extracting text from DOCX document...")
        corpus = extract_text_from_docx(file_path)
    elif document_name.lower().endswith('.ppt') or document_name.lower().endswith('.pptx'):
        logger.info("Extracting text from PPT document...")
        corpus = extract_text_from_pptx(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF and DOCX are supported.")
    logger.info(f"Extracted text from {document_name}.")
    logger.info("Chunking text...")
    chunks = chunk_text(corpus)
    logger.info(f"Created {len(chunks)} chunks")
    index = get_index()
    vectors = []
    logger.info("Generating embeddings...")
    for chunk in chunks:
        embedding = client.embeddings.create(
            input=chunk["text"],
            model="text-embedding-3-small"
        ).data[0].embedding

        vector_id = f"{document_name}_chunk_{chunk['chunk_id']}"
        metadata = {
            "text": chunk["text"],
            "document": document_name
        }
        
        vectors.append((vector_id, embedding, metadata))
    
    logger.info("Upserting to vector database...")

    for i in range(0, len(vectors), 100):  # 100 vectors per upsert
        batch = vectors[i:i+100]
        index.upsert(vectors=batch, namespace=document_name)

    # because at the first run of the app.post("/query"), if the document isn't in db yet 
    # the chunks arent retrieved. Likely because of latency
    time.sleep(10) 

def query_document(document_name: str, query: str, top_k: int = 3) -> List[Dict]:
    """Query a specific document namespace in the vector DB"""
    index = get_index()
    

    embedding = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    ).data[0].embedding
    
    results = index.query(
        vector=embedding,
        top_k= top_k,
        namespace=document_name,
        include_metadata=True
    )
    
    return [{
        "text": match.metadata["text"],
        "score": match.score
    } for match in results.matches]

#print (query_document("Caterpillar-3500-generator-sets-operation-and-maintenance-manual.pdf", "what kind of machine is this?"))