import fitz
import chromadb
from sentence_transformers import SentenceTransformer
import os

embedder = SentenceTransformer("BAAI/bge-small-en-v1.5") #bge model loading
client = chromadb.PersistentClient(path="./chroma_db") 
collection = client.get_or_create_collection(name="etude")

def extract(pdf_path):
    doc = fitz.open(pdf_path) #PyMuPDF
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

if __name__ == "__main__":
    text = extract("data/textbooks/python_notes.pdf")
    print("First 500 characters:")
    print(text[:500])
    print(f"\nTotal characters: {len(text)}")