"""Vector store provider interface.
Rules:
1. Only providers/vectorstore/*.py may import vendor SDKs.
2. Business logic uses providers.factory.get_vectorstore() to get an instance.
3. Methods return primitive types only. No vendor objects leak.
"""
from abc import ABC, abstractmethod

class VectorStoreProvider(ABC):

    @abstractmethod
    def upsert(self, ids: list[str], vectors: list[list[float]], payloads: list[dict]) -> None:
        """Store vectors with their IDs and metadata payloads."""
        pass

    @abstractmethod
    def query(self, vector: list[float], n: int = 5) -> list[dict]:
        """Find n most similar vectors. Returns list of {id, score, payload}."""
        pass

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        """Delete vectors by ID."""
        pass

    @property
    @abstractmethod
    def collection_name(self) -> str:
        """Collection/index name in the vector store."""
        pass
