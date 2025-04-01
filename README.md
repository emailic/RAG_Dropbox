# RAG Dropbox API

## Overview

This API, which could be a backend for an application, provides a Retrieval-Augmented Generation (RAG) system integrated with Dropbox. It allows users to query documents stored in Dropbox using natural language, with responses generated based on the document content. The system processes documents by extracting text, chunking it, generating embeddings, and storing them in Pinecone vector database for efficient retrieval.

## Architecture and Repository Structure

```
RAG_Dropbox/
│
├── app/                          # Main application directory
│   ├── main.py                   # FastAPI application and routes
│   ├── rag.py                    # RAG query processing logic
│   ├── dropbox_utils.py          # Dropbox API interactions
│   ├── vector_db.py              # Pinecone vector database operations
│   └── text_extraction_utils.py  # Document text extraction utilities
│
├── .env                          # Environment variables (gitignored)
├── .gitignore                    # Git ignore rules
├── poetry.lock                   # Prevents automatic dependency updates
├── pyproject.toml                # Poetry dependencies
└── README.md                     # This documentation
```

### Key Architectural Components:

1. **API Layer** (`main.py`):
   - FastAPI endpoints for document listing and querying
   - Request/response models and error handling

2. **RAG** (`rag.py`):
   - Query processing pipeline
   - Context generation and OpenAI call
   - Response formatting

3. **Document Processing** (`text_extraction_utils.py`):
   - Multi-format text extraction (PDF, DOCX, PPTX)
   - OCR fallback system
   - Text chunking

4. **Storage Integrations**:
   - Dropbox (`dropbox_utils.py`)
   - Pinecone vector database (`vector_db.py`)

5. **Supporting Infrastructure**:
   - Environment configuration (`.env`)
   - Dependency management (`pyproject.toml`)


## Prerequisites

- Python 3.9+
- Poetry (for package management)
- Dropbox account with API access
- Pinecone account
- OpenAI API key
- Tesseract OCR (for image-based document processing)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/RAG_Dropbox.git
   cd RAG_Dropbox
   ```

2. Install system dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt install tesseract-ocr poppler-utils
   
   # MacOS
   brew install tesseract poppler
   
   # Windows (using Chocolatey)
   choco install tesseract
   ```

3. Install Python dependencies using Poetry:
   ```bash
   poetry install
   ```

4. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Environment Variables Setup

Create a `.env` file in the root directory with the following variables:

```ini
DROPBOX_ACCESS_TOKEN=your_dropbox_access_token
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
```

### Obtaining API Keys

1. **Dropbox Access Token**:
   - Go to the [Dropbox Developers Console](https://www.dropbox.com/developers/apps)
   - Create a new app with "Full Dropbox" access
   - Generate an access token

2. **OpenAI API Key**:
   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Create an API key in the "API Keys" section

3. **Pinecone API Key**:
   - Sign up at [Pinecone](https://www.pinecone.io/)
   - Create an index and get your API key from the dashboard

## Running the Application

1. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --app-dir .
   ```
2. The app will be available at http://127.0.0.1:8000

3. To try out the API, we need to navigate to Swagger UI:  http://127.0.0.1:8000/docs

## API Endpoints

### `GET /documents`

List all PDF documents in Dropbox with their processing status.

**Response Example**:
```json
[
  {
    "name": "document1.pdf",
    "processed": true
  },
  {
    "name": "document2.pdf",
    "processed": false
  }
]
```

### `POST /query`

Query a specific document.

**Request Body**:
```json
{
  "document_name": "example.pdf",
  "query": "What is the main topic of this document?"
}
```

**Response Example**:
```json
{
  "query": "What is the main topic of this document?",
  "answer": "The document discusses the operation and maintenance of generator sets.",
  "source_document": "example.pdf",
  "relevant_chunks": [
    {
      "text": "The Caterpillar 3500 generator sets are designed for...",
      "score": 0.92
    }
  ]
}
```

## Technical Approach

1. **Document Processing**:
   - Files are retrieved from Dropbox when needed
   - Text is extracted using appropriate methods for each file type
   - OCR is used as a fallback when direct text extraction fails
   - Text is chunked into manageable pieces (≈1000 characters)

2. **Vector Storage**:
   - Chunks are converted to embeddings using OpenAI's text-embedding-3-small
   - Embeddings are stored in Pinecone with document names as namespaces
   - Each document maintains its own namespace in the vector database

3. **Query Processing**:
   - Queries are converted to embeddings using the same model
   - Three relevant chunks are retrieved from the appropriate document namespace
   - Retrieved context is used to generate answers via OpenAI's GPT-3.5-turbo

## Implementation Notes

### Document Processing Approach

Since no example files were provided for development, we made the following assumptions about document structure:
1. Files would be either:
   - Text-based (with direct text extraction possible)
   - Image-based (requiring OCR for text extraction)

This led to our dual-phase processing strategy:
1. First attempt direct text extraction
2. Only fall back to OCR if no text is found

**Benefits:**
- Improved efficiency by avoiding unnecessary OCR processing
- Faster processing for text-based documents
- Automatic handling of mixed-content documents

### Known Limitations & Notes

1. **PowerPoint Image Extraction**:
   - Current implementation cannot extract text from images embedded in PowerPoint files
   - This limitation appears to be systemic, as even advanced AI tools (ChatGPT, DeepSeek) struggle with this task
   - Text in native PowerPoint text elements is still extracted successfully

2. **OCR Dependencies**:
   - The system requires Tesseract OCR to be installed for image-based processing
   - OCR quality depends on image clarity and resolution

3. **Mixed Image and Text Files**
    - If the files contain both text and images from which text should be extracted, our system will only extract text.
    - The naive solution would be to simply extract text from all files using OCR but we decided to go with a more sophisticated approach (Dual-phase processing strategy presented above)

4. **Performance Considerations**:
   - The first query for a document will be slower as it needs to process the document
   - Subsequent queries will be faster as they use the pre-processed embeddings
   - Document processing includes a 10-second delay to ensure Pinecone availability

5. **File Support**:
   - Currently supports PDF, DOCX, and PPT/PPTX files
   - PDFs with scanned images will be processed using OCR
   - Complex PowerPoint files may have limited text extraction accuracy

6. **Temporary Files**:
   - Downloaded files are stored in a `temp_downloads` directory
   - These files are automatically deleted after processing

7. **Additional Dependencies**:
   - For successful PDF processing, ensure `poppler-utils` is installed

8. **`shape.type` not implemented**
   - This method from `pptx` package plays a crucial role in extracting images from powerpoints. Upon further inspection, it looks like its not implemented in the original package, which might be the root of the issue on why it was so hard to extract images from slides.
   - [This](https://stackoverflow.com/questions/52491656/extracting-images-from-presentation-file) might be a good alternative proposal for extracting images from powerpoint, but due to time constraints didn't get time to try it out. 

9. **Chunking**
   - Chunking is implemented in a way for it to continue concatenating paragraphs until they exceed 1000 characters, but if a single paragraph is longer than 1000 characters, it will become a single chunk. 

10. **No Tests**
   - Due to time constraits, unit and integration tests were not implemented.

11. **No Front End**
   - Due to time constraints, front end was not implemented.


## Testing

You can test the API endpoints using FastAPI's built-in docs interface at `http://localhost:8000/docs`

## Future Improvements

1. Add support for more file types (e.g., TXT, HTML)
2. Implement document versioning
3. Add user authentication
4. Improve OCR accuracy with advanced preprocessing
5. Add batch processing for multiple documents
6. Pinecone namespaces should be named as document ID

## Troubleshooting

1. **Document not found errors**:
   - Ensure the document exists in your Dropbox root folder
   - Check the Dropbox access token has proper permissions
   - Dropbox access token needs to be regenerated daily

2. **OCR issues**:
   - Verify Tesseract OCR is properly installed
   - Check system PATH includes Tesseract executable

3. **Pinecone connection problems**:
   - Verify your Pinecone API key
   - Check the index name matches your Pinecone configuration
   - Ensure your Pinecone index is in the correct region (us-east-1)

