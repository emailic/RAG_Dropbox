import os
import shutil
import tempfile
from PyPDF2 import PdfReader
import pdf2image
import pytesseract
from docx import Document
from typing import List, Dict
from PIL import Image
from zipfile import ZipFile


def extract_images_from_docx(docx_path: str, temp_dir: str) -> List[str]:
    """Extract images from a DOCX file and save them to a temporary directory."""
    images = []
    with ZipFile(docx_path, 'r') as docx_zip:
        # DOCX files are zip archives, so we can extract the images
        for file_name in docx_zip.namelist():
            if file_name.startswith('word/media/'):
                # Extract each image to the temp directory
                extracted_image_path = os.path.join(temp_dir, file_name.split('/')[-1])
                docx_zip.extract(file_name, temp_dir)
                # Rename the image file correctly
                shutil.move(os.path.join(temp_dir, file_name.split('/')[-1]), extracted_image_path)
                images.append(extracted_image_path)  # Get image file path
    return images


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


def extract_text_from_docx(docx_path: str) -> str:
    """Extract text from DOCX, using OCR if needed"""
    texts = []
    
    # Try regular text extraction
    doc = Document(docx_path)
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            texts.append(text)
    
    # If no text found, assume the document has embedded images and try OCR
    if not texts:
        # Extract images from the DOCX file
        temp_dir = tempfile.mkdtemp()  # Temporary directory to store images
        images = extract_images_from_docx(docx_path, temp_dir)  # Extract images to temp_dir
        print(images) 

        for image_path in images:
            try:
                with Image.open(image_path) as img:
                    text = pytesseract.image_to_string(img).strip()
                    if text:
                        texts.append(text)
            except Exception as e:
                print(f"Error processing image {image_path}: {e}")
        
        # Clean up the temporary directory
        for image_path in images:
            os.remove(image_path)
        shutil.rmtree(temp_dir)  # Use shutil.rmtree() to remove the directory
    
    corpus = "\n".join(texts)
    return corpus


def chunk_text(corpus: str, chunk_size: int = 1000) -> List[Dict]:
    """Chunk text into smaller pieces with metadata"""
    chunks = []

    # Chunking by splitting on paragraphs.
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


# Test with your docx file
print(chunk_text(extract_text_from_docx("example03.docx")))
