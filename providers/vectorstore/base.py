"""Vector store provider interface."""

from abc import ABC, abstractmethod


class VectorStoreProvider(ABC):

    @abstractmethod
    def ensure_collection(self) -> None:
        """Create the collection if it doesn't exist."""
        pass

    @abstractmethod
    def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
        batch_size: int = 100
    ) -> None:
        """Store vectors with their IDs and metadata payloads in batches."""
        pass

    @abstractmethod
    def query(
        self,
        vector: list[float],
        n: int = 5,
        filters: dict = None,
        score_threshold: float = 0.0,
        related_vectors: list[list[float]] = None
    ) -> list[dict]:
        """Find n most similar vectors. Returns list of {id, score, payload}."""
        pass

    @abstractmethod
    def delete_by_ids(self, ids: list[str]) -> None:
        """Delete specific chunks by ID."""
        pass

    @abstractmethod
    def delete_by_filter(self, filters: dict) -> int:
        """Delete chunks matching filter. Returns count deleted."""
        pass

    @abstractmethod
    def fetch_by_filter(self, filters: dict, limit: int = 1000) -> list[dict]:
        """Fetch chunks matching filter."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Total chunks stored."""
        pass

    @property
    @abstractmethod
    def collection_name(self) -> str:
        """Collection/index name."""
        pass