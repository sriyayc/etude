"""Voyage AI embedding provider."""

import requests
from providers.embeddings.base import EmbeddingProvider
import config
class VoyageEmbedder(EmbeddingProvider)