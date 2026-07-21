import os
from dotenv import load_dotenv
load_dotenv()

# Provider selection
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "jina")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
VECTORSTORE_PROVIDER = os.getenv("VECTORSTORE_PROVIDER", "qdrant")

# API keys
JINA_API_KEY = os.getenv("JINA_API_KEY")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# service_role key: bypasses RLS entirely. Server-only, never expose to a
# browser/frontend. Used for the pre-auth SRN lookup during login (see
# db/client.py get_service_client and services/auth_service.py login).
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Public origin of the deployed app. Used to build the redirect target for
# password-reset / email-confirmation links, so it must be the address the
# user's browser can reach -- not localhost, once deployed. This value must
# also be listed under Supabase > Authentication > URL Configuration >
# Redirect URLs, or Supabase will refuse the redirect.
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:3000").rstrip("/")

# Feature flags
USE_RERANKER = os.getenv("USE_RERANKER", "false").lower() == "true"

# Sanity check
def verify_config():
    required = {
        "JINA_API_KEY": JINA_API_KEY,
        "GROQ_API_KEY": GROQ_API_KEY,
        "QDRANT_URL": QDRANT_URL,
        "QDRANT_API_KEY": QDRANT_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "SUPABASE_SERVICE_ROLE_KEY": SUPABASE_SERVICE_ROLE_KEY,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise ValueError(f"Missing env variables: {missing}")
    print("All env variables loaded")

if __name__ == "__main__":
    verify_config()
