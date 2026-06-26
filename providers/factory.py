"""
Provider factory.

The ONLY place business logic touches concrete providers.
Switching providers = changing env variables, not code.
"""

import config
from providers.embeddings.base import EmbeddingProvider
from providers.embeddings.jina import JinaEmbedder
from providers.llm.base import LLMProvider
from providers.llm.groq import GroqLLM
from providers.vectorstore.base import VectorStoreProvider
from providers.vectorstore.qdrant import QdrantStore


def get_embedder() -> EmbeddingProvider:
    """Return embedding provider instance based on EMBEDDING_PROVIDER env var."""
    provider = config.EMBEDDING_PROVIDER
    if provider == "jina":
        return JinaEmbedder()
    raise ValueError(f"Unknown embedding provider: {provider}")


def get_llm() -> LLMProvider:
    """Return LLM provider instance based on LLM_PROVIDER env var."""
    provider = config.LLM_PROVIDER
    if provider == "groq":
        return GroqLLM()
    raise ValueError(f"Unknown LLM provider: {provider}")


def get_vectorstore(dimension: int) -> VectorStoreProvider:
    """
    Return vector store provider instance based on VECTORSTORE_PROVIDER env var.
    
    Requires dimension because vector stores need it for collection creation.
    Pass embedder.dimension to ensure they match.
    """
    provider = config.VECTORSTORE_PROVIDER
    if provider == "qdrant":
        store = QdrantStore(dimension=dimension)
        _verify_dimension_match(store, dimension)
        return store
    raise ValueError(f"Unknown vector store provider: {provider}")


def _verify_dimension_match(store: VectorStoreProvider, expected_dimension: int) -> None:
    """
    Guard against silent dimension mismatches.
    
    If the collection already exists with a different dimension, abort loudly.
    """
    try:
        info = store.client.get_collection(store.collection_name)
        existing_dimension = info.config.params.vectors.size
        if existing_dimension != expected_dimension:
            raise ValueError(
                f"Dimension mismatch: collection '{store.collection_name}' "
                f"has dimension {existing_dimension}, but embedder produces {expected_dimension}. "
                f"Either delete the collection or switch back to the original embedder."
            )
    except ValueError:
        raise
    except Exception:
        pass