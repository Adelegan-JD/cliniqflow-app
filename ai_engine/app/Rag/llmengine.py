# """
# RAG engine for medication dosing guidance.

# This module performs retrieval over document chunks and can optionally
# call OpenAI to generate a safe summary answer.
# """

# from __future__ import annotations

# import os
# import re
# from pathlib import Path
# from typing import List, Optional

# from openai import OpenAI

# from .loader import DocumentChunk, load_documents


# STOPWORDS = {
#     "the", "and", "is", "are", "of", "a", "an", "to", "for",
#     "in", "on", "at", "with", "that", "this", "as", "by",
#     "or", "be", "was", "were", "from", "it", "its", "which",
# }


# def _tokenize(text: str) -> List[str]:
#     """Convert text into lowercase tokens and remove punctuation."""
#     text = text.lower()
#     tokens = re.findall(r"\b[a-z0-9]+\b", text)
#     return [token for token in tokens if token not in STOPWORDS]


# def _score_chunk(query_tokens: List[str], chunk_text: str) -> float:
#     """Score a chunk by how many query tokens it shares with the text."""
#     if not query_tokens:
#         return 0.0

#     chunk_tokens = set(_tokenize(chunk_text))
#     common = set(query_tokens) & chunk_tokens
#     return len(common) / max(len(query_tokens), 1)


# def _format_source(chunk: DocumentChunk) -> str:
#     """Create a human-readable source citation for a chunk."""
#     if chunk.page:
#         return f"{chunk.source_file} (page {chunk.page})"
#     return chunk.source_file


# class RAGEngine:
#     """
#     A lightweight retrieval engine for the medication dose knowledge base.
#     """

#     def __init__(
#         self,
#         docs_path: str,
#         openai_api_key: Optional[str] = None,
#         chunk_count: int = 5,
#     ):
#         self.docs_path = Path(docs_path)
#         self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
#         self.chunks = load_documents(self.docs_path)
#         self.top_k = chunk_count
#         self.client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

#     def retrieve(self, query: str, top_k: Optional[int] = None) -> List[dict]:
#         """
#         Retrieve the best-matching document chunks for the query.
#         """
#         query_tokens = _tokenize(query)
#         scored = []

#         for chunk in self.chunks:
#             score = _score_chunk(query_tokens, chunk.text)
#             if score > 0:
#                 scored.append(
#                     {
#                         "chunk_id": chunk.chunk_id,
#                         "source": _format_source(chunk),
#                         "page": chunk.page,
#                         "score": score,
#                         "text": chunk.text,
#                     }
#                 )

#         scored.sort(key=lambda item: item["score"], reverse=True)
#         selected = scored[: top_k or self.top_k]
#         return selected

#     def build_prompt(self, query: str, chunks: List[dict]) -> str:
#         """
#         Build a safe prompt for the LLM using retrieved chunks as evidence.
#         """
#         instructions = (
#             "You are a clinical reference assistant. Use only the information from "
#             "the provided evidence excerpts. Do NOT invent dosage rules or medication "
#             "values. If the information is incomplete, say that the source is insufficient. "
#             "Always remind the user to verify with a licensed clinician."
#         )

#         evidence_text = "\n\n".join(
#             f"Source: {chunk['source']}\nExcerpt:\n{chunk['text']}"
#             for chunk in chunks
#         )

#         return (
#             f"{instructions}\n\n"
#             f"Question:\n{query}\n\n"
#             f"Evidence:\n{evidence_text}\n\n"
#             "Answer using only the evidence above and cite the source names."
#         )

#     def answer(self, query: str, top_k: Optional[int] = None) -> dict:
#         """
#         Retrieve evidence and optionally generate a safe answer via OpenAI.
#         """
#         chunks = self.retrieve(query, top_k=top_k)
#         if not chunks:
#             return {
#                 "query": query,
#                 "answer": "No relevant medication guidance was found in the knowledge base.",
#                 "sources": [],
#                 "retrieved_count": 0,
#                 "model_used": False,
#             }

#         prompt = self.build_prompt(query, chunks)

#         if not self.client:
#             return {
#                 "query": query,
#                 "answer": "OpenAI API key not configured. Retrieval succeeded, but no summary was generated.",
#                 "sources": [chunk["source"] for chunk in chunks],
#                 "retrieved_count": len(chunks),
#                 "model_used": False,
#                 "retrieved_chunks": chunks,
#             }

#         response = self.client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You are a safe clinical evidence assistant."},
#                 {"role": "user", "content": prompt},
#             ],
#             max_tokens=500,
#             temperature=0.0,
#         )

#         answer_text = response.choices[0].message.content.strip()
#         return {
#             "query": query,
#             "answer": answer_text,
#             "sources": [chunk["source"] for chunk in chunks],
#             "retrieved_count": len(chunks),
#             "model_used": True,
#             "retrieved_chunks": chunks,
#         }


# if __name__ == "__main__":
#     # Example usage for local testing only.
#     engine = RAGEngine("app/rag/files")
#     query = "What is the recommended pediatric amoxicillin mg/kg dosing range?"
#     result = engine.answer(query)
#     print("Answer:")
#     print(result["answer"])
#     print("\nSources:")
#     for source in result["sources"]:
#         print("-", source)



"""
Orchestrator for the RAG medication guidance service.

This module loads documents, builds chunks, retrieves evidence,
and optionally generates a safe LLM summary.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from openai import OpenAI

from .chunker import split_chunks
from .loader import load_documents
from .models import DocumentChunk, LLMAnswer, RetrievalResult
from .prompter import build_prompt
from .retriever import Retriever


class RAGEngine:
    """
    High-level RAG engine that can answer medication guidance queries.
    """

    def __init__(
        self,
        docs_path: str,
        use_embeddings: bool = False,
        openai_api_key: Optional[str] = None,
        top_k: int = 5,
    ):
        self.docs_path = Path(docs_path)
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.use_embeddings = use_embeddings
        self.top_k = top_k

        self.documents = load_documents(self.docs_path)
        self.chunks = self._build_chunks(self.documents)
        self.retriever = Retriever(self.chunks, use_embeddings=self.use_embeddings, openai_api_key=self.openai_api_key)

        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

    def _build_chunks(self, documents: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Convert loaded documents into searchable chunks.
        """
        chunk_list: List[DocumentChunk] = []
        for document in self.documents:
            chunk_list.extend(split_chunks(document))
        return chunk_list

    def reload(self) -> None:
        """
        Reload all documents and rebuild the retrieval index.
        """
        self.documents = load_documents(self.docs_path)
        self.chunks = self._build_chunks(self.documents)
        self.retriever = Retriever(self.chunks, use_embeddings=self.use_embeddings, openai_api_key=self.openai_api_key)

    def retrieve(self, query: str) -> List[RetrievalResult]:
        """
        Return the top retrieved evidence for a query.
        """
        return self.retriever.retrieve(query, top_k=self.top_k)

    def answer(self, query: str) -> LLMAnswer:
        """
        Return a safe answer for the query using retrieved evidence.
        """
        results = self.retrieve(query)

        if not results:
            return LLMAnswer(
                query=query,
                answer="No relevant medication guidance was found in the knowledge base.",
                sources=[],
                retrieved_count=0,
                model_used=False,
                retrieved_chunks=[],
            )

        if not self.openai_client:
            return LLMAnswer(
                query=query,
                answer="OpenAI API key is not configured. Retrieval succeeded, but no LLM summary was generated.",
                sources=[result.source for result in results],
                retrieved_count=len(results),
                model_used=False,
                retrieved_chunks=results,
            )

        prompt = build_prompt(query, results)
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a safe clinical evidence assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.0,
        )

        answer_text = response.choices[0].message.content.strip()
        return LLMAnswer(
            query=query,
            answer=answer_text,
            sources=[result.source for result in results],
            retrieved_count=len(results),
            model_used=True,
            retrieved_chunks=results,
        )


if __name__ == "__main__":
    # Example test harness.
    engine = RAGEngine("app/rag/files", use_embeddings=False)
    query = "What are the recommended pediatric amoxicillin dosing guidelines?"
    result = engine.answer(query)
    print("Answer:")
    print(result.answer)
    print("\nSources:")
    for source in result.sources:
        print("-", source)