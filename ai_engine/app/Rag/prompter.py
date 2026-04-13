"""
Build safe, production-ready prompts for the RAG answer generation.
"""

from __future__ import annotations

from typing import List

from .models import RetrievalResult


SYSTEM_INSTRUCTIONS = (
    "You are a clinical evidence assistant. Respond using only the evidence provided below. "
    "Do NOT invent medication doses or dosing rules. "
    "Do NOT provide a prescription. "
    "If the evidence is insufficient, say so clearly. "
    "Always remind the reader to verify with a licensed clinician."
)


def build_prompt(query: str, results: List[RetrievalResult]) -> str:
    """
    Create a safe prompt for the LLM based on retrieved evidence.
    """
    evidence_blocks = []
    for result in results:
        block = (
            f"Source: {result.source}\n"
            f"Score: {result.score:.3f}\n"
            f"Text:\n{result.text}\n"
            "-----"
        )
        evidence_blocks.append(block)

    evidence_text = "\n\n".join(evidence_blocks)

    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"QUESTION:\n{query}\n\n"
        f"EVIDENCE:\n{evidence_text}\n\n"
        "Answer using only the evidence above. Cite the sources by name. "
        "If the evidence does not answer the question, say that the source is insufficient."
    )