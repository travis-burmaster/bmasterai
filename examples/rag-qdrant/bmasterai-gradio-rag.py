#!/usr/bin/env python3
"""
BMasterAI RAG Example with Anthropic API and Qdrant Vector Database
Document upload, vectorization, and semantic search through Gradio UI

This implementation uses the BMasterAI framework for enhanced logging,
monitoring, and integration capabilities.
"""

import os
import json
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

import gradio as gr
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import PyPDF2
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Import BMasterAI framework components
from bmasterai import (
    configure_logging,
    get_logger,
    LogLevel,
    EventType,
    get_monitor,
    get_integration_manager
)
from bmasterai.integrations import SlackConnector, EmailConnector


@dataclass
class BMasterAIRAGConfig:
    """Configuration for BMasterAI RAG system"""
    anthropic_api_key: str
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    model_name: str = "claude-3-5-sonnet-20241022"
    embedding_model: str = "all-MiniLM-L6-v2"
    collection_name: str = "bmasterai_documents"
    max_tokens: int = 4096
    temperature: float = 0.7
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7
    system_prompt: str = """You are a helpful AI assistant that answers questions based on provided documents. 
    Use the context provided to answer questions accurately. If the answer isn't in the provided context, 
    say so clearly. Always cite relevant document sources when available."""


class DocumentProcessor:
    """Handle document processing and text extraction with BMasterAI logging"""
    
    def __init__(self, agent_id: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.agent_id = agent_id
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.logger = get_logger()
        self.monitor = get_monitor()
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                self.logger.log_event(
                    self.agent_id,
                    EventType.TASK_COMPLETE,
                    f"PDF text extraction completed",
                    metadata={"file_path": file_path, "text_length": len(text)}
                )
                return text.strip()
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error extracting text from PDF: {e}",
                metadata={"file_path": file_path, "error": str(e)}
            )
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"DOCX text extraction completed",
                metadata={"file_path": file_path, "text_length": len(text)}
            )
            return text.strip()
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error extracting text from DOCX: {e}",
                metadata={"file_path": file_path, "error": str(e)}
            )
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read().strip()
                
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"TXT text extraction completed",
                metadata={"file_path": file_path, "text_length": len(text)}
            )
            return text
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error extracting text from TXT: {e}",
                metadata={"file_path": file_path, "error": str(e)}
            )
            return ""
    
    def extract_text(self, file_path: str, filename: str) -> str:
        """Extract text based on file extension"""
        ext = filename.lower().split('.')[-1]
        
        self.logger.log_event(
            self.agent_id,
            EventType.TASK_START,
            f"Starting text extraction from {ext} file",
            metadata={"filename": filename, "extension": ext}
        )
        
        if ext == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext == 'docx':
            return self.extract_text_from_docx(file_path)
        elif ext == 'txt':
            return self.extract_text_from_txt(file_path)
        else:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Unsupported file type: {ext}",
                metadata={"filename": filename}
            )
            return ""
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        start_time = datetime.now()
        chunks = self.text_splitter.split_text(text)
        
        chunked_docs = []
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Skip empty chunks
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_id': i,
                    'chunk_text': chunk,
                    'chunk_hash': hashlib.md5(chunk.encode()).hexdigest()
                })
                chunked_docs.append(chunk_metadata)
        
        # Track performance
        duration = (datetime.now() - start_time).total_seconds()
        self.monitor.track_task_duration(self.agent_id, "text_chunking", duration * 1000)
        
        self.logger.log_event(
            self.agent_id,
            EventType.TASK_COMPLETE,
            f"Text chunking completed",
            metadata={
                "chunks_created": len(chunked_docs),
                "processing_time": duration
            }
        )
        
        return chunked_docs


class VectorStore:
    """Qdrant vector database interface with BMasterAI monitoring"""
    
    def __init__(self, agent_id: str, config: BMasterAIRAGConfig):
        self.agent_id = agent_id
        self.config = config
        self.client = QdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key
        )
        self.embedding_model = SentenceTransformer(config.embedding_model)
        self.collection_name = config.collection_name
        self.logger = get_logger()
        self.monitor = get_monitor()
        
        # Initialize collection
        self._init_collection()
    
    def _init_collection(self):
        """Initialize Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(
                col.name == self.collection_name 
                for col in collections.collections
            )
            
            if not collection_exists:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=Distance.COSINE
                    )
                )
                self.logger.log_event(
                    self.agent_id,
                    EventType.AGENT_START,
                    f"Created collection: {self.collection_name}"
                )
            else:
                self.logger.log_event(
                    self.agent_id,
                    EventType.AGENT_START,
                    f"Collection {self.collection_name} already exists"
                )
                
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error initializing collection: {e}",
                metadata={"error": str(e)}
            )
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to vector store"""
        start_time = datetime.now()
        try:
            points = []
            for doc in documents:
                # Generate embedding
                embedding = self.embedding_model.encode(doc['chunk_text'])
                
                # Create point
                point = PointStruct(
                    id=doc['chunk_hash'],
                    vector=embedding.tolist(),
                    payload={
                        'filename': doc['filename'],
                        'file_hash': doc['file_hash'],
                        'chunk_id': doc['chunk_id'],
                        'chunk_text': doc['chunk_text'],
                        'upload_time': doc['upload_time'],
                        'file_size': doc['file_size']
                    }
                )
                points.append(point)
            
            # Insert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            # Track performance
            duration = (datetime.now() - start_time).total_seconds()
            self.monitor.track_task_duration(
                self.agent_id,
                "vector_insertion",
                duration * 1000
            )
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Added {len(points)} document chunks to vector store",
                metadata={
                    "chunks_added": len(points),
                    "processing_time": duration
                }
            )
            return True
            
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error adding documents to vector store: {e}",
                metadata={"error": str(e)}
            )
            self.monitor.track_error(self.agent_id, "vector_insertion_error")
            return False
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        start_time = datetime.now()
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k,
                with_payload=True
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'score': result.score,
                    'text': result.payload['chunk_text'],
                    'filename': result.payload['filename'],
                    'chunk_id': result.payload['chunk_id'],
                    'upload_time': result.payload['upload_time']
                })
            
            # Track performance
            duration = (datetime.now() - start_time).total_seconds()
            self.monitor.track_task_duration(
                self.agent_id,
                "vector_search",
                duration * 1000
            )
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Document search completed",
                metadata={
                    "query_length": len(query),
                    "results_found": len(formatted_results),
                    "search_time": duration
                }
            )
            
            return formatted_results
            
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error searching documents: {e}",
                metadata={"error": str(e)}
            )
            self.monitor.track_error(self.agent_id, "vector_search_error")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'status': info.status,
                'points_count': info.points_count,
                'vectors_count': info.vectors_count,
                'segments_count': info.segments_count
            }
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error getting collection info: {e}",
                metadata={"error": str(e)}
            )
            return {'error': str(e)}
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the collection"""
        try:
            # Use scroll to get all points
            result = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,  # Adjust based on your needs
                with_payload=True
            )
            
            documents = {}
            for point in result[0]:
                filename = point.payload['filename']
                if filename not in documents:
                    documents[filename] = {
                        'filename': filename,
                        'file_hash': point.payload['file_hash'],
                        'upload_time': point.payload['upload_time'],
                        'file_size': point.payload['file_size'],
                        'chunk_count': 0
                    }
                documents[filename]['chunk_count'] += 1
            
            return list(documents.values())
            
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error listing documents: {e}",
                metadata={"error": str(e)}
            )
            return []


class AnthropicChat:
    """Anthropic API interface with BMasterAI monitoring"""
    
    def __init__(self, agent_id: str, config: BMasterAIRAGConfig):
        self.agent_id = agent_id
        self.config = config
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.logger = get_logger()
        self.monitor = get_monitor()
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for API request"""
        return {
            "Content-Type": "application/json",
            "x-api-key": self.config.anthropic_api_key,
            "anthropic-version": "2023-06-01"
        }
    
    def generate_response(self, query: str, context: str) -> str:
        """Generate response using context and query"""
        start_time = datetime.now()
        try:
            # Prepare context-aware prompt
            prompt = f"""Context from documents:
{context}

User question: {query}

Please answer the question based on the provided context. If the answer isn't in the context, say so clearly."""
            
            # Prepare request payload
            payload = {
                "model": self.config.model_name,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "system": self.config.system_prompt,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            self.logger.log_event(
                self.agent_id,
                EventType.LLM_REQUEST,
                f"Sending request to Anthropic API",
                metadata={
                    "model": self.config.model_name,
                    "query_length": len(query),
                    "context_length": len(context)
                }
            )
            
            # Make API request
            response = requests.post(
                self.base_url,
                headers=self._prepare_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result["content"][0]["text"]
                
                # Track performance and usage
                duration = (datetime.now() - start_time).total_seconds()
                self.monitor.track_task_duration(
                    self.agent_id,
                    "llm_response_generation",
                    duration * 1000
                )
                
                # Track LLM usage
                usage = result.get("usage", {})
                if usage:
                    self.monitor.track_llm_usage(
                        self.agent_id,
                        self.config.model_name,
                        usage.get("input_tokens", 0),
                        usage.get("output_tokens", 0)
                    )
                
                self.logger.log_event(
                    self.agent_id,
                    EventType.LLM_RESPONSE,
                    f"Received response from Anthropic API",
                    metadata={
                        "response_length": len(answer),
                        "generation_time": duration,
                        "usage": usage
                    }
                )
                
                return answer
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                self.logger.log_event(
                    self.agent_id,
                    EventType.LLM_ERROR,
                    error_msg,
                    metadata={"status_code": response.status_code}
                )
                self.monitor.track_error(self.agent_id, "llm_api_error")
                return f"Error: {error_msg}"
                
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.LLM_ERROR,
                f"Error generating response: {e}",
                metadata={"error": str(e)}
            )
            self.monitor.track_error(self.agent_id, "llm_generation_error")
            return f"Error generating response: {str(e)}"


class BMasterAIRAGSystem:
    """Main RAG system combining all components with BMasterAI framework"""
    
    def __init__(self, config: BMasterAIRAGConfig):
        self.config = config
        self.agent_id = "rag-system-001"
        
        # Initialize BMasterAI components
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.integration_manager = get_integration_manager()
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Register agent
        self.monitor.track_agent_start(self.agent_id)
        
        # Initialize RAG components
        self.doc_processor = DocumentProcessor(self.agent_id, config.chunk_size, config.chunk_overlap)
        self.vector_store = VectorStore(self.agent_id, config)
        self.chat = AnthropicChat(self.agent_id, config)
        
        # Session tracking
        self.session_stats = {
            'documents_uploaded': 0,
            'queries_processed': 0,
            'start_time': datetime.now().isoformat()
        }
        
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            f"BMasterAI RAG System initialized",
            metadata={
                "agent_id": self.agent_id,
                "model": config.model_name,
                "embedding_model": config.embedding_model
            }
        )
    
    def upload_document(self, file_path: str, filename: str) -> Tuple[bool, str]:
        """Upload and process a document"""
        start_time = datetime.now()
        try:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_START,
                f"Starting document upload: {filename}",
                metadata={"filename": filename}
            )
            
            # Extract text
            text = self.doc_processor.extract_text(file_path, filename)
            if not text:
                return False, "Could not extract text from document"
            
            # Prepare metadata
            file_hash = hashlib.md5(text.encode()).hexdigest()
            metadata = {
                'filename': filename,
                'file_hash': file_hash,
                'upload_time': datetime.now().isoformat(),
                'file_size': len(text)
            }
            
            # Chunk document
            chunks = self.doc_processor.chunk_text(text, metadata)
            if not chunks:
                return False, "Could not chunk document"
            
            # Add to vector store
            success = self.vector_store.add_documents(chunks)
            
            if success:
                self.session_stats['documents_uploaded'] += 1
                duration = (datetime.now() - start_time).total_seconds()
                
                self.monitor.track_task_duration(
                    self.agent_id,
                    "document_upload",
                    duration * 1000
                )
                
                self.logger.log_event(
                    self.agent_id,
                    EventType.TASK_COMPLETE,
                    f"Document upload completed: {filename}",
                    metadata={
                        "filename": filename,
                        "chunks": len(chunks),
                        "processing_time": duration
                    }
                )
                
                # Send notification if configured
                self.integration_manager.send_notification(
                    f"✅ Document uploaded successfully: {filename}\n"
                    f"📊 Chunks created: {len(chunks)}"
                )
                
                return True, f"Successfully uploaded {filename} with {len(chunks)} chunks"
            else:
                return False, "Failed to add document to vector store"
                
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error uploading document: {e}",
                metadata={"filename": filename, "error": str(e)}
            )
            self.monitor.track_error(self.agent_id, "document_upload_error")
            return False, f"Error uploading document: {str(e)}"
    
    def search_and_answer(self, query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Search documents and generate answer"""
        start_time = datetime.now()
        try:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_START,
                f"Processing query: {query[:100]}...",
                metadata={"query_length": len(query)}
            )
            
            # Search for relevant documents
            search_results = self.vector_store.search_documents(
                query, 
                top_k=self.config.top_k
            )
            
            if not search_results:
                return "No relevant documents found for your query.", []
            
            # Prepare context
            context = "\n\n".join([
                f"Document: {result['filename']}\n{result['text']}"
                for result in search_results
                if result['score'] >= self.config.similarity_threshold
            ])
            
            if not context:
                return "No sufficiently relevant documents found for your query.", search_results
            
            # Generate response
            response = self.chat.generate_response(query, context)
            
            self.session_stats['queries_processed'] += 1
            duration = (datetime.now() - start_time).total_seconds()
            
            self.monitor.track_task_duration(
                self.agent_id,
                "query_processing",
                duration * 1000
            )
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Query processing completed",
                metadata={
                    "query_length": len(query),
                    "response_length": len(response),
                    "processing_time": duration,
                    "documents_used": len(search_results)
                }
            )
            
            return response, search_results
            
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error in search and answer: {e}",
                metadata={"error": str(e)}
            )
            self.monitor.track_error(self.agent_id, "query_processing_error")
            return f"Error processing query: {str(e)}", []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information"""
        try:
            collection_info = self.vector_store.get_collection_info()
            agent_dashboard = self.monitor.get_agent_dashboard(self.agent_id)
            
            return {
                'session_stats': self.session_stats,
                'collection_info': collection_info,
                'agent_performance': agent_dashboard,
                'system_health': self.monitor.get_system_health(),
                'config': {
                    'model_name': self.config.model_name,
                    'embedding_model': self.config.embedding_model,
                    'collection_name': self.config.collection_name,
                    'chunk_size': self.config.chunk_size,
                    'top_k': self.config.top_k
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def shutdown(self):
        """Gracefully shutdown the RAG system"""
        self.monitor.track_agent_stop(self.agent_id)
        self.monitor.stop_monitoring()
        
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_STOP,
            f"BMasterAI RAG System shutdown",
            metadata={
                "total_documents": self.session_stats['documents_uploaded'],
                "total_queries": self.session_stats['queries_processed']
            }
        )


class BMasterAIRAGApp:
    """Gradio application for RAG system with BMasterAI framework"""
    
    def __init__(self):
        # Configure BMasterAI logging
        configure_logging(
            log_level=LogLevel.INFO,
            enable_json=os.getenv("ENABLE_JSON_LOGS", "false").lower() == "true",
            enable_file=os.getenv("ENABLE_FILE_LOGS", "true").lower() == "true"
        )
        
        # Initialize configuration
        self.config = BMasterAIRAGConfig(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            model_name=os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            collection_name=os.getenv("COLLECTION_NAME", "bmasterai_documents"),
            max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            top_k=int(os.getenv("TOP_K", "5")),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
        )
        
        # Setup integrations if configured
        integration_manager = get_integration_manager()
        
        # Add Slack integration if configured
        if os.getenv("SLACK_WEBHOOK_URL"):
            slack = SlackConnector(webhook_url=os.getenv("SLACK_WEBHOOK_URL"))
            integration_manager.add_connector("slack", slack)
        
        # Add email integration if configured
        if os.getenv("SMTP_SERVER") and os.getenv("SMTP_USERNAME"):
            email = EmailConnector(
                smtp_server=os.getenv("SMTP_SERVER"),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                username=os.getenv("SMTP_USERNAME"),
                password=os.getenv("SMTP_PASSWORD")
            )
            integration_manager.add_connector("email", email)
        
        # Initialize RAG system
        try:
            self.rag_system = BMasterAIRAGSystem(self.config)
            self.system_status = "✅ System initialized successfully"
        except Exception as e:
            self.system_status = f"❌ System initialization failed: {str(e)}"
            self.rag_system = None
    
    def upload_file(self, file) -> str:
        """Handle file upload"""
        if not self.rag_system:
            return "❌ System not initialized"
        
        if file is None:
            return "❌ No file selected"
        
        try:
            # Get file info
            filename = os.path.basename(file.name)
            file_path = file.name
            
            # Check file type
            allowed_extensions = ['.pdf', '.docx', '.txt']
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                return f"❌ Unsupported file type: {file_ext}. Supported: {', '.join(allowed_extensions)}"
            
            # Upload document
            success, message = self.rag_system.upload_document(file_path, filename)
            
            if success:
                return f"✅ {message}"
            else:
                return f"❌ {message}"
                
        except Exception as e:
            return f"❌ Error uploading file: {str(e)}"
    
    def upload_multiple_files(self, files) -> str:
        """Handle multiple file uploads"""
        if not self.rag_system:
            return "❌ System not initialized"
        
        if not files:
            return "❌ No files selected"
        
        results = []
        success_count = 0
        
        for file in files:
            try:
                filename = os.path.basename(file.name)
                file_path = file.name
                
                # Check file type
                allowed_extensions = ['.pdf', '.docx', '.txt']
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext not in allowed_extensions:
                    results.append(f"❌ {filename}: Unsupported file type")
                    continue
                
                # Upload document
                success, message = self.rag_system.upload_document(file_path, filename)
                
                if success:
                    results.append(f"✅ {filename}: {message}")
                    success_count += 1
                else:
                    results.append(f"❌ {filename}: {message}")
                    
            except Exception as e:
                results.append(f"❌ {filename}: Error - {str(e)}")
        
        summary = f"\n📊 Summary: {success_count}/{len(files)} files uploaded successfully\n\n"
        return summary + "\n".join(results)
    
    def chat_interface(self, message: str, history: List[List[str]]) -> Tuple[str, List[List[str]]]:
        """Chat interface for questions"""
        if not self.rag_system:
            history.append([message, "❌ System not initialized"])
            return "", history
        
        if not message.strip():
            return "", history
        
        try:
            # Get answer from RAG system
            answer, sources = self.rag_system.search_and_answer(message)
            
            # Format response with sources
            if sources:
                source_info = f"\n\n📚 **Sources ({len(sources)} documents):**\n"
                for i, source in enumerate(sources[:3], 1):  # Show top 3 sources
                    source_info += f"{i}. **{source['filename']}** (Score: {source['score']:.3f})\n"
                    source_info += f"   {source['text'][:150]}...\n\n"
                
                full_response = answer + source_info
            else:
                full_response = answer
            
            history.append([message, full_response])
            return "", history
            
        except Exception as e:
            error_response = f"❌ Error processing question: {str(e)}"
            history.append([message, error_response])
            return "", history
    
    def get_system_status(self) -> str:
        """Get formatted system status"""
        if not self.rag_system:
            return "❌ System not initialized"
        
        try:
            status = self.rag_system.get_system_status()
            
            status_text = f"""
## 🖥️ System Status: {self.system_status}

### 📊 Session Statistics:
- **Documents Uploaded**: {status['session_stats']['documents_uploaded']}
- **Queries Processed**: {status['session_stats']['queries_processed']}
- **Session Started**: {status['session_stats']['start_time']}

### 📚 Collection Information:
- **Status**: {status['collection_info'].get('status', 'Unknown')}
- **Documents**: {status['collection_info'].get('points_count', 0)} chunks
- **Vectors**: {status['collection_info'].get('vectors_count', 0)}

### ⚙️ Configuration:
- **LLM Model**: {status['config']['model_name']}
- **Embedding Model**: {status['config']['embedding_model']}
- **Collection**: {status['config']['collection_name']}
- **Chunk Size**: {status['config']['chunk_size']}
- **Top-K Results**: {status['config']['top_k']}

### 🔗 System Health:
- **Active Agents**: {status['system_health'].get('active_agents', 0)}
- **Total Agents**: {status['system_health'].get('total_agents', 0)}
"""
            
            return status_text
            
        except Exception as e:
            return f"❌ Error getting system status: {str(e)}"
    
    def list_documents(self) -> str:
        """List all uploaded documents"""
        if not self.rag_system:
            return "❌ System not initialized"
        
        try:
            documents = self.rag_system.vector_store.list_documents()
            
            if not documents:
                return "📚 No documents uploaded yet"
            
            doc_list = "📚 **Uploaded Documents:**\n\n"
            for i, doc in enumerate(documents, 1):
                doc_list += f"{i}. **{doc['filename']}**\n"
                doc_list += f"   - Chunks: {doc['chunk_count']}\n"
                doc_list += f"   - Size: {doc['file_size']} characters\n"
                doc_list += f"   - Uploaded: {doc['upload_time']}\n\n"
            
            return doc_list
            
        except Exception as e:
            return f"❌ Error listing documents: {str(e)}"
    
    def search_documents(self, query: str) -> str:
        """Search documents without generating answer"""
        if not self.rag_system:
            return "❌ System not initialized"
        
        if not query.strip():
            return "❌ Please enter a search query"
        
        try:
            results = self.rag_system.vector_store.search_documents(query, top_k=10)
            
            if not results:
                return "🔍 No relevant documents found"
            
            search_results = f"🔍 **Search Results for:** {query}\n\n"
            for i, result in enumerate(results, 1):
                search_results += f"{i}. **{result['filename']}** (Score: {result['score']:.3f})\n"
                search_results += f"   {result['text'][:200]}...\n\n"
            
            return search_results
            
        except Exception as e:
            return f"❌ Error searching documents: {str(e)}"
    
    def get_performance_metrics(self) -> str:
        """Get performance metrics"""
        if not self.rag_system:
            return "❌ System not initialized"
        
        try:
            dashboard = self.rag_system.monitor.get_agent_dashboard(self.rag_system.agent_id)
            
            metrics_text = "📈 **Performance Metrics:**\n\n"
            
            if dashboard.get('performance'):
                for task_name, metrics in dashboard['performance'].items():
                    metrics_text += f"**{task_name.replace('_', ' ').title()}:**\n"
                    metrics_text += f"- Average Duration: {metrics.get('avg_duration_ms', 0):.2f}ms\n"
                    metrics_text += f"- Min Duration: {metrics.get('min_duration_ms', 0):.2f}ms\n"
                    metrics_text += f"- Max Duration: {metrics.get('max_duration_ms', 0):.2f}ms\n"
                    metrics_text += f"- Total Calls: {metrics.get('total_calls', 0)}\n\n"
            
            metrics_text += f"**System Metrics:**\n"
            metrics_text += f"- Total Errors: {dashboard.get('metrics', {}).get('total_errors', 0)}\n"
            metrics_text += f"- Agent Status: {dashboard.get('status', 'Unknown')}\n"
            
            return metrics_text
            
        except Exception as e:
            return f"❌ Error getting performance metrics: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Create the complete Gradio interface"""
        
        # Custom CSS for better styling
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
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1);
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
        .upload-box {
            background-color: #e8f5e8;
            padding: 20px;
            border-radius: 10px;
            border: 2px dashed #28a745;
            margin: 10px 0;
        }
        """
        
        with gr.Blocks(css=custom_css, title="BMasterAI RAG System", theme=gr.themes.Soft()) as demo:
            
            # Header
            gr.HTML("""
            <div class="header-text">
                🧠 BMasterAI RAG System
            </div>
            <div style="text-align: center; margin-bottom: 30px;">
                <p style="font-size: 1.2em; color: #666;">
                    Advanced Document Q&A with Qdrant Vector Database & Anthropic Claude
                </p>
            </div>
            """)
            
            with gr.Tabs():
                
                # Chat Tab
                with gr.TabItem("💬 Chat with Documents", elem_id="chat-tab"):
                    with gr.Row():
                        with gr.Column(scale=3):
                            chatbot = gr.Chatbot(
                                label="Document Q&A Assistant",
                                height=500,
                                show_label=True,
                                elem_id="chatbot",
                                bubble_full_width=False
                            )
                            
                            with gr.Row():
                                msg = gr.Textbox(
                                    label="Ask a question about your documents",
                                    placeholder="What would you like to know about your uploaded documents?",
                                    lines=2,
                                    scale=4
                                )
                                submit_btn = gr.Button("Ask", variant="primary", scale=1)
                            
                            with gr.Row():
                                clear_btn = gr.Button("Clear Chat", variant="secondary")
                                example_btn = gr.Button("Example Questions", variant="secondary")
                        
                        with gr.Column(scale=1):
                            gr.HTML("<h3>💡 Quick Actions</h3>")
                            
                            # Example questions
                            with gr.Accordion("Example Questions", open=True):
                                example_questions = [
                                    "What are the main topics in the documents?",
                                    "Summarize the key findings",
                                    "What are the recommendations?",
                                    "Are there any important dates or deadlines?"
                                ]
                                
                                for question in example_questions:
                                    example_q_btn = gr.Button(f"❓ {question}", size="sm")
                                    example_q_btn.click(
                                        lambda q=question: (q, []),
                                        outputs=[msg, chatbot]
                                    )
                            
                            # Quick search
                            with gr.Accordion("Quick Search", open=False):
                                search_input = gr.Textbox(
                                    label="Search Documents",
                                    placeholder="Enter search terms...",
                                    lines=1
                                )
                                search_btn = gr.Button("Search", size="sm")
                                search_results = gr.Markdown("Search results will appear here...")
                
                # Document Upload Tab
                with gr.TabItem("📁 Upload Documents", elem_id="upload-tab"):
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("""
                            <div class="upload-box">
                                <h3>📤 Upload Your Documents</h3>
                                <p>Supported formats: PDF, DOCX, TXT</p>
                                <p>Upload individual files or multiple files at once</p>
                            </div>
                            """)
                            
                            # Single file upload
                            with gr.Group():
                                gr.HTML("<h4>Single File Upload</h4>")
                                single_file = gr.File(
                                    label="Choose a document",
                                    file_types=[".pdf", ".docx", ".txt"],
                                    type="filepath"
                                )
                                single_upload_btn = gr.Button("Upload File", variant="primary")
                                single_result = gr.Textbox(label="Upload Result", interactive=False, lines=3)
                            
                            # Multiple file upload
                            with gr.Group():
                                gr.HTML("<h4>Multiple File Upload</h4>")
                                multiple_files = gr.File(
                                    label="Choose multiple documents",
                                    file_count="multiple",
                                    file_types=[".pdf", ".docx", ".txt"],
                                    type="filepath"
                                )
                                multiple_upload_btn = gr.Button("Upload All Files", variant="primary")
                                multiple_result = gr.Textbox(label="Upload Results", interactive=False, lines=8)
                        
                        with gr.Column():
                            gr.HTML("<h3>📚 Document Library</h3>")
                            
                            document_list = gr.Markdown("Loading document list...")
                            refresh_docs_btn = gr.Button("Refresh Document List")
                            
                            gr.HTML("<h3>📊 Upload Statistics</h3>")
                            upload_stats = gr.Markdown("Loading statistics...")
                            refresh_stats_btn = gr.Button("Refresh Statistics")
                
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
                            gr.HTML("<h3>🔧 System Configuration</h3>")
                            
                            # Display current configuration
                            config_display = gr.JSON(
                                value={
                                    "model_name": self.config.model_name,
                                    "embedding_model": self.config.embedding_model,
                                    "collection_name": self.config.collection_name,
                                    "chunk_size": self.config.chunk_size,
                                    "chunk_overlap": self.config.chunk_overlap,
                                    "top_k": self.config.top_k,
                                    "similarity_threshold": self.config.similarity_threshold,
                                    "max_tokens": self.config.max_tokens,
                                    "temperature": self.config.temperature
                                },
                                label="Current Configuration"
                            )
                        
                        with gr.Column():
                            gr.HTML("<h3>🔗 Integration Status</h3>")
                            
                            integration_status = gr.Markdown("""
                            **Available Integrations:**
                            - Slack: Configure with SLACK_WEBHOOK_URL
                            - Email: Configure with SMTP settings
                            - Monitoring: Always enabled with BMasterAI
                            
                            **Environment Variables:**
                            - ANTHROPIC_API_KEY: Required
                            - QDRANT_URL: Vector database URL
                            - QDRANT_API_KEY: Optional for cloud
                            """)
                
                # Help Tab
                with gr.TabItem("❓ Help & Documentation", elem_id="help-tab"):
                    gr.HTML("""
                    <div style="padding: 20px;">
                        <h2>🚀 Getting Started</h2>
                        <ol>
                            <li><strong>Upload Documents:</strong> Go to the "Upload Documents" tab and upload your PDF, DOCX, or TXT files</li>
                            <li><strong>Ask Questions:</strong> Use the "Chat with Documents" tab to ask questions about your uploaded content</li>
                            <li><strong>Monitor System:</strong> Check the "System Status" tab for performance metrics and health information</li>
                        </ol>
                        
                        <h2>📚 Supported File Types</h2>
                        <ul>
                            <li><strong>PDF:</strong> Portable Document Format files</li>
                            <li><strong>DOCX:</strong> Microsoft Word documents</li>
                            <li><strong>TXT:</strong> Plain text files</li>
                        </ul>
                        
                        <h2>🔧 Configuration</h2>
                        <p>The system can be configured using environment variables:</p>
                        <ul>
                            <li><code>ANTHROPIC_API_KEY</code>: Your Anthropic API key (required)</li>
                            <li><code>QDRANT_URL</code>: Qdrant database URL (default: http://localhost:6333)</li>
                            <li><code>QDRANT_API_KEY</code>: Qdrant API key for cloud instances</li>
                            <li><code>MODEL_NAME</code>: Anthropic model to use</li>
                            <li><code>CHUNK_SIZE</code>: Document chunk size for processing</li>
                            <li><code>TOP_K</code>: Number of relevant documents to retrieve</li>
                        </ul>
                        
                        <h2>🚨 Troubleshooting</h2>
                        <ul>
                            <li><strong>Upload fails:</strong> Check file format and size</li>
                            <li><strong>No answers:</strong> Ensure documents are uploaded and relevant to your question</li>
                            <li><strong>System errors:</strong> Check the System Status tab for details</li>
                        </ul>
                        
                        <h2>📞 Support</h2>
                        <p>For support and documentation, visit:</p>
                        <ul>
                            <li><a href="https://github.com/travis-burmaster/bmasterai">BMasterAI GitHub Repository</a></li>
                            <li><a href="mailto:travis@burmaster.com">Email Support</a></li>
                        </ul>
                    </div>
                    """)
            
            # Event handlers
            def submit_message(message, history):
                if message.strip():
                    return self.chat_interface(message, history)
                return message, history
            
            # Wire up the interface
            submit_btn.click(submit_message, inputs=[msg, chatbot], outputs=[msg, chatbot])
            msg.submit(submit_message, inputs=[msg, chatbot], outputs=[msg, chatbot])
            
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])
            
            # File upload handlers
            single_upload_btn.click(
                self.upload_file,
                inputs=[single_file],
                outputs=[single_result]
            )
            
            multiple_upload_btn.click(
                self.upload_multiple_files,
                inputs=[multiple_files],
                outputs=[multiple_result]
            )
            
            # Document management
            refresh_docs_btn.click(
                self.list_documents,
                outputs=[document_list]
            )
            
            # Search functionality
            search_btn.click(
                self.search_documents,
                inputs=[search_input],
                outputs=[search_results]
            )
            
            # Status and metrics
            refresh_status_btn.click(
                self.get_system_status,
                outputs=[system_status_display]
            )
            
            refresh_metrics_btn.click(
                self.get_performance_metrics,
                outputs=[performance_metrics]
            )
            
            refresh_stats_btn.click(
                self.get_system_status,
                outputs=[upload_stats]
            )
            
            # Auto-refresh on load
            demo.load(self.get_system_status, outputs=[system_status_display])
            demo.load(self.get_performance_metrics, outputs=[performance_metrics])
            demo.load(self.list_documents, outputs=[document_list])
            demo.load(self.get_system_status, outputs=[upload_stats])
        
        return demo


def main():
    """
    Main function to launch the BMasterAI RAG Gradio application
    """
    
    # Environment setup instructions
    required_vars = ["ANTHROPIC_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("\n" + "="*60)
        print("🔑 SETUP REQUIRED:")
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"  {var}='your-{var.lower().replace('_', '-')}'")
        
        print("\nSet them with:")
        for var in missing_vars:
            print(f"export {var}='your-{var.lower().replace('_', '-')}'")
        
        print("\nOr create a .env file with:")
        for var in missing_vars:
            print(f"{var}=your-{var.lower().replace('_', '-')}")
        
        print("\n🌐 Get your keys from:")
        print("  Anthropic: https://console.anthropic.com/")
        print("  Qdrant Cloud: https://cloud.qdrant.io/ (optional)")
        print("="*60 + "\n")
    
    try:
        # Create and launch the application
        print("🚀 Initializing BMasterAI RAG Gradio application...")
        app = BMasterAIRAGApp()
        demo = app.create_interface()
        
        # Launch configuration
        server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
        server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
        share = os.getenv("GRADIO_SHARE", "false").lower() == "true"
        
        print(f"🌐 Launching Gradio interface on {server_name}:{server_port}")
        print(f"📊 System Status: {app.system_status}")
        
        if not missing_vars:
            print("✅ All required environment variables configured!")
        else:
            print("⚠️  Some environment variables missing - limited functionality")
        
        print("\n🎯 Features available:")
        print("  📁 Document Upload (PDF, DOCX, TXT)")
        print("  💬 Interactive Q&A Chat")
        print("  🔍 Document Search")
        print("  📊 System Monitoring")
        print("  ⚙️  Configuration Management")
        
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
        print("2. Verify Anthropic API key")
        print("3. Ensure Qdrant is running (if using local instance)")
        print("4. Check network connectivity")
    
    finally:
        # Cleanup
        try:
            if 'app' in locals() and app.rag_system:
                app.rag_system.shutdown()
        except:
            pass
        print("\n✅ BMasterAI RAG Gradio application stopped!")


if __name__ == "__main__":
    main()AGSystem(self.config)
            self.system_status = "✅ RAG System Initialized with BMasterAI Framework"
        except Exception as e:
            get_logger().log_event(
                "app",
                EventType.TASK_ERROR,
                f"Failed to initialize RAG system: {e}",
                metadata={"error": str(e)}
            )
            self.system_status = f"❌ System Error: {e}"
            self.rag_system = None
    