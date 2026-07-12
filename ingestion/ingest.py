import os

import chromadb
import fitz
from sentence_transformers import SentenceTransformer


# Load embedding model
embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")

# ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="etude")


def extract(pdf_path):
    """Extract text from a PDF."""
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        full_text += page.get_text()

    doc.close()
    return full_text


def chunking(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks


def ingest_pdf(pdf_path):
    """Ingest a single PDF into ChromaDB."""

    print(f"\n📄 Ingesting: {pdf_path}")

    text = extract(pdf_path)

    if not text.strip():
        print("⚠ Empty PDF. Skipping.")
        return

    chunks = chunking(text)

    for i, chunk in enumerate(chunks):
        embedding = embedder.encode(chunk).tolist()

        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            ids=[f"{pdf_path.replace(os.sep, '_')}_chunk_{i}"],
        )

    print(f"✅ {len(chunks)} chunks added.")


if __name__ == "__main__":

    ROOT_FOLDER = "data/Sem1"

    total = 0

    for folder, _, files in os.walk(ROOT_FOLDER):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(folder, file)
                ingest_pdf(pdf_path)
                total += 1

    print("\n====================================")
    print(f"🎉 Finished ingesting {total} PDF files.")
    print("====================================")