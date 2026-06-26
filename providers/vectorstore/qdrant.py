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
    DIMENSION = 1024

    def __init__(self):
        if not config.QDRANT_URL or not config.QDRANT_API_KEY:
            raise ValueError("QDRANT_URL and QDRANT_API_KEY must be set in .env")
        self.client = QdrantClient(
            url=config.QDRANT_URL,
            api_key=config.QDRANT_API_KEY
        )
        self._ensure_collection()

    def _ensure_collection(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if self.COLLECTION not in existing:
            self.client.create_collection(
                collection_name=self.COLLECTION,
                vectors_config=VectorParams(
                    size=self.DIMENSION,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Created collection: {self.COLLECTION}")
        else:
            print(f"✅ Collection already exists: {self.COLLECTION}")

    def _build_subject_filter(self, subject: str) -> Filter:
        return Filter(
            must=[
                FieldCondition(
                    key="subject",
                    match=MatchValue(value=subject)
                )
            ]
        )

    def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
        batch_size: int = 100
    ) -> None:
        """
        Store vectors in batches. Every chunk is guaranteed to be stored.

        Expected payload fields per chunk:
        {
            "text":            str,   # raw chunk text
            "subject":         str,   # e.g. "Computer Networks"
            "source":          str,   # filename e.g. "cn_slides.pdf"
            "page":            int,   # page number in source PDF
            "section_heading": str,   # nearest heading above this chunk
            "chunk_index":     int,   # position within the document
        }
        """
        total = len(ids)
        batches_sent = 0

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
            batches_sent += 1
            print(f"  Upserted batch {batches_sent} ({min(i + batch_size, total)}/{total} chunks)")

        print(f"✅ All {total} chunks stored in Qdrant.")

    def query(
        self,
        vector: list[float],
        n: int = 15,
        subject: str = None,
        score_threshold: float = 0.65,
        related_vectors: list[list[float]] = None
    ) -> list[dict]:
        """
        Find the most similar chunks to a query vector.
        Uses query_points (newer Qdrant API — replaces deprecated search()).
        """
        query_filter = self._build_subject_filter(subject) if subject else None

        # Primary search — query_points returns QueryResponse with .points
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

        # Related query expansion — merges results, keeps best score per chunk
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

    def delete(self, ids: list[str]) -> None:
        self.client.delete(
            collection_name=self.COLLECTION,
            points_selector=PointIdsList(points=ids)
        )
        print(f"🗑️  Deleted {len(ids)} chunks from Qdrant.")

    @property
    def collection_name(self) -> str:
        return self.COLLECTION

    def count(self) -> int:
        result = self.client.count(collection_name=self.COLLECTION)
        return result.count

    def fetch_by_source(self, source: str) -> list[dict]:
        records, _ = self.client.scroll(
            collection_name=self.COLLECTION,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source)
                    )
                ]
            ),
            limit=1000,
            with_payload=True
        )
        return [{"id": r.id, "payload": r.payload} for r in records]

    def fetch_by_subject(self, subject: str) -> list[dict]:
        records, _ = self.client.scroll(
            collection_name=self.COLLECTION,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="subject",
                        match=MatchValue(value=subject)
                    )
                ]
            ),
            limit=5000,
            with_payload=True
        )
        return [{"id": r.id, "payload": r.payload} for r in records]
