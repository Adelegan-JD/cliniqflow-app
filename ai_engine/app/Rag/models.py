from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DocumentRecord:
    """
    A loaded source document before splitting into chunks.
    """
    doc_id: str
    source_file: str
    page: Optional[int]
    text: str
    metadata: Dict[str, Any]


@dataclass
class DocumentChunk:
    """
    A chunk of text used for retrieval.
    """
    chunk_id: str
    source_file: str
    page: Optional[int]
    text: str
    metadata: Dict[str, Any]


@dataclass
class RetrievalResult:
    """
    A retrieval result returned by the search layer.
    """
    chunk_id: str
    source: str
    page: Optional[int]
    score: float
    text: str
    metadata: Dict[str, Any]


@dataclass
class LLMAnswer:
    """
    The final answer object returned by the RAG engine.
    """
    query: str
    answer: str
    sources: List[str]
    retrieved_count: int
    model_used: bool
    retrieved_chunks: List[RetrievalResult]