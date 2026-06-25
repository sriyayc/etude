import os
from dotenv import load_dotenv

load_dotenv()

# Provider selection
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "jina")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
VECTORSTORE_PROVIDER = os.getenv("VECTORSTORE_PROVIDER", "qdrant")

# API keys
JINA_API_KEY = os.getenv("JINA_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Sanity check
def verify_config():
    required = {
        "JINA_API_KEY": JINA_API_KEY,
        "GROQ_API_KEY": GROQ_API_KEY,
        "QDRANT_URL": QDRANT_URL,
        "QDRANT_API_KEY": QDRANT_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise ValueError(f"Missing env variables: {missing}")
    print("✅ All env variables loaded")

if __name__ == "__main__":
    verify_config()