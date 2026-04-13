"""
Build retrieval indexes for document chunks.

This module supports both keyword retrieval and optional OpenAI embedding retrieval.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional

from openai import OpenAI

from .models import DocumentChunk, RetrievalResult


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute the cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


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


class EmbeddingIndexer:
    """
    A semantic embedding-based index using OpenAI embeddings.
    """

    def __init__(
        self,
        chunks: Iterable[DocumentChunk],
        openai_api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
    ):
        self.chunks = list(chunks)
        self.embedding_model = embedding_model
        self.client: Optional[OpenAI] = None
        self.vectors: List[List[float]] = []

        if openai_api_key:
            self.client = OpenAI(api_key=openai_api_key)
            self._build_index()

    def _build_index(self) -> None:
        """Compute embeddings for each chunk and store them in memory."""
        texts = [chunk.text for chunk in self.chunks]
        for i in range(0, len(texts), 64):
            batch = texts[i : i + 64]
            response = self.client.embeddings.create(model=self.embedding_model, input=batch)
            for j, item in enumerate(response.data):
                self.vectors.append(item.embedding)

    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        if not self.client or not self.vectors:
            raise RuntimeError("Embedding index is not initialized.")

        query_vector = self.client.embeddings.create(model=self.embedding_model, input=[query]).data[0].embedding
        scored: List[RetrievalResult] = []

        for chunk, vector in zip(self.chunks, self.vectors):
            score = _cosine_similarity(query_vector, vector)
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