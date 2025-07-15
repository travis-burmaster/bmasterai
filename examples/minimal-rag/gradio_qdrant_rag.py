#!/usr/bin/env python3
"""
BMasterAI Qdrant Cloud RAG with Gradio UI
Interactive web interface for RAG system using Qdrant Cloud and BMasterAI framework
"""

import os
import json
import time
import uuid
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import threading

# BMasterAI imports
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor

# External dependencies
try:
    import gradio as gr
    import openai
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import pandas as pd
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Install with: pip install gradio openai qdrant-client sentence-transformers numpy pandas")
    exit(1)

@dataclass
class QdrantConfig:
    """Configuration for Qdrant Cloud connection"""
    url: str
    api_key: str
    collection_name: str = "bmasterai_knowledge"
    vector_size: int = 384  # all-MiniLM-L6-v2 embedding size
    distance: Distance = Distance.COSINE
    timeout: int = 30

@dataclass
class RAGConfig:
    """Configuration for RAG system"""
    openai_api_key: str
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.7
    top_k_results: int = 5
    similarity_threshold: float = 0.7

class BMasterAIQdrantRAGUI:
    """
    BMasterAI Qdrant RAG system with Gradio UI
    """
    
    def __init__(self, qdrant_config: QdrantConfig, rag_config: RAGConfig):
        self.qdrant_config = qdrant_config
        self.rag_config = rag_config
        
        # Initialize BMasterAI components
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.agent_id = "qdrant-rag-ui"
        
        # Initialize clients
        self.qdrant_client = None
        self.openai_client = None
        self.embedding_model = None
        
        # UI state
        self.chat_history = []
        self.system_status = "Initializing..."
        self.collection_info = {}
        
        # Initialize system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize all system components"""
        try:
            self.system_status = "🔄 Initializing Qdrant client..."
            self._init_qdrant_client()
            
            self.system_status = "🔄 Initializing OpenAI client..."
            self._init_openai_client()
            
            self.system_status = "🔄 Loading embedding model..."
            self._init_embedding_model()
            
            self.system_status = "🔄 Setting up collection..."
            self.create_collection()
            
            self.system_status = "✅ System ready!"
            
            self.logger.log_event(
                self.agent_id,
                EventType.AGENT_START,
                "BMasterAI Qdrant RAG UI system initialized successfully",
                metadata={
                    "qdrant_url": self.qdrant_config.url,
                    "collection": self.qdrant_config.collection_name,
                    "embedding_model": self.rag_config.embedding_model,
                    "llm_model": self.rag_config.llm_model
                }
            )
            
        except Exception as e:
            self.system_status = f"❌ Initialization failed: {str(e)}"
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"System initialization failed: {str(e)}",
                level=LogLevel.ERROR
            )
    
    def _init_qdrant_client(self):
        """Initialize Qdrant Cloud client"""
        self.qdrant_client = QdrantClient(
            url=self.qdrant_config.url,
            api_key=self.qdrant_config.api_key,
            timeout=self.qdrant_config.timeout
        )
        
        # Test connection
        collections = self.qdrant_client.get_collections()
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_COMMUNICATION,
            "Connected to Qdrant Cloud successfully",
            metadata={"collections_count": len(collections.collections)}
        )
    
    def _init_openai_client(self):
        """Initialize OpenAI client"""
        openai.api_key = self.rag_config.openai_api_key
        self.openai_client = openai
        
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_COMMUNICATION,
            "OpenAI client initialized",
            metadata={"model": self.rag_config.llm_model}
        )
    
    def _init_embedding_model(self):
        """Initialize sentence transformer model for embeddings"""
        self.embedding_model = SentenceTransformer(self.rag_config.embedding_model)
        
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            "Embedding model loaded successfully",
            metadata={"model": self.rag_config.embedding_model}
        )
    
    def create_collection(self) -> str:
        """Create Qdrant collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.qdrant_config.collection_name in collection_names:
                message = f"✅ Collection '{self.qdrant_config.collection_name}' already exists"
                self.logger.log_event(
                    self.agent_id,
                    EventType.TASK_COMPLETE,
                    message
                )
                self._update_collection_info()
                return message
            
            # Create collection
            self.qdrant_client.create_collection(
                collection_name=self.qdrant_config.collection_name,
                vectors_config=VectorParams(
                    size=self.qdrant_config.vector_size,
                    distance=self.qdrant_config.distance
                )
            )
            
            message = f"✅ Created collection '{self.qdrant_config.collection_name}'"
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                message,
                metadata={
                    "vector_size": self.qdrant_config.vector_size,
                    "distance": self.qdrant_config.distance.value
                }
            )
            
            self._update_collection_info()
            return message
            
        except Exception as e:
            error_msg = f"❌ Failed to create collection: {str(e)}"
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                error_msg,
                level=LogLevel.ERROR
            )
            return error_msg
    
    def _update_collection_info(self):
        """Update collection information"""
        try:
            collection_info = self.qdrant_client.get_collection(self.qdrant_config.collection_name)
            self.collection_info = {
                "name": self.qdrant_config.collection_name,
                "vector_size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance.value,
                "points_count": collection_info.points_count,
                "status": collection_info.status.value
            }
        except Exception as e:
            self.collection_info = {"error": str(e)}
    
    def add_documents_from_text(self, documents_text: str, source_name: str = "manual_input") -> str:
        """
        Add documents from text input (one document per line)
        """
        try:
            if not documents_text.strip():
                return "❌ Please provide document text"
            
            # Split text into documents (by lines or paragraphs)
            lines = [line.strip() for line in documents_text.split('\n') if line.strip()]
            
            if not lines:
                return "❌ No valid documents found"
            
            documents = []
            for i, line in enumerate(lines):
                documents.append({
                    "text": line,
                    "metadata": {
                        "source": source_name,
                        "line_number": i + 1,
                        "added_at": datetime.now().isoformat()
                    },
                    "source": source_name
                })
            
            result = self.add_documents(documents)
            self._update_collection_info()
            return result
            
        except Exception as e:
            error_msg = f"❌ Error processing documents: {str(e)}"
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                error_msg,
                level=LogLevel.ERROR
            )
            return error_msg
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Add documents to Qdrant collection"""
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        try:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_START,
                f"Adding {len(documents)} documents to Qdrant",
                metadata={"task_id": task_id, "document_count": len(documents)}
            )
            
            points = []
            
            for i, doc in enumerate(documents):
                # Generate embedding
                embedding = self.embedding_model.encode(doc['text']).tolist()
                
                # Create unique ID
                doc_id = hashlib.md5(doc['text'].encode()).hexdigest()
                
                # Create point
                point = PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "text": doc['text'],
                        "metadata": doc.get('metadata', {}),
                        "timestamp": datetime.now().isoformat(),
                        "source": doc.get('source', 'unknown')
                    }
                )
                points.append(point)
            
            # Upload to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.qdrant_config.collection_name,
                points=points
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            success_msg = f"✅ Successfully added {len(documents)} documents in {duration_ms:.0f}ms"
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                success_msg,
                duration_ms=duration_ms,
                metadata={
                    "task_id": task_id,
                    "document_count": len(documents),
                    "collection": self.qdrant_config.collection_name
                }
            )
            
            self.monitor.track_task_duration(self.agent_id, "add_documents", duration_ms)
            return success_msg
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"❌ Failed to add documents: {str(e)}"
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                error_msg,
                level=LogLevel.ERROR,
                duration_ms=duration_ms,
                metadata={"task_id": task_id}
            )
            
            self.monitor.track_error(self.agent_id, "add_documents")
            return error_msg
    
    def search_similar(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """Search for similar documents in Qdrant"""
        start_time = time.time()
        
        if limit is None:
            limit = self.rag_config.top_k_results
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.qdrant_config.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=self.rag_config.similarity_threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload["text"],
                    "metadata": result.payload.get("metadata", {}),
                    "source": result.payload.get("source", "unknown"),
                    "timestamp": result.payload.get("timestamp")
                })
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Found {len(results)} similar documents",
                duration_ms=duration_ms,
                metadata={
                    "query_length": len(query),
                    "results_count": len(results),
                    "avg_score": np.mean([r["score"] for r in results]) if results else 0
                }
            )
            
            self.monitor.track_task_duration(self.agent_id, "search_similar", duration_ms)
            return results
            
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Failed to search documents: {str(e)}",
                level=LogLevel.ERROR
            )
            
            self.monitor.track_error(self.agent_id, "search_similar")
            return []
    
    def generate_answer(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate answer using OpenAI with retrieved context"""
        start_time = time.time()
        
        try:
            # Prepare context
            context_text = "\n\n".join([
                f"Document {i+1} (Score: {doc['score']:.3f}):\n{doc['text']}"
                for i, doc in enumerate(context_docs)
            ])
            
            # Create prompt
            prompt = f"""Based on the following context documents, please answer the question. If the answer cannot be found in the context, please say so.

Context:
{context_text}

Question: {query}

Answer:"""
            
            # Call OpenAI
            response = self.openai_client.chat.completions.create(
                model=self.rag_config.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.rag_config.max_tokens,
                temperature=self.rag_config.temperature
            )
            
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                self.agent_id,
                EventType.LLM_CALL,
                "Answer generated successfully",
                duration_ms=duration_ms,
                metadata={
                    "tokens_used": tokens_used,
                    "answer_length": len(answer),
                    "context_length": len(context_text)
                }
            )
            
            self.monitor.track_llm_call(
                self.agent_id,
                self.rag_config.llm_model,
                tokens_used,
                duration_ms
            )
            
            return answer
            
        except Exception as e:
            error_msg = f"Error generating answer: {str(e)}"
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                error_msg,
                level=LogLevel.ERROR
            )
            
            self.monitor.track_error(self.agent_id, "generate_answer")
            return error_msg
    
    def chat_interface(self, message: str, history: List[List[str]]) -> Tuple[str, List[List[str]]]:
        """Main chat interface for Gradio"""
        if not message.strip():
            return "", history
        
        try:
            # Step 1: Search for similar documents
            similar_docs = self.search_similar(message)
            
            if not similar_docs:
                response = "I couldn't find relevant information to answer your question. Please try adding some documents first."
                history.append([message, response])
                return "", history
            
            # Step 2: Generate answer
            answer = self.generate_answer(message, similar_docs)
            
            # Add sources information
            sources_info = f"\n\n📚 **Sources ({len(similar_docs)} documents found):**\n"
            for i, doc in enumerate(similar_docs[:3]):  # Show top 3 sources
                sources_info += f"• **Source {i+1}** (Score: {doc['score']:.3f}): {doc['text'][:100]}...\n"
            
            full_response = answer + sources_info
            history.append([message, full_response])
            
            return "", history
            
        except Exception as e:
            error_response = f"Error processing your question: {str(e)}"
            history.append([message, error_response])
            return "", history
    
    def get_system_status(self) -> str:
        """Get current system status"""
        try:
            self._update_collection_info()
            
            status_info = f"""
## 🖥️ System Status: {self.system_status}

### 📊 Collection Information:
- **Name**: {self.collection_info.get('name', 'N/A')}
- **Documents**: {self.collection_info.get('points_count', 0)}
- **Vector Size**: {self.collection_info.get('vector_size', 'N/A')}
- **Distance Metric**: {self.collection_info.get('distance', 'N/A')}
- **Status**: {self.collection_info.get('status', 'N/A')}

### ⚙️ Configuration:
- **Embedding Model**: {self.rag_config.embedding_model}
- **LLM Model**: {self.rag_config.llm_model}
- **Top-K Results**: {self.rag_config.top_k_results}
- **Similarity Threshold**: {self.rag_config.similarity_threshold}

### 🔗 Connections:
- **Qdrant Cloud**: {'✅ Connected' if self.qdrant_client else '❌ Not Connected'}
- **OpenAI API**: {'✅ Connected' if self.openai_client else '❌ Not Connected'}
- **Embedding Model**: {'✅ Loaded' if self.embedding_model else '❌ Not Loaded'}
"""
            return status_info
            
        except Exception as e:
            return f"❌ Error getting system status: {str(e)}"
    
    def get_performance_metrics(self) -> str:
        """Get performance metrics from BMasterAI monitoring"""
        try:
            dashboard = self.monitor.get_agent_dashboard(self.agent_id)
            
            metrics_info = f"""
## 📈 Performance Metrics

### 🎯 Task Performance:
"""
            
            if dashboard.get('performance'):
                for task_name, metrics in dashboard['performance'].items():
                    metrics_info += f"""
**{task_name.replace('_', ' ').title()}:**
- Average Duration: {metrics.get('avg_duration_ms', 0):.2f}ms
- Min Duration: {metrics.get('min_duration_ms', 0):.2f}ms
- Max Duration: {metrics.get('max_duration_ms', 0):.2f}ms
- Total Calls: {metrics.get('total_calls', 0)}
"""
            
            metrics_info += f"""
### 📊 System Metrics:
- **Total Events**: {dashboard.get('metrics', {}).get('total_errors', 0)}
- **Error Count**: {dashboard.get('metrics', {}).get('total_errors', 0)}
- **Agent Status**: {dashboard.get('status', 'Unknown')}
"""
            
            return metrics_info
            
        except Exception as e:
            return f"❌ Error getting performance metrics: {str(e)}"
    
    def create_gradio_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        
        # Custom CSS
        custom_css = """
        .gradio-container {
            max-width: 1400px;
            margin: auto;
        }
        .header-text {
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status-box {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #007bff;
            margin: 10px 0;
        }
        .metric-box {
            background-color: #e8f5e8;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #28a745;
            margin: 10px 0;
        }
        """
        
        with gr.Blocks(css=custom_css, title="BMasterAI Qdrant RAG", theme=gr.themes.Soft()) as demo:
            
            # Header
            gr.HTML("""
            <div class="header-text">
                🚀 BMasterAI Qdrant Cloud RAG System
            </div>
            <div style="text-align: center; margin-bottom: 30px;">
                <p style="font-size: 1.2em; color: #666;">
                    Advanced Retrieval-Augmented Generation with Qdrant Cloud & BMasterAI Framework
                </p>
            </div>
            """)
            
            with gr.Tabs():
                
                # Chat Tab
                with gr.TabItem("💬 Chat Interface", elem_id="chat-tab"):
                    with gr.Row():
                        with gr.Column(scale=3):
                            chatbot = gr.Chatbot(
                                label="RAG Chat Assistant",
                                height=500,
                                show_label=True,
                                elem_id="chatbot",
                                bubble_full_width=False
                            )
                            
                            with gr.Row():
                                msg = gr.Textbox(
                                    label="Your Question",
                                    placeholder="Ask me anything about your documents...",
                                    lines=2,
                                    scale=4
                                )
                                submit_btn = gr.Button("Send", variant="primary", scale=1)
                            
                            with gr.Row():
                                clear_btn = gr.Button("Clear Chat", variant="secondary")
                                example_btn = gr.Button("Load Example Questions", variant="secondary")
                        
                        with gr.Column(scale=1):
                            gr.HTML("<h3>💡 Quick Actions</h3>")
                            
                            # Example questions
                            with gr.Accordion("Example Questions", open=True):
                                example_questions = [
                                    "What is BMasterAI?",
                                    "How does RAG work?",
                                    "What are vector embeddings?",
                                    "Tell me about Qdrant database"
                                ]
                                
                                for question in example_questions:
                                    example_q_btn = gr.Button(f"❓ {question}", size="sm")
                                    example_q_btn.click(
                                        lambda q=question: (q, []),
                                        outputs=[msg, chatbot]
                                    )
                            
                            # Quick stats
                            with gr.Accordion("Quick Stats", open=False):
                                stats_display = gr.Markdown("Loading stats...")
                                refresh_stats_btn = gr.Button("Refresh Stats", size="sm")
                
                # Document Management Tab
                with gr.TabItem("📚 Document Management", elem_id="docs-tab"):
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("<h3>📝 Add Documents</h3>")
                            
                            doc_input = gr.Textbox(
                                label="Documents (one per line)",
                                placeholder="Enter your documents here, one per line...\n\nExample:\nBMasterAI is an advanced AI framework.\nQdrant is a vector database for similarity search.\nRAG combines retrieval with generation.",
                                lines=10
                            )
                            
                            source_name = gr.Textbox(
                                label="Source Name",
                                placeholder="e.g., 'knowledge_base', 'manual_input', 'documentation'",
                                value="manual_input"
                            )
                            
                            add_docs_btn = gr.Button("Add Documents", variant="primary")
                            add_result = gr.Textbox(label="Result", interactive=False)
                        
                        with gr.Column():
                            gr.HTML("<h3>📊 Collection Status</h3>")
                            
                            collection_status = gr.Markdown("Loading collection status...")
                            refresh_collection_btn = gr.Button("Refresh Collection Info")
                            
                            gr.HTML("<h3>🔍 Search Test</h3>")
                            
                            search_query = gr.Textbox(
                                label="Test Search Query",
                                placeholder="Enter a query to test document retrieval..."
                            )
                            search_btn = gr.Button("Search Documents")
                            search_results = gr.JSON(label="Search Results")
                
                # System Status Tab
                with gr.TabItem("🖥️ System Status", elem_id="status-tab"):
                    with gr.Row():
                        with gr.Column():
                            system_status_display = gr.Markdown("Loading system status...")
                            refresh_status_btn = gr.Button("Refresh Status", variant="primary")
                        
                        with gr.Column():
                            performance_metrics = gr.Markdown("Loading performance metrics...")
                            refresh_metrics_btn = gr.Button("Refresh Metrics", variant="primary")
                
                # Configuration Tab
                with gr.TabItem("⚙️ Configuration", elem_id="config-tab"):
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("<h3>🔧 RAG Settings</h3>")
                            
                            top_k_slider = gr.Slider(
                                minimum=1,
                                maximum=20,
                                value=self.rag_config.top_k_results,
                                step=1,
                                label="Top-K Results"
                            )
                            
                            similarity_threshold_slider = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=self.rag_config.similarity_threshold,
                                step=0.05,
                                label="Similarity Threshold"
                            )
                            
                            temperature_slider = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=self.rag_config.temperature,
                                step=0.1,
                                label="LLM Temperature"
                            )
                            
                            max_tokens_slider = gr.Slider(
                                minimum=100,
                                maximum=2000,
                                value=self.rag_config.max_tokens,
                                step=100,
                                label="Max Tokens"
                            )
                            
                            update_config_btn = gr.Button("Update Configuration", variant="primary")
                            config_result = gr.Textbox(label="Configuration Update Result", interactive=False)
                        
                        with gr.Column():
                            gr.HTML("<h3>📋 Current Configuration</h3>")
                            
                            current_config = gr.JSON(
                                value={
                                    "qdrant_url": self.qdrant_config.url,
                                    "collection_name": self.qdrant_config.collection_name,
                                    "embedding_model": self.rag_config.embedding_model,
                                    "llm_model": self.rag_config.llm_model,
                                    "top_k_results": self.rag_config.top_k_results,
                                    "similarity_threshold": self.rag_config.similarity_threshold,
                                    "temperature": self.rag_config.temperature,
                                    "max_tokens": self.rag_config.max_tokens
                                },
                                label="Current Settings"
                            )
            
            # Event handlers
            def submit_message(message, history):
                if message.strip():
                    return self.chat_interface(message, history)
                return message, history
            
            def update_configuration(top_k, similarity_threshold, temperature, max_tokens):
                try:
                    self.rag_config.top_k_results = int(top_k)
                    self.rag_config.similarity_threshold = float(similarity_threshold)
                    self.rag_config.temperature = float(temperature)
                    self.rag_config.max_tokens = int(max_tokens)
                    
                    return "✅ Configuration updated successfully!"
                except Exception as e:
                    return f"❌ Error updating configuration: {str(e)}"
            
            def search_documents(query):
                if not query.strip():
                    return {"error": "Please enter a search query"}
                
                results = self.search_similar(query, limit=5)
                return {
                    "query": query,
                    "results_count": len(results),
                    "results": [
                        {
                            "score": r["score"],
                            "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                            "source": r["source"]
                        }
                        for r in results
                    ]
                }
            
            # Wire up the interface
            submit_btn.click(submit_message, inputs=[msg, chatbot], outputs=[msg, chatbot])
            msg.submit(submit_message, inputs=[msg, chatbot], outputs=[msg, chatbot])
            
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])
            
            add_docs_btn.click(
                self.add_documents_from_text,
                inputs=[doc_input, source_name],
                outputs=[add_result]
            )
            
            refresh_collection_btn.click(
                self.get_system_status,
                outputs=[collection_status]
            )
            
            search_btn.click(
                search_documents,
                inputs=[search_query],
                outputs=[search_results]
            )
            
            refresh_status_btn.click(
                self.get_system_status,
                outputs=[system_status_display]
            )
            
            refresh_metrics_btn.click(
                self.get_performance_metrics,
                outputs=[performance_metrics]
            )
            
            update_config_btn.click(
                update_configuration,
                inputs=[top_k_slider, similarity_threshold_slider, temperature_slider, max_tokens_slider],
                outputs=[config_result]
            )
            
            # Auto-refresh on load
            demo.load(self.get_system_status, outputs=[system_status_display])
            demo.load(self.get_performance_metrics, outputs=[performance_metrics])
            demo.load(self.get_system_status, outputs=[collection_status])
        
        return demo

def main():
    """
    Main function to launch the BMasterAI Qdrant RAG Gradio application
    """
    
    # Configure logging
    configure_logging(log_level=LogLevel.INFO)
    
    # Start monitoring
    monitor = get_monitor()
    monitor.start_monitoring()
    
    # Environment setup instructions
    required_vars = ["QDRANT_URL", "QDRANT_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("\n" + "="*60)
        print("🔑 SETUP REQUIRED:")
        print("Missing environment variables:")
        for var in missing_vars:
            if "QDRANT" in var:
                print(f"  {var}='your-qdrant-{var.lower().split('_')[1]}'")
            else:
                print(f"  {var}='your-openai-api-key'")
        
        print("\nSet them with:")
        for var in missing_vars:
            print(f"export {var}='your-{var.lower().replace('_', '-')}'")
        
        print("\nOr create a .env file with:")
        for var in missing_vars:
            print(f"{var}=your-{var.lower().replace('_', '-')}")
        
        print("\n🌐 Get your keys from:")
        print("  Qdrant Cloud: https://cloud.qdrant.io/")
        print("  OpenAI: https://platform.openai.com/")
        print("="*60 + "\n")
        
        # Continue anyway for demo purposes
    
    # Configuration
    qdrant_config = QdrantConfig(
        url=os.getenv("QDRANT_URL", "https://your-cluster.qdrant.io"),
        api_key=os.getenv("QDRANT_API_KEY", ""),
        collection_name=os.getenv("QDRANT_COLLECTION", "bmasterai_rag_demo")
    )
    
    rag_config = RAGConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        llm_model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
        top_k_results=int(os.getenv("TOP_K_RESULTS", "5"))
    )
    
    try:
        # Create and launch the application
        print("🚀 Initializing BMasterAI Qdrant RAG Gradio application...")
        app = BMasterAIQdrantRAGUI(qdrant_config, rag_config)
        demo = app.create_gradio_interface()
        
        # Launch configuration
        server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
        server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
        share = os.getenv("GRADIO_SHARE", "false").lower() == "true"
        
        print(f"🌐 Launching Gradio interface on {server_name}:{server_port}")
        print(f"📊 System Status: {app.system_status}")
        
        if not missing_vars:
            print("✅ All environment variables configured!")
        else:
            print("⚠️  Some environment variables missing - limited functionality")
        
        demo.launch(
            server_name=server_name,
            server_port=server_port,
            share=share,
            show_error=True,
            debug=False
        )
        
    except Exception as e:
        print(f"❌ Error launching application: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("1. Check your environment variables")
        print("2. Verify Qdrant Cloud and OpenAI API keys")
        print("3. Ensure all dependencies are installed")
        print("4. Check network connectivity")
    
    finally:
        # Stop monitoring
        monitor.stop_monitoring()
        print("\n✅ BMasterAI Qdrant RAG Gradio application stopped!")

if __name__ == "__main__":
    main()