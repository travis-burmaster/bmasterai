"""Agentic RAG example using BMasterAI logging.

This script demonstrates how to build a simple retrieval-augmented generation
(RAG) pipeline instrumented with BMasterAI's structured logging utilities. It
indexes in-memory documents with SentenceTransformers and FAISS, retrieves
relevant context for a query, and calls the Anthropic API to generate an answer.

The example is intentionally lightweight and focuses on showing how logging
can trace agent start/stop events, document ingestion, and question answering
steps. To run it, ensure the following packages are installed:

- sentence_transformers
- faiss-cpu
- requests

An Anthropic API key must be available in the ``ANTHROPIC_API_KEY`` environment
variable.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import List

import faiss
import requests
from sentence_transformers import SentenceTransformer

from bmasterai.logging import (
    configure_logging,
    get_logger,
    LogLevel,
    EventType,
)


@dataclass
class Document:
    """Simple data structure holding a text document and its identifier."""

    id: str
    text: str


class AgenticRAG:
    """Minimal agentic RAG pipeline with BMasterAI logging."""

    def __init__(self) -> None:
        configure_logging(log_level=LogLevel.INFO)
        self.logger = get_logger()
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatIP(self.embedder.get_sentence_embedding_dimension())
        self.docs: List[Document] = []

        self.logger.log_event(
            agent_id="agentic_rag",
            event_type=EventType.AGENT_START,
            message="Initialized Agentic RAG pipeline",
        )

    def add_documents(self, documents: List[Document]) -> None:
        """Embed and index documents."""
        texts = [doc.text for doc in documents]
        embeddings = self.embedder.encode(texts, convert_to_numpy=True)
        self.index.add(embeddings)
        self.docs.extend(documents)

        self.logger.log_event(
            agent_id="agentic_rag",
            event_type=EventType.TASK_COMPLETE,
            message=f"Indexed {len(documents)} documents",
        )

    def answer(self, question: str, k: int = 3) -> str:
        """Retrieve context for ``question`` and generate an answer."""
        start = time.time()
        self.logger.log_event(
            agent_id="agentic_rag",
            event_type=EventType.TASK_START,
            message=f"Answering question: {question}",
        )

        q_emb = self.embedder.encode([question], convert_to_numpy=True)
        scores, indices = self.index.search(q_emb, k)
        context_parts = [self.docs[i].text for i in indices[0] if i != -1]
        context = "\n\n".join(context_parts)

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 512,
            "messages": [
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer succinctly.",
                }
            ],
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        resp = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        if resp.status_code == 200:
            answer = resp.json()["content"][0]["text"]
        else:
            answer = f"Error from API: {resp.status_code}"

        duration = (time.time() - start) * 1000
        self.logger.log_event(
            agent_id="agentic_rag",
            event_type=EventType.TASK_COMPLETE,
            message="Answered question",
            metadata={"question": question},
            duration_ms=duration,
        )
        return answer

    def shutdown(self) -> None:
        self.logger.log_event(
            agent_id="agentic_rag",
            event_type=EventType.AGENT_STOP,
            message="Shutting down Agentic RAG pipeline",
        )


def main() -> None:
    rag = AgenticRAG()
    rag.add_documents(
        [
            Document(id="1", text="BMasterAI provides observability tools for AI applications."),
            Document(id="2", text="Retrieval augmented generation combines search with generation."),
            Document(id="3", text="Anthropic's Claude models are capable language models."),
        ]
    )

    question = "What does RAG stand for and which model is used?"
    answer = rag.answer(question)
    print(answer)

    rag.shutdown()


if __name__ == "__main__":
    main()
