from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from rag import process_query
from dropbox_utils import list_dropbox_files, download_file
from vector_db import check_document_exists, process_and_store_document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

class QueryRequest(BaseModel):
    document_name: str
    query: str

class DocumentResponse(BaseModel):
    name: str
    processed: bool

@app.get("/documents", response_model=List[DocumentResponse])
async def get_documents():
    """List all PDF documents in Dropbox with their status of being stored in Pinecone"""
    try:
        files = list_dropbox_files() 
        documents = []
        for doc in files:
            processed = check_document_exists(doc)
            documents.append({"name": doc, "processed": processed})
        
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def handle_query(request: QueryRequest):
    """Handle a RAG query against a specific document"""
    try:
        logger.info(f"Starting query for document: {request.document_name}")
        
        logger.info("Listing Dropbox files...")
        files = list_dropbox_files()
        if request.document_name not in files:
            raise HTTPException(status_code=404, detail="Document not found in Dropbox")
    
        if not check_document_exists(request.document_name):
            logger.info(f"Document {request.document_name} needs to be chunked, embedded and upserted to vector db.")
            file_path = download_file(request.document_name)
            logger.info(f"Downloaded to {file_path}, starting processing...")
            process_and_store_document(request.document_name, file_path)
            os.remove(file_path)  
            logger.info("Processing complete, temporary file deleted.")
        else:
            logger.info("Document found in vector db.")

        logger.info("Starting query processing...")
        result = process_query(request.document_name, request.query)
        logger.info("Query processed successfully")
        return result
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))