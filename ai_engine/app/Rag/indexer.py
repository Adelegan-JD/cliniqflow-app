"""
Build retrieval indexes for document chunks.

This module provides offline keyword retrieval for the bundled clinical guidance.
"""

from __future__ import annotations

from typing import Iterable, List

from .models import DocumentChunk, RetrievalResult


class SimpleIndexer:
    """
    A basic text-matching index for retrieval.
    Useful when embeddings are unavailable.
    """

    def __init__(self, chunks: Iterable[DocumentChunk]):
        self.chunks = list(chunks)

    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        query_tokens = set(_tokenize(query))
        scored: List[RetrievalResult] = []

        for chunk in self.chunks:
            chunk_tokens = set(_tokenize(chunk.text))
            score = len(query_tokens & chunk_tokens) / max(len(query_tokens), 1)
            if score > 0:
                scored.append(
                    RetrievalResult(
                        chunk_id=chunk.chunk_id,
                        source=chunk.source_file if not chunk.page else f"{chunk.source_file} (page {chunk.page})",
                        page=chunk.page,
                        score=score,
                        text=chunk.text,
                        metadata=chunk.metadata,
                    )
                )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]


def _tokenize(text: str) -> List[str]:
    """Tokenize text to lowercase alphanumeric terms."""
    return [token for token in text.lower().split() if token.isalnum()]
