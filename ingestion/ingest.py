import fitz
import chromadb
from sentence_transformers import SentenceTransformer
import os

embedder= SentenceTransformer("BAAI/bge-small-en-v1.5")
client= chromadb.PersistentClient(path="./chroma_db")
collection=client.get_or_create_collection(name="etude")