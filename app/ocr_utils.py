from PyPDF2 import PdfReader
import pdf2image
import pytesseract
from typing import Tuple, List, Dict
import os

def extract_text_from_pdf(pdf_path: str) -> Tuple[List[str], List[int]]:
    """Extract text from PDF pages, using OCR if needed"""
    texts = []
    page_numbers = []
    
    # First try regular text extraction
    reader = PdfReader(pdf_path)
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            texts.append(text.strip())
            page_numbers.append(i+1)
    
    # If no text found, use OCR
    if not texts:
        images = pdf2image.convert_from_path(pdf_path)
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img).strip()
            if text:
                texts.append(text)
                page_numbers.append(i+1)
    
    return texts, page_numbers

def chunk_text(texts: List[str], page_numbers: List[int], chunk_size: int = 1000) -> List[Dict]:
    """Chunk text into smaller pieces with metadata"""
    chunks = []
    for text, page in zip(texts, page_numbers):
        # Simple chunking by splitting on paragraphs
        paragraphs = [p for p in text.split('\n') if p.strip()]
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                chunks.append({
                    "text": current_chunk.strip(),
                    "page": page,
                    "chunk_id": f"page_{page}_chunk_{len(chunks)+1}"
                })
                current_chunk = para + "\n\n"
        
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "page": page,
                "chunk_id": f"page_{page}_chunk_{len(chunks)+1}"
            })
    
    return chunks