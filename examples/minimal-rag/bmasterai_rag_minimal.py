#!/usr/bin/env python3
"""
Minimal BMasterAI RAG Example - Simplified Implementation
Uses bmasterai framework for logging, monitoring, and integrations
"""

import os
import gradio as gr
from bmasterai.logging import configure_logging, get_logger, EventType
from bmasterai.monitoring import get_monitor
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
import PyPDF2

# Configure BMasterAI
logger = configure_logging()
monitor = get_monitor()
monitor.start_monitoring()

class MinimalRAG:
    def __init__(self):
        # Core setup
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.qdrant = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        self.collection = "bmasterai_docs"
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        
        # Initialize collection
        try:
            self.qdrant.recreate_collection(
                self.collection,
                vectors_config={"size": 384, "distance": "Cosine"}
            )
            logger.log_event("system", EventType.AGENT_START, "RAG initialized")
        except Exception as e:
            logger.log_event("system", EventType.ERROR, f"Init error: {e}")
    
    def upload_document(self, file):
        """Upload and process document"""
        if not file:
            return "No file uploaded"
        
        # Extract text
        text = ""
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            text = "\n".join(page.extract_text() for page in reader.pages)
        elif file.name.endswith('.txt'):
            text = file.read().decode('utf-8')
        
        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(text)
        
        # Embed and store
        for i, chunk in enumerate(chunks):
            embedding = self.embedder.encode(chunk)
            self.qdrant.upsert(
                collection_name=self.collection,
                points=[{
                    "id": f"{file.name}_{i}",
                    "vector": embedding.tolist(),
                    "payload": {"text": chunk, "source": file.name}
                }]
            )
        
        # Log and monitor
        logger.log_event("upload", EventType.TASK_COMPLETE, f"Uploaded {file.name}")
        monitor.record_metric("documents_uploaded", 1)
        
        return f"✅ Uploaded {file.name} ({len(chunks)} chunks)"
    
    def search_and_answer(self, query):
        """Search documents and generate answer"""
        if not query:
            return "Please enter a question"
        
        # Search vectors
        query_vector = self.embedder.encode(query)
        results = self.qdrant.search(
            collection_name=self.collection,
            query_vector=query_vector.tolist(),
            limit=3
        )
        
        # Build context
        context = "\n\n".join([
            f"[{r.payload['source']}]: {r.payload['text']}" 
            for r in results
        ])
        
        if not context:
            return "No relevant documents found"
        
        # Generate answer using Anthropic
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1024,
                "messages": [{
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer based on the context:"
                }]
            }
        )
        
        # Log metrics
        monitor.record_metric("queries_processed", 1)
        logger.log_event("query", EventType.TASK_COMPLETE, f"Query: {query[:50]}...")
        
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        else:
            return f"Error: {response.status_code}"

# Create Gradio interface
def create_app():
    rag = MinimalRAG()
    
    with gr.Blocks(title="BMasterAI Minimal RAG") as app:
        gr.Markdown("# 🚀 BMasterAI Minimal RAG System")
        gr.Markdown("Upload documents and ask questions - powered by BMasterAI framework")
        
        with gr.Row():
            with gr.Column():
                file_input = gr.File(label="Upload Document", file_types=[".pdf", ".txt"])
                upload_btn = gr.Button("Upload", variant="primary")
                upload_status = gr.Textbox(label="Status")
                
            with gr.Column():
                query_input = gr.Textbox(label="Ask a Question", lines=2)
                search_btn = gr.Button("Search & Answer", variant="primary")
                answer_output = gr.Textbox(label="Answer", lines=8)
        
        # Event handlers
        upload_btn.click(rag.upload_document, inputs=[file_input], outputs=[upload_status])
        search_btn.click(rag.search_and_answer, inputs=[query_input], outputs=[answer_output])
        query_input.submit(rag.search_and_answer, inputs=[query_input], outputs=[answer_output])
        
        # System metrics display
        with gr.Accordion("System Metrics", open=False):
            metrics_display = gr.JSON(label="BMasterAI Metrics")
            
            def get_metrics():
                return {
                    "system_health": monitor.get_system_health(),
                    "metrics": monitor.get_all_metrics()
                }
            
            gr.Button("Refresh Metrics").click(get_metrics, outputs=[metrics_display])
    
    return app

if __name__ == "__main__":
    # Check environment
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Set ANTHROPIC_API_KEY environment variable")
        print("export ANTHROPIC_API_KEY='your-key-here'")
    
    # Launch app
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)
