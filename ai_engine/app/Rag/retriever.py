"""
Higher-level retrieval interface for the RAG engine.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from .indexer import EmbeddingIndexer, SimpleIndexer
from .models import DocumentChunk, RetrievalResult


class Retriever:
    """
    Retrieve top document chunks using the configured indexer.
    """

    def __init__(
        self,
        chunks: Sequence[DocumentChunk],
        use_embeddings: bool = False,
        openai_api_key: Optional[str] = None,
    ):
        self.use_embeddings = use_embeddings
        self.chunks = list(chunks)

        if use_embeddings and openai_api_key:
            self.indexer = EmbeddingIndexer(self.chunks, openai_api_key=openai_api_key)
        else:
            self.indexer = SimpleIndexer(self.chunks)

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Return the top-k retrieval results for a query.
        """
        return self.indexer.search(query, top_k=top_k)