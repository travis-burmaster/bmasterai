#!/usr/bin/env python3
"""BMasterAI RAG in ~50 lines - The absolute minimum"""
import os, gradio as gr, numpy as np, requests
from bmasterai.logging import configure_logging, EventType
from bmasterai.monitoring import get_monitor
from sentence_transformers import SentenceTransformer

# Setup
logger = configure_logging()
monitor = get_monitor()
embedder = SentenceTransformer('all-MiniLM-L6-v2')
docs = {"vectors": [], "texts": [], "sources": []}
API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

def upload(file):
    """Upload document and embed chunks"""
    if not file: return "No file"
    text = file.read().decode('utf-8')
    chunks = [text[i:i+500] for i in range(0, len(text), 400)]
    
    for chunk in chunks:
        docs["vectors"].append(embedder.encode(chunk))
        docs["texts"].append(chunk)
        docs["sources"].append(file.name)
    
    logger.log_event("upload", EventType.TASK_COMPLETE, f"Uploaded {file.name}")
    monitor.record_metric("docs", len(chunks))
    return f"✅ Uploaded {len(chunks)} chunks from {file.name}"

def ask(question):
    """Search docs and get AI answer"""
    if not question or not docs["vectors"]: return "Need question & docs"
    
    # Find similar chunks
    q_vec = embedder.encode(question)
    similarities = [np.dot(q_vec, v)/(np.linalg.norm(q_vec)*np.linalg.norm(v)) for v in docs["vectors"]]
    top_3 = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:3]
    context = "\n".join([docs["texts"][i] for i in top_3])
    
    # Ask Claude
    resp = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01"},
        json={"model": "claude-3-5-sonnet-20241022", "max_tokens": 300,
              "messages": [{"role": "user", "content": f"Context:\n{context}\n\nQ: {question}"}]})
    
    monitor.record_metric("queries", 1)
    return resp.json()["content"][0]["text"] if resp.ok else "API Error"

# UI
with gr.Blocks(title="BMasterAI RAG") as app:
    gr.Markdown("# 🚀 BMasterAI RAG in 50 Lines")
    with gr.Row():
        file = gr.File(label="Upload .txt")
        gr.Button("Upload").click(upload, file, gr.Textbox(label="Status"))
    query = gr.Textbox(label="Ask Question")
    gr.Button("Ask").click(ask, query, gr.Textbox(label="Answer", lines=5))

if __name__ == "__main__":
    app.launch()
