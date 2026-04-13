"""
Split long documents into smaller searchable chunks.

Chunking ensures retrieval works well for long guideline documents.
"""

from __future__ import annotations

from typing import List

from .models import DocumentChunk, DocumentRecord


def split_chunks(
    record: DocumentRecord,
    chunk_size: int = 250,
    chunk_overlap: int = 60,
) -> List[DocumentChunk]:
    """
    Split a single document into overlapping chunks.

    Args:
        record: the normalized document record
        chunk_size: number of words per chunk
        chunk_overlap: number of words to overlap between chunks
    """
    words = record.text.split()
    if not words:
        return []

    chunks: List[DocumentChunk] = []
    start = 0
    chunk_index = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        text = " ".join(chunk_words).strip()

        if text:
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{record.doc_id}:{chunk_index}",
                    source_file=record.source_file,
                    page=record.page,
                    text=text,
                    metadata={
                        **record.metadata,
                        "chunk_index": chunk_index,
                    },
                )
            )

        chunk_index += 1
        start += chunk_size - chunk_overlap

    return chunks