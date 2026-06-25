"""
Embedding provider interface.

Rules:
1. Only providers/embeddings/*.py may import vendor SDKs.
2. Business logic uses providers.factory.get_embedder() to get an instance.
3. Methods return primitive types only. No vendor objects leak.
"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Convert texts to embedding vectors. Returns one vector per text."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier for chunk metadata."""
        pass