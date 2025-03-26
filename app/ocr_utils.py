from PyPDF2 import PdfReader
import pdf2image
import pytesseract
from typing import List, Dict

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF, using OCR if needed"""
    texts = []
    
    # First try regular text extraction
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            texts.append(text.strip())
    
    # If no text found, use OCR
    if not texts:
        images = pdf2image.convert_from_path(pdf_path)
        for img in images:
            text = pytesseract.image_to_string(img).strip()
            if text:
                texts.append(text)
    corpus = "\n".join(texts)
    return corpus

def chunk_text(corpus: str, chunk_size: int = 1000) -> List[Dict]:
    """Chunk text into smaller pieces with metadata"""
    chunks = []

    # Chunking by splitting on paragraphs.
    # Note that if the paragraph is larger than 1000 char, it will still be added as a chunk. 
    paragraphs = [p for p in corpus.split('\n') if p.strip()]
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            chunks.append({
                "text": current_chunk.strip(),
                "chunk_id": f"chunk_{len(chunks)+1}"
            })
            current_chunk = para + "\n\n"
    
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "chunk_id": f"chunk_{len(chunks)+1}"
        })

    return chunks

#print(chunk_text(extract_text_from_pdf("Caterpillar-3500-generator-sets-operation-and-maintenance-manual.pdf")))