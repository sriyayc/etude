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

#splitting data into chunks for easier processing and embedding
def chunking(text, chunk_size = 500, overlap = 50):
    words = text.split() # so that words dont get cut off in the middle
    chunks = [] 
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size]) # slice the list and join w spaces
        chunks.append(chunk)
    return chunks

def ingest_pdf(pdf_path):
    print(f"Ingesting PDF: {pdf_path}")
    text = extract(pdf_path)
    chunks = chunking(text)
    for i, chunk in enumerate(chunks):
        embedding = embedder.encode(chunk).tolist() #converts NumPy array to python list
        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            ids=[f"{os.path.basename(pdf_path)}_chunk_{i}"]
        )
    print(f"Total chunks created: {len(chunks)} chunks added to chromadb")


if __name__ == "__main__":
    ingest_pdf("data/textbooks/python_notes.pdf")