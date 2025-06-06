import os
from openai import OpenAI
from typing import Dict, List
from app.vector_db import query_document

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_response(query: str, context: str) -> str | None:
    """Generate answer using OpenAI based on retrieved context"""
    if not context:
        return "No relevant excerpts were retrieved from the document, hence I can't answer your query." 
    
    prompt = f"""Use the following context from the document to answer the question regarding the document. 
    If you don't know the answer, say you don't know.
    
    Context: {context}
    
    Question: {query}
    Answer:"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who answers questions based on the context extracted from the document."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content

def process_query(document_name: str, query: str) -> Dict:
    """Run vector search of a query against a specific document and generate response"""

    chunks = query_document(document_name, query, top_k=3)
    
    context = "\n\n".join([chunk['text'] for chunk in chunks])
    
    answer = generate_response(query, context)
    
    return {
        "query": query,
        "answer": answer,
        "source_document": document_name,
        "relevant_chunks": chunks
    }

#print(process_query("corrupted.pdf", "what is this document about?"))