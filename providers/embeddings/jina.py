"""Jina AI embedding provider."""

import requests
from providers.embeddings.base import EmbeddingProvider
import config


class JinaEmbedder(EmbeddingProvider):
    
    API_URL = "https://api.jina.ai/v1/embeddings"
    MODEL = "jina-embeddings-v3"
    DIMENSION = 1024
    
    def __init__(self):
        if not config.JINA_API_KEY:
            raise ValueError("JINA_API_KEY not set in .env")
        self.headers = {
            "Authorization": f"Bearer {config.JINA_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def embed(self, texts: list[str]) -> list[list[float]]:
        payload = {
            "model": self.MODEL,
            "task": "retrieval.passage",
            "input": texts
        }
        response = requests.post(self.API_URL, headers=self.headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]
    
    @property
    def dimension(self) -> int:
        return self.DIMENSION
    
    @property
    def model_name(self) -> str:
        return self.MODEL
    
if __name__ == "__main__":
    embedder = JinaEmbedder()
    test_texts = ["Data structures store data efficiently."]
    vectors = embedder.embed(test_texts)
    
    print(f"Model: {embedder.model_name}")
    print(f"Dimension: {embedder.dimension}")
    print(f"Number of vectors returned: {len(vectors)}")
    print(f"First vector length: {len(vectors[0])}")
    print(f"First 5 values: {vectors[0][:5]}")