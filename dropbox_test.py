import os
import time
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import openai
from PyPDF2 import PdfReader
from pptx import Presentation
from docx import Document
import pytesseract
import pdf2image
from tqdm import tqdm
import dropbox
import requests

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
print(DROPBOX_ACCESS_TOKEN)



def download_file_from_dropbox(dropbox_path, local_path):
    """Download a file from Dropbox to a local directory"""
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    
    #try:
    dbx.files_download_to_file(local_path, dropbox_path)
    print(f"Downloaded {dropbox_path} to {local_path}")
    # except dropbox.exceptions.ApiError as e:
    #     print(f"Error downloading {dropbox_path}: {e}")
def extract_text_from_pdf(pdf_path):
    """Extract text from PDF, handling both searchable and scanned documents."""
    reader = PdfReader(pdf_path)
    text_chunks = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
             text_chunks.append((text))

    # Caterpillar manual cant be read, likely because it is scanned. Thus we extract text from images:
    if len(text_chunks)==0:
        print(f"PDF Manual needs to be processed using OCR. Path: {pdf_path}")
        images = pdf2image.convert_from_path(pdf_path)
        for i, img in tqdm(enumerate(images), desc = "Extracting text from images"):
            text = pytesseract.image_to_string(img)
            if text:
                text_chunks.append((text)) 
    corpus_string = "".join(text_chunks)
    return  corpus_string

docs = {
        #"Caterpillar 3500": "Caterpillar-3500-generator-sets-operation-and-maintenance-manual.pdf",
         "Waukesha VGF": ("/Waukesha_VGF_f18g.pdf", "Waukesha_VGF_f18g.pdf"),
        # "Presentation Example": "example.pptx",
        # "Word Document Example": "example.docx"
    }    

for title, (dropbox_path, local_filename) in docs.items():
    local_path = os.path.join(os.getcwd(), local_filename)
    
    # Download file from Dropbox
    download_file_from_dropbox(dropbox_path, local_path)
     # Process the downloaded file
    if local_filename.endswith(".pdf"):
        text_chunks = extract_text_from_pdf(local_path)
print(text_chunks)
