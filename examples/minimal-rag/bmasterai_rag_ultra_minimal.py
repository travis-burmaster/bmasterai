#!/usr/bin/env python3
"""
Ultra-Minimal BMasterAI RAG - In-Memory Implementation
No external vector DB required - uses bmasterai + numpy
"""

import os
import gradio as gr
import numpy as np
from bmasterai.logging import configure_logging, get_logger, EventType
from bmasterai.monitoring import get_monitor
from sentence_transformers import SentenceTransformer
import requests

# BMasterAI setup
logger = configure_logging()
monitor = get_monitor()

class UltraMinimalRAG:
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.vectors = []  # In-memory storage
        self.texts = []
        self.sources = []
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        logger.log_event("system", EventType.AGENT_START, "Ultra-minimal RAG started")
    
    def upload(self, file):
        if not file: return "No file"
        
        # Read text
        text = file.read().decode('utf-8') if file.name.endswith('.txt') else "PDF support not included"
        
        # Simple chunking
        chunks = [text[i:i+500] for i in range(0, len(text), 400)]
        
        # Store embeddings
        for chunk in chunks:
            self.vectors.append(self.embedder.encode(chunk))
            self.texts.append(chunk)
            self.sources.append(file.name)
        
        monitor.record_metric("docs_uploaded", 1)
        return f"✅ Uploaded {file.name} ({len(chunks)} chunks)"
    
    def query(self, question):
        if not question or not self.vectors:
            return "No question or documents"
        
        # Find similar chunks
        q_vec = self.embedder.encode(question)
        scores = [np.dot(q_vec, v) / (np.linalg.norm(q_vec) * np.linalg.norm(v)) 
                  for v in self.vectors]
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
        
        # Build context
        context = "\n".join([f"[{self.sources[i]}]: {self.texts[i]}" for i in top_idx])
        
        # Ask Claude
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": f"Context:\n{context}\n\nQ: {question}"}]
            }
        )
        
        monitor.record_metric("queries", 1)
        return resp.json()["content"][0]["text"] if resp.ok else "Error"

# Gradio UI
def create_ui():
    rag = UltraMinimalRAG()
    
    return gr.Interface(
        fn=lambda file, q, action: rag.upload(file) if action == "upload" else rag.query(q),
        inputs=[
            gr.File(label="Upload .txt file"),
            gr.Textbox(label="Question"),
            gr.Radio(["upload", "query"], label="Action")
        ],
        outputs=gr.Textbox(label="Result"),
        title="🚀 Ultra-Minimal BMasterAI RAG",
        description="Simplest possible RAG with BMasterAI logging/monitoring"
    )

if __name__ == "__main__":
    create_ui().launch()
