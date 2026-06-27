"""Qdrant vector store provider."""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct, VectorParams, Distance,
    Filter, FieldCondition, MatchValue,
    PointIdsList
)
from providers.vectorstore.base import VectorStoreProvider
import config


class QdrantStore(VectorStoreProvider):

    COLLECTION = "etude"

    def __init__(self, dimension: int):
        if not config.QDRANT_URL or not config.QDRANT_API_KEY:
            raise ValueError("QDRANT_URL and QDRANT_API_KEY must be set in .env")
        self.dimension = dimension
        self.client = QdrantClient(
            url=config.QDRANT_URL,
            api_key=config.QDRANT_API_KEY
        )

    def ensure_collection(self) -> None:
        existing = [c.name for c in self.client.get_collections().collections]
        if self.COLLECTION not in existing:
            self.client.create_collection(
               collection_name=self.COLLECTION,
               vectors_config=VectorParams(
                  size=self.dimension,
                  distance=Distance.COSINE
            )
        )
    
    # Create payload indexes for filtering
        self._ensure_payload_indexes()


    def _ensure_payload_indexes(self) -> None:
        """Create indexes on metadata fields used for filtering."""
        indexed_fields = [
            "content_hash",
            "document_id",
            "subject",
            "semester",
            "topic",
            "unit_number",
            "is_current",
            "source_file",
            "document_type",
            "version",
         ]
    
        for field in indexed_fields:
            try:
                 self.client.create_payload_index(
                     collection_name=self.COLLECTION,
                     field_name=field,
                     field_schema="keyword"
            )
            except Exception:
                 pass

    def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
        batch_size: int = 100
    ) -> None:
        """
        Expected payload schema:
        {
            "chunk_id":         str,
            "document_id":      str,
            "source_file":      str,
            "page_number":      int,
            "chunk_index":      int,
            "chunk_text":       str,
            "document_type":    str,
            "subject":          str,
            "semester":         int,
            "unit_number":      int | None,
            "topic":            str | None,
            "embedding_model":  str,
            "content_hash":     str,
            "version":          int,
            "is_current":       bool,
            "created_at":       str,
        }
        """
        total = len(ids)
        for i in range(0, total, batch_size):
            batch_points = [
                PointStruct(id=id_, vector=vec, payload=pay)
                for id_, vec, pay in zip(
                    ids[i:i + batch_size],
                    vectors[i:i + batch_size],
                    payloads[i:i + batch_size]
                )
            ]
            self.client.upsert(
                collection_name=self.COLLECTION,
                points=batch_points
            )

    def query(
        self,
        vector: list[float],
        n: int = 5,
        filters: dict = None,
        score_threshold: float = 0.0,
        related_vectors: list[list[float]] = None
    ) -> list[dict]:
        query_filter = self._build_filter(filters) if filters else None

        response = self.client.query_points(
            collection_name=self.COLLECTION,
            query=vector,
            limit=n,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True
        )
        results = {
            r.id: {"id": r.id, "score": r.score, "payload": r.payload}
            for r in response.points
        }

        if related_vectors:
            for rel_vec in related_vectors:
                rel_response = self.client.query_points(
                    collection_name=self.COLLECTION,
                    query=rel_vec,
                    limit=n,
                    score_threshold=score_threshold,
                    query_filter=query_filter,
                    with_payload=True
                )
                for r in rel_response.points:
                    if r.id not in results or r.score > results[r.id]["score"]:
                        results[r.id] = {"id": r.id, "score": r.score, "payload": r.payload}

        return sorted(results.values(), key=lambda x: x["score"], reverse=True)

    def delete_by_ids(self, ids: list[str]) -> None:
        self.client.delete(
            collection_name=self.COLLECTION,
            points_selector=PointIdsList(points=ids)
        )

    def delete_by_filter(self, filters: dict) -> int:
        before = self.count()
        self.client.delete(
            collection_name=self.COLLECTION,
            points_selector=self._build_filter(filters)
        )
        after = self.count()
        return before - after

    def fetch_by_filter(self, filters: dict, limit: int = 1000) -> list[dict]:
        records, _ = self.client.scroll(
            collection_name=self.COLLECTION,
            scroll_filter=self._build_filter(filters),
            limit=limit,
            with_payload=True
        )
        return [{"id": r.id, "payload": r.payload} for r in records]

    def count(self) -> int:
        result = self.client.count(collection_name=self.COLLECTION)
        return result.count

    @property
    def collection_name(self) -> str:
        return self.COLLECTION

    def _build_filter(self, filters: dict) -> Filter:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filters.items()
        ]
        return Filter(must=conditions)