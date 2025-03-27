import os
import shutil
import tempfile
from typing import List, Dict

from PyPDF2 import PdfReader
import pdf2image
import pytesseract
from docx import Document
import pptx
from PIL import Image
from zipfile import ZipFile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF, using OCR if needed"""
    texts = []
    
    # First try regular text extraction
    logger.info("Trying PdfReader to extract text...")
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            texts.append(text.strip())
    
    # If no text found, use OCR
    if not texts:

        images = pdf2image.convert_from_path(pdf_path)
        logger.info("No text retrieved the traditional way. Starting OCR on the PDF file...")
        for img in images:
            text = pytesseract.image_to_string(img).strip()
            if text:
                texts.append(text)
    corpus = "\n".join(texts)
    return corpus

def extract_images_from_docx(docx_path: str, temp_dir: str) -> List[str]:
    """
    Extract images from a DOCX file and save them to a temporary directory.
    
    Args:
        docx_path (str): Path to the DOCX file
        temp_dir (str): Temporary directory to store extracted images
    
    Returns:
        List[str]: Paths to extracted image files
    """
    images = []
    try:
        with ZipFile(docx_path, 'r') as docx_zip:
            # DOCX files are zip archives, so we can extract the images
            for file_name in docx_zip.namelist():
                if file_name.startswith('word/media/'):
                    # Extract each image to the temp directory
                    image_filename = file_name.split('/')[-1]
                    extracted_image_path = os.path.join(temp_dir, image_filename)
                    
                    # Extract the file content
                    with docx_zip.open(file_name) as source, open(extracted_image_path, 'wb') as target:
                        target.write(source.read())
                    
                    images.append(extracted_image_path)
    except Exception as e:
        print(f"Error extracting images from DOCX: {e}")
    
    return images



def extract_text_from_docx(docx_path: str) -> str:
    """
    Extract text from DOCX, using OCR if needed.
    """
    texts = []
    images = []
    temp_dir = None
    
    try:
        # Try regular text extraction
        doc = Document(docx_path)
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                texts.append(text)
        
        # If no text found, try OCR on embedded images
        if not texts:
            temp_dir = tempfile.mkdtemp()
            images = extract_images_from_docx(docx_path, temp_dir)
            
            # Process each extracted image
            for image_path in images:
                try:
                    with Image.open(image_path) as img:
                        text = pytesseract.image_to_string(img).strip()
                        if text:
                            texts.append(text)
                except Exception as img_err:
                    print(f"Error processing image {image_path}: {img_err}")
    
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
    
    finally:
        # Cleanup temporary files and directory
        if images and temp_dir:
            for image_path in images:
                if os.path.exists(image_path):
                    os.remove(image_path)
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_err:
                print(f"Error during cleanup: {cleanup_err}")
    
    corpus = "\n".join(texts)
    return corpus

def extract_images_from_pptx(pptx_path: str, temp_dir: str) -> List[str]:
    """
    Extract images from a PowerPoint file and save them to a temporary directory.
    
    Args:
        pptx_path (str): Path to the PowerPoint file
        temp_dir (str): Temporary directory to store extracted images
    
    Returns:
        List[str]: Paths to extracted image files
    """
    images = []
    try:
        prs = pptx.Presentation(pptx_path)
        
        for i, slide in enumerate(prs.slides):
            for shape in slide.shapes:
                # Check if the shape is a picture
                if shape.shape_type == 13:  # MSO_SHAPE_TYPE for pictures
                    image = shape.image
                    image_filename = f"slide_{i}_image_{len(images)}.{image.ext}"
                    image_path = os.path.join(temp_dir, image_filename)
                    
                    # Save the image
                    with open(image_path, 'wb') as f:
                        f.write(image.blob)
                    
                    images.append(image_path)
    except Exception as e:
        print(f"Error extracting images from PowerPoint: {e}")
    
    return images


def extract_text_from_pptx(pptx_path: str) -> str:
    """
    Extract text from PowerPoint file, using OCR for image-based slides.
    """
    texts = []
    images = []
    temp_dir = None
    
    try:
        # Try regular text extraction
        prs = pptx.Presentation(pptx_path)
        
        # Extract text from slides
        for slide in prs.slides:
            # Extract text from text boxes
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text = shape.text.strip()
                    if text:
                        texts.append(text)
                
                # Extract text from tables
                if shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                texts.append(cell.text.strip())
        
        # If no text found, try OCR on embedded images
        if not texts:
            temp_dir = tempfile.mkdtemp()
            images = extract_images_from_pptx(pptx_path, temp_dir)
            
            # Process each extracted image
            for image_path in images:
                try:
                    with Image.open(image_path) as img:
                        text = pytesseract.image_to_string(img).strip()
                        if text:
                            texts.append(text)
                except Exception as img_err:
                    print(f"Error processing image {image_path}: {img_err}")
    
    except Exception as e:
        print(f"Error extracting text from PowerPoint: {e}")
    
    finally:
        # Cleanup temporary files and directory
        if images and temp_dir:
            for image_path in images:
                if os.path.exists(image_path):
                    os.remove(image_path)
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_err:
                print(f"Error during cleanup: {cleanup_err}")
    
    corpus = "\n".join(texts)
    return corpus


def chunk_text(corpus: str, chunk_size: int = 1000) -> List[Dict]:
    """
    Chunk text into smaller pieces with metadata.
    """
    chunks = []
    # paragraph based chunking
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
    

print(chunk_text(extract_text_from_pptx("Abstract.pptx")))
