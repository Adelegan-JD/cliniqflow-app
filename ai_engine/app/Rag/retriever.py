"""
Higher-level retrieval interface for the RAG engine.
"""

from __future__ import annotations

from typing import List, Sequence

from .indexer import SimpleIndexer
from .models import DocumentChunk, RetrievalResult


class Retriever:
    """
    Retrieve top document chunks using the configured indexer.
    """

    def __init__(
        self,
        chunks: Sequence[DocumentChunk],
        use_embeddings: bool = False,
        openai_api_key: str | None = None,
    ):
        self.use_embeddings = use_embeddings
        self.chunks = list(chunks)

        self.indexer = SimpleIndexer(self.chunks)

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Return the top-k retrieval results for a query.
        """
        return self.indexer.search(query, top_k=top_k)
