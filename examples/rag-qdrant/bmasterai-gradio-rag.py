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
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# Optional caching dependency
try:
    import diskcache as dc
    DISKCACHE_AVAILABLE = True
except ImportError:
    print("⚠️  diskcache not available - caching will be disabled")
    DISKCACHE_AVAILABLE = False
    
    # Create a simple fallback cache
    class SimpleCache:
        def __init__(self, directory=None):
            self._cache = {}
        
        def __setitem__(self, key, value):
            self._cache[key] = value
        
        def __getitem__(self, key):
            return self._cache[key]
        
        def __contains__(self, key):
            return key in self._cache
    
    dc = type('dc', (), {'Cache': SimpleCache})()

# External dependencies
try:
    import gradio as gr
    import requests
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    import PyPDF2
    import docx
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Install with: pip install gradio requests qdrant-client sentence-transformers PyPDF2 python-docx langchain python-dotenv")
    exit(1)

# Import BMasterAI framework components (with fallbacks)
BMASTERAI_AVAILABLE = True
try:
    from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
    from bmasterai.monitoring import get_monitor
    from bmasterai.integrations import get_integration_manager, SlackConnector, EmailConnector
    BMASTERAI_AVAILABLE = True
    print("✅ BMasterAI framework loaded successfully")
    
    # Ensure EventType has all required attributes (patch if missing)
    if not hasattr(EventType, 'LLM_ERROR'):
        EventType.LLM_ERROR = "llm_error"
    if not hasattr(EventType, 'AGENT_STOP'):
        EventType.AGENT_STOP = "agent_stop"
except ImportError as e:
    print(f"⚠️  BMasterAI framework not found: {e}")
    print("Running in standalone mode with basic logging...")
    
    # Create fallback classes and functions
    import logging
    
    class EventType:
        TASK_START = "task_start"
        TASK_COMPLETE = "task_complete"
        TASK_ERROR = "task_error"
        AGENT_START = "agent_start"
        AGENT_STOP = "agent_stop"
        LLM_REQUEST = "llm_request"
        LLM_RESPONSE = "llm_response"
        LLM_ERROR = "llm_error"
    
    class LogLevel:
        DEBUG = logging.DEBUG
        INFO = logging.INFO
        WARNING = logging.WARNING
        ERROR = logging.ERROR
    
    class FallbackLogger:
        def __init__(self):
            self.logger = logging.getLogger("bmasterai_rag")
        
        def log_event(self, agent_id, event_type, message, metadata=None):
            self.logger.info(f"[{agent_id}] {event_type}: {message}")
            if metadata:
                self.logger.debug(f"Metadata: {metadata}")
    
    class FallbackMonitor:
        def start_monitoring(self):
            pass
        
        def track_agent_start(self, agent_id):
            logging.info(f"Agent started: {agent_id}")
        
        def track_task_duration(self, agent_id, task_name, duration_ms):
            logging.debug(f"Task {task_name} took {duration_ms}ms")
        
        def track_error(self, agent_id, error_type):
            logging.warning(f"Error tracked: {error_type}")
        
        def track_llm_usage(self, agent_id, model, input_tokens, output_tokens):
            logging.info(f"LLM usage: {input_tokens} in, {output_tokens} out")
    
    class FallbackIntegrationManager:
        def __init__(self):
            pass
    
    def configure_logging():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def get_logger():
        return FallbackLogger()
    
    def get_monitor():
        return FallbackMonitor()
    
    def get_integration_manager():
        return FallbackIntegrationManager()

# Load environment variables
load_dotenv()

def get_env_var(key: str, default: Any = None, var_type: type = str) -> Any:
    """Get environment variable with type conversion and validation"""
    value = os.getenv(key, default)
    if value is None:
        return default
    
    # Clean the value by removing inline comments and whitespace
    if isinstance(value, str):
        value = value.split('#')[0].strip()
        if not value:  # If empty after cleaning, return default
            return default
    
    try:
        if var_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif var_type == int:
            return int(value)
        elif var_type == float:
            return float(value)
        else:
            return str(value)
    except (ValueError, TypeError):
        print(f"Warning: Invalid value for {key}: {value}. Using default: {default}")
        return default


@dataclass
class BMasterAIRAGConfig:
    """Configuration for BMasterAI RAG system loaded from environment variables"""
    
    def __init__(self):
        # Required configuration
        self.anthropic_api_key = get_env_var("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key or self.anthropic_api_key == "your-anthropic-api-key-here":
            raise ValueError("ANTHROPIC_API_KEY must be set in .env file")
        
        # Vector Database Configuration
        self.qdrant_url = get_env_var("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = get_env_var("QDRANT_API_KEY") or None
        
        # Model Configuration
        self.model_name = get_env_var("MODEL_NAME", "claude-3-5-sonnet-20241022")
        self.embedding_model = get_env_var("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.collection_name = get_env_var("COLLECTION_NAME", "bmasterai_documents")
        
        # API Configuration
        self.max_tokens = get_env_var("MAX_TOKENS", 4096, int)
        self.temperature = get_env_var("TEMPERATURE", 0.7, float)
        
        # Document Processing Configuration
        self.chunk_size = get_env_var("CHUNK_SIZE", 1000, int)
        self.chunk_overlap = get_env_var("CHUNK_OVERLAP", 200, int)
        self.top_k = get_env_var("TOP_K", 5, int)
        self.similarity_threshold = get_env_var("SIMILARITY_THRESHOLD", 0.7, float)
        
        # Performance Configuration
        self.max_file_size = get_env_var("MAX_FILE_SIZE", 50 * 1024 * 1024, int)
        self.max_concurrent_uploads = get_env_var("MAX_CONCURRENT_UPLOADS", 5, int)
        self.max_connections = get_env_var("MAX_CONNECTIONS", 5, int)
        self.connection_timeout = get_env_var("CONNECTION_TIMEOUT", 30, int)
        
        # Cache Configuration
        self.cache_dir = get_env_var("CACHE_DIR", "/tmp/bmasterai_cache")
        self.enable_response_cache = get_env_var("ENABLE_RESPONSE_CACHE", True, bool)
        self.enable_embedding_cache = get_env_var("ENABLE_EMBEDDING_CACHE", True, bool)
        
        # Server Configuration
        self.gradio_server_name = get_env_var("GRADIO_SERVER_NAME", "0.0.0.0")
        self.gradio_server_port = get_env_var("GRADIO_SERVER_PORT", 7860, int)
        self.gradio_share = get_env_var("GRADIO_SHARE", False, bool)
        self.gradio_auth = get_env_var("GRADIO_AUTH") or None
        
        # Logging Configuration
        self.log_level = get_env_var("LOG_LEVEL", "INFO")
        self.enable_json_logs = get_env_var("ENABLE_JSON_LOGS", False, bool)
        self.enable_file_logs = get_env_var("ENABLE_FILE_LOGS", True, bool)
        self.log_file_path = get_env_var("LOG_FILE_PATH", "logs/bmasterai_rag.log")
        
        # Monitoring Configuration
        self.enable_performance_monitoring = get_env_var("ENABLE_PERFORMANCE_MONITORING", True, bool)
        self.enable_usage_tracking = get_env_var("ENABLE_USAGE_TRACKING", True, bool)
        
        # Security Configuration
        self.rate_limit_per_minute = get_env_var("RATE_LIMIT_PER_MINUTE", 60, int)
        self.allowed_file_extensions = get_env_var("ALLOWED_FILE_EXTENSIONS", "pdf,docx,txt").split(",")
        self.max_filename_length = get_env_var("MAX_FILENAME_LENGTH", 255, int)
        
        # Development Configuration
        self.debug_mode = get_env_var("DEBUG_MODE", False, bool)
        self.verbose_logging = get_env_var("VERBOSE_LOGGING", False, bool)
        self.dev_mode = get_env_var("DEV_MODE", False, bool)
        self.auto_reload = get_env_var("AUTO_RELOAD", False, bool)
        
        # System Prompt Configuration
        default_system_prompt = """You are a helpful AI assistant that answers questions based on provided documents. 
Use the context provided to answer questions accurately. If the answer isn't in the provided context, 
say so clearly. Always cite relevant document sources when available."""
        self.system_prompt = get_env_var("SYSTEM_PROMPT", default_system_prompt)
        
        # Optional Integrations
        self.slack_webhook_url = get_env_var("SLACK_WEBHOOK_URL") or None
        self.slack_channel = get_env_var("SLACK_CHANNEL", "#ai-notifications")
        self.smtp_server = get_env_var("SMTP_SERVER") or None
        self.smtp_port = get_env_var("SMTP_PORT", 587, int)
        self.smtp_username = get_env_var("SMTP_USERNAME") or None
        self.smtp_password = get_env_var("SMTP_PASSWORD") or None
        self.smtp_from_email = get_env_var("SMTP_FROM_EMAIL") or None
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create log directory if logging is enabled
        if self.enable_file_logs:
            log_dir = os.path.dirname(self.log_file_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required fields
        if not self.anthropic_api_key:
            issues.append("ANTHROPIC_API_KEY is required")
        
        # Check file size limits
        if self.max_file_size <= 0:
            issues.append("MAX_FILE_SIZE must be positive")
        
        # Check chunk configuration
        if self.chunk_size <= 0:
            issues.append("CHUNK_SIZE must be positive")
        if self.chunk_overlap >= self.chunk_size:
            issues.append("CHUNK_OVERLAP must be less than CHUNK_SIZE")
        
        # Check model parameters
        if self.temperature < 0 or self.temperature > 2:
            issues.append("TEMPERATURE must be between 0 and 2")
        if self.max_tokens <= 0:
            issues.append("MAX_TOKENS must be positive")
        
        # Check server configuration
        if self.gradio_server_port <= 0 or self.gradio_server_port > 65535:
            issues.append("GRADIO_SERVER_PORT must be between 1 and 65535")
        
        return issues
    
    def print_config_summary(self):
        """Print configuration summary for debugging"""
        print("🔧 BMasterAI RAG Configuration Summary:")
        print(f"   Model: {self.model_name}")
        print(f"   Embedding Model: {self.embedding_model}")
        print(f"   Qdrant URL: {self.qdrant_url}")
        print(f"   Collection: {self.collection_name}")
        print(f"   Cache Directory: {self.cache_dir}")
        print(f"   Server: {self.gradio_server_name}:{self.gradio_server_port}")
        print(f"   Debug Mode: {self.debug_mode}")
        print(f"   Performance Monitoring: {self.enable_performance_monitoring}")
        if self.qdrant_api_key:
            print(f"   Qdrant API Key: {'*' * len(self.qdrant_api_key[:4])}...")
        print(f"   API Key: {'*' * len(self.anthropic_api_key[:4])}...")


class CachedEmbeddingModel:
    """Cached embedding model for better performance"""

    def __init__(self, model_name: str, cache_dir: str = "/tmp/embedding_cache"):
        self.model = SentenceTransformer(model_name)
        self.cache = dc.Cache(cache_dir)
        self.logger = get_logger()

    def encode(self, texts: List[str]) -> List[List[float]]:
        """Encode texts with caching"""
        results = []
        cache_hits = 0

        for text in texts:
            text_hash = hashlib.md5(text.encode()).hexdigest()

            if text_hash in self.cache:
                results.append(self.cache[text_hash])
                cache_hits += 1
            else:
                embedding = self.model.encode(text).tolist()
                self.cache[text_hash] = embedding
                results.append(embedding)

        if cache_hits > 0:
            self.logger.log_event(
                "embedding_cache",
                EventType.TASK_COMPLETE,
                f"Cache hits: {cache_hits}/{len(texts)}",
                metadata={"cache_hit_rate": cache_hits / len(texts)}
            )

        return results

    def encode_single(self, text: str) -> List[float]:
        """Encode single text with caching"""
        return self.encode([text])[0]


class AsyncDocumentProcessor:
    """Handle document processing with async capabilities"""

    def __init__(self, agent_id: str, chunk_size: int = 1000, chunk_overlap: int = 200, max_workers: int = 4):
        self.agent_id = agent_id
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def extract_text_from_pdf_async(self, file_path: str) -> str:
        """Extract text from PDF file asynchronously"""
        loop = asyncio.get_event_loop()
        try:
            def extract_sync():
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text.strip()

            text = await loop.run_in_executor(self.executor, extract_sync)

            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"PDF text extraction completed",
                metadata={"file_path": file_path, "text_length": len(text)}
            )
            return text
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error extracting text from PDF: {e}",
                metadata={"file_path": file_path, "error": str(e)}
            )
            return ""

    async def extract_text_from_docx_async(self, file_path: str) -> str:
        """Extract text from DOCX file asynchronously"""
        loop = asyncio.get_event_loop()
        try:
            def extract_sync():
                doc = docx.Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text.strip()

            text = await loop.run_in_executor(self.executor, extract_sync)

            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"DOCX text extraction completed",
                metadata={"file_path": file_path, "text_length": len(text)}
            )
            return text
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error extracting text from DOCX: {e}",
                metadata={"file_path": file_path, "error": str(e)}
            )
            return ""

    async def extract_text_from_txt_async(self, file_path: str) -> str:
        """Extract text from TXT file asynchronously"""
        loop = asyncio.get_event_loop()
        try:
            def extract_sync():
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read().strip()

            text = await loop.run_in_executor(self.executor, extract_sync)

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

    async def extract_text_async(self, file_path: str, filename: str) -> str:
        """Extract text based on file extension asynchronously"""
        ext = filename.lower().split('.')[-1]

        self.logger.log_event(
            self.agent_id,
            EventType.TASK_START,
            f"Starting async text extraction from {ext} file",
            metadata={"filename": filename, "extension": ext}
        )

        if ext == 'pdf':
            return await self.extract_text_from_pdf_async(file_path)
        elif ext == 'docx':
            return await self.extract_text_from_docx_async(file_path)
        elif ext == 'txt':
            return await self.extract_text_from_txt_async(file_path)
        else:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Unsupported file type: {ext}",
                metadata={"filename": filename}
            )
            return ""

    async def process_multiple_documents_async(self, file_paths_and_names: List[Tuple[str, str]]) -> List[Tuple[bool, str, Dict]]:
        """Process multiple documents concurrently"""
        start_time = datetime.now()

        tasks = []
        for file_path, filename in file_paths_and_names:
            task = asyncio.create_task(self.process_single_document_async(file_path, filename))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        duration = (datetime.now() - start_time).total_seconds()
        success_count = sum(1 for r in results if isinstance(r, tuple) and r[0])

        self.logger.log_event(
            self.agent_id,
            EventType.TASK_COMPLETE,
            f"Batch document processing completed",
            metadata={
                "total_documents": len(file_paths_and_names),
                "successful_documents": success_count,
                "processing_time": duration
            }
        )

        return results

    async def process_single_document_async(self, file_path: str, filename: str) -> Tuple[bool, str, Dict]:
        """Process a single document asynchronously"""
        try:
            text = await self.extract_text_async(file_path, filename)
            if not text:
                return False, "Could not extract text", {}

            # Prepare metadata
            file_hash = hashlib.md5(text.encode()).hexdigest()
            metadata = {
                'filename': filename,
                'file_hash': file_hash,
                'upload_time': datetime.now().isoformat(),
                'file_size': len(text)
            }

            # Chunk document
            chunks = self.chunk_text(text, metadata)

            return True, f"Successfully processed {filename}", {
                'chunks': chunks,
                'metadata': metadata
            }

        except Exception as e:
            return False, f"Error processing {filename}: {str(e)}", {}

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

        return chunked_docs


class ImprovedVectorStore:
    """Enhanced Qdrant vector database interface with connection pooling"""

    def __init__(self, agent_id: str, config: BMasterAIRAGConfig):
        self.agent_id = agent_id
        self.config = config
        self.embedding_model = CachedEmbeddingModel(config.embedding_model, config.cache_dir)
        self.collection_name = config.collection_name
        self.logger = get_logger()
        self.monitor = get_monitor()

        # Connection pool
        self.connection_pool = []
        self.max_connections = 5
        self._init_connection_pool()

        # Initialize collection
        self._init_collection()

    def _init_connection_pool(self):
        """Initialize connection pool for better performance"""
        for _ in range(self.max_connections):
            try:
                client = QdrantClient(
                    url=self.config.qdrant_url,
                    api_key=self.config.qdrant_api_key,
                    timeout=30
                )
                self.connection_pool.append(client)
            except Exception as e:
                self.logger.log_event(
                    self.agent_id,
                    EventType.TASK_ERROR,
                    f"Failed to create connection: {e}",
                    metadata={"error": str(e)}
                )

    def get_connection(self) -> Optional[QdrantClient]:
        """Get connection from pool"""
        if self.connection_pool:
            return self.connection_pool.pop()
        else:
            # Create new connection if pool is empty
            try:
                return QdrantClient(
                    url=self.config.qdrant_url,
                    api_key=self.config.qdrant_api_key,
                    timeout=30
                )
            except Exception as e:
                self.logger.log_event(
                    self.agent_id,
                    EventType.TASK_ERROR,
                    f"Failed to create new connection: {e}",
                    metadata={"error": str(e)}
                )
                return None

    def return_connection(self, client: QdrantClient):
        """Return connection to pool"""
        if len(self.connection_pool) < self.max_connections:
            self.connection_pool.append(client)

    def _init_collection(self):
        """Initialize Qdrant collection"""
        client = self.get_connection()
        if not client:
            raise Exception("Could not establish connection to Qdrant")

        try:
            # Check if collection exists
            collections = client.get_collections()
            collection_exists = any(
                col.name == self.collection_name
                for col in collections.collections
            )

            if not collection_exists:
                # Create collection
                client.create_collection(
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
        finally:
            self.return_connection(client)

    async def add_documents_batch(self, documents: List[Dict[str, Any]], batch_size: int = 100) -> bool:
        """Add documents to vector store in batches"""
        start_time = datetime.now()
        client = self.get_connection()

        if not client:
            return False

        try:
            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                # Generate embeddings for batch
                texts = [doc['chunk_text'] for doc in batch]
                embeddings = self.embedding_model.encode(texts)

                # Create points
                points = []
                for doc, embedding in zip(batch, embeddings):
                    point = PointStruct(
                        id=doc['chunk_hash'],
                        vector=embedding,
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

                # Insert batch
                client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )

                # Small delay between batches
                await asyncio.sleep(0.1)

            # Track performance
            duration = (datetime.now() - start_time).total_seconds()
            self.monitor.track_task_duration(
                self.agent_id,
                "vector_insertion_batch",
                duration * 1000
            )

            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Added {len(documents)} document chunks to vector store",
                metadata={
                    "chunks_added": len(documents),
                    "processing_time": duration,
                    "batches": len(documents) // batch_size + 1
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
        finally:
            self.return_connection(client)

    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        start_time = datetime.now()
        client = self.get_connection()

        if not client:
            return []

        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode_single(query)

            # Search using the new query_points method
            search_result = client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                with_payload=True
            )
            results = search_result.points

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
        finally:
            self.return_connection(client)

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        client = self.get_connection()
        if not client:
            return {'error': 'No connection available'}

        try:
            info = client.get_collection(self.collection_name)
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
        finally:
            self.return_connection(client)

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the collection"""
        client = self.get_connection()
        if not client:
            return []

        try:
            # Use scroll to get all points
            result = client.scroll(
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
        finally:
            self.return_connection(client)


class ImprovedAnthropicChat:
    """Enhanced Anthropic API interface with retry logic"""

    def __init__(self, agent_id: str, config: BMasterAIRAGConfig):
        self.agent_id = agent_id
        self.config = config
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.logger = get_logger()
        self.monitor = get_monitor()

        # Response cache
        self.response_cache = dc.Cache(os.path.join(config.cache_dir, "responses"))

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for API request"""
        return {
            "Content-Type": "application/json",
            "x-api-key": self.config.anthropic_api_key,
            "anthropic-version": "2023-06-01"
        }

    def _get_cache_key(self, query: str, context: str) -> str:
        """Generate cache key for query and context"""
        combined = f"{query}|{context}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _make_api_request(self, payload: Dict) -> requests.Response:
        """Make API request with simple retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self._prepare_headers(),
                    json=payload,
                    timeout=30
                )
                return response
            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff
        
    def _make_api_request_original(self, payload: Dict) -> requests.Response:
        """Make API request with retry logic"""
        return requests.post(
            self.base_url,
            headers=self._prepare_headers(),
            json=payload,
            timeout=60
        )

    def generate_response(self, query: str, context: str) -> str:
        """Generate response using context and query with caching"""
        start_time = datetime.now()

        # Check cache first
        cache_key = self._get_cache_key(query, context)
        if cache_key in self.response_cache:
            self.logger.log_event(
                self.agent_id,
                EventType.LLM_RESPONSE,
                f"Cache hit for query",
                metadata={"query_length": len(query), "cached": True}
            )
            return self.response_cache[cache_key]

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

            # Make API request with retry
            response = self._make_api_request(payload)

            if response.status_code == 200:
                result = response.json()
                answer = result["content"][0]["text"]

                # Cache the response
                self.response_cache[cache_key] = answer

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
                        "usage": usage,
                        "cached": False
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


class EnhancedBMasterAIRAGSystem:
    """Enhanced main RAG system with async processing and performance improvements"""

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

        # Initialize enhanced RAG components
        self.doc_processor = AsyncDocumentProcessor(
            self.agent_id,
            config.chunk_size,
            config.chunk_overlap,
            max_workers=config.max_concurrent_uploads
        )
        self.vector_store = ImprovedVectorStore(self.agent_id, config)
        self.chat = ImprovedAnthropicChat(self.agent_id, config)

        # Session tracking
        self.session_stats = {
            'documents_uploaded': 0,
            'queries_processed': 0,
            'cache_hits': 0,
            'start_time': datetime.now().isoformat()
        }

        # Performance metrics
        self.performance_metrics = {
            'avg_upload_time': 0.0,
            'avg_query_time': 0.0,
            'success_rate': 100.0,
            'total_errors': 0
        }

        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            f"Enhanced BMasterAI RAG System initialized",
            metadata={
                "agent_id": self.agent_id,
                "model": config.model_name,
                "embedding_model": config.embedding_model,
                "async_enabled": True,
                "caching_enabled": True
            }
        )

    async def upload_documents_async(self, file_paths_and_names: List[Tuple[str, str]]) -> Tuple[int, int, List[str]]:
        """Upload multiple documents asynchronously"""
        start_time = datetime.now()

        self.logger.log_event(
            self.agent_id,
            EventType.TASK_START,
            f"Starting batch document upload: {len(file_paths_and_names)} files",
            metadata={"file_count": len(file_paths_and_names)}
        )

        # Process documents concurrently
        results = await self.doc_processor.process_multiple_documents_async(file_paths_and_names)

        # Collect all chunks for batch insertion
        all_chunks = []
        success_count = 0
        error_messages = []

        for result in results:
            if isinstance(result, Exception):
                error_messages.append(f"Exception: {str(result)}")
            elif result[0]:  # Success
                success_count += 1
                all_chunks.extend(result[2]['chunks'])
            else:  # Failed
                error_messages.append(result[1])

        # Batch insert all chunks
        if all_chunks:
            insert_success = await self.vector_store.add_documents_batch(all_chunks)
            if not insert_success:
                error_messages.append("Failed to insert chunks into vector store")
                success_count = 0

        # Update session stats
        self.session_stats['documents_uploaded'] += success_count

        # Update performance metrics
        duration = (datetime.now() - start_time).total_seconds()
        self.performance_metrics['avg_upload_time'] = (
            (self.performance_metrics['avg_upload_time'] + duration) / 2
            if self.performance_metrics['avg_upload_time'] > 0 else duration
        )

        if len(file_paths_and_names) > 0:
            self.performance_metrics['success_rate'] = (success_count / len(file_paths_and_names)) * 100

        self.monitor.track_task_duration(
            self.agent_id,
            "batch_document_upload",
            duration * 1000
        )

        self.logger.log_event(
            self.agent_id,
            EventType.TASK_COMPLETE,
            f"Batch document upload completed",
            metadata={
                "total_files": len(file_paths_and_names),
                "successful_files": success_count,
                "total_chunks": len(all_chunks),
                "processing_time": duration,
                "success_rate": self.performance_metrics['success_rate']
            }
        )

        # Send notification if configured
        if success_count > 0:
            self.integration_manager.send_notification(
                f"✅ Batch upload completed: {success_count}/{len(file_paths_and_names)} files\n"
                f"📊 Total chunks created: {len(all_chunks)}\n"
                f"⏱️ Processing time: {duration:.2f}s"
            )

        return success_count, len(file_paths_and_names), error_messages

    async def upload_document_async(self, file_path: str, filename: str) -> Tuple[bool, str]:
        """Upload and process a single document asynchronously"""
        start_time = datetime.now()

        try:
            # Validate file
            if not self._validate_file(file_path, filename):
                return False, "File validation failed"

            self.logger.log_event(
                self.agent_id,
                EventType.TASK_START,
                f"Starting document upload: {filename}",
                metadata={"filename": filename}
            )

            # Process document
            success, message, data = await self.doc_processor.process_single_document_async(file_path, filename)

            if not success:
                return False, message

            # Add to vector store
            chunks = data['chunks']
            if chunks:
                insert_success = await self.vector_store.add_documents_batch(chunks)
                if not insert_success:
                    return False, "Failed to add document to vector store"

            # Update stats
            self.session_stats['documents_uploaded'] += 1
            duration = (datetime.now() - start_time).total_seconds()

            self.monitor.track_task_duration(
                self.agent_id,
                "single_document_upload",
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

            return True, f"Successfully uploaded {filename} with {len(chunks)} chunks"

        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error uploading document: {e}",
                metadata={"filename": filename, "error": str(e)}
            )
            self.monitor.track_error(self.agent_id, "document_upload_error")
            self.performance_metrics['total_errors'] += 1
            return False, f"Error uploading document: {str(e)}"

    def _validate_file(self, file_path: str, filename: str) -> bool:
        """Validate uploaded file"""
        try:
            # Check file exists
            if not os.path.exists(file_path):
                return False

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.config.max_file_size:
                return False

            # Check file extension
            allowed_extensions = ['.pdf', '.docx', '.txt']
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in allowed_extensions:
                return False

            return True

        except Exception:
            return False

    def search_and_answer(self, query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Search documents and generate answer"""
        # Ensure query is a string
        if not isinstance(query, str):
            query = str(query) if query is not None else ""
            
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

            # Filter by similarity threshold
            filtered_results = [
                result for result in search_results
                if result['score'] >= self.config.similarity_threshold
            ]

            if not filtered_results:
                return "No sufficiently relevant documents found for your query.", search_results

            # Prepare context
            context = "\n\n".join([
                f"Document: {result['filename']}\n{result['text']}"
                for result in filtered_results
            ])

            # Generate response
            response = self.chat.generate_response(query, context)

            # Update stats
            self.session_stats['queries_processed'] += 1
            duration = (datetime.now() - start_time).total_seconds()

            self.performance_metrics['avg_query_time'] = (
                (self.performance_metrics['avg_query_time'] + duration) / 2
                if self.performance_metrics['avg_query_time'] > 0 else duration
            )

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
                    "documents_used": len(filtered_results)
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
            self.performance_metrics['total_errors'] += 1
            return f"Error processing query: {str(e)}", []

    def get_system_status(self) -> Dict[str, Any]:
        """Get enhanced system status information"""
        try:
            collection_info = self.vector_store.get_collection_info()
            agent_dashboard = self.monitor.get_agent_dashboard(self.agent_id)

            return {
                'session_stats': self.session_stats,
                'performance_metrics': self.performance_metrics,
                'collection_info': collection_info,
                'agent_performance': agent_dashboard,
                'system_health': self.monitor.get_system_health(),
                'config': {
                    'model_name': self.config.model_name,
                    'embedding_model': self.config.embedding_model,
                    'collection_name': self.config.collection_name,
                    'chunk_size': self.config.chunk_size,
                    'top_k': self.config.top_k,
                    'max_concurrent_uploads': self.config.max_concurrent_uploads,
                    'caching_enabled': True
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def shutdown(self):
        """Gracefully shutdown the RAG system"""
        self.monitor.track_agent_stop(self.agent_id)
        self.monitor.stop_monitoring()

        # Close executor
        if hasattr(self.doc_processor, 'executor'):
            self.doc_processor.executor.shutdown(wait=True)

        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_STOP,
            f"Enhanced BMasterAI RAG System shutdown",
            metadata={
                "total_documents": self.session_stats['documents_uploaded'],
                "total_queries": self.session_stats['queries_processed'],
                "total_errors": self.performance_metrics['total_errors']
            }
        )


class BMasterAIRAGApp:
    """Complete Gradio application for RAG system with BMasterAI framework"""

    def __init__(self):
        # Configure BMasterAI logging
        try:
            configure_logging()
        except Exception as e:
            print(f"⚠️  Could not configure BMasterAI logging: {e}")
            # Fall back to basic Python logging
            import logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Initialize configuration from environment variables
        self.config = BMasterAIRAGConfig()

        # Setup integrations if configured
        self._setup_integrations()

        # Initialize RAG system
        self._initialize_rag_system()

    def _setup_integrations(self):
        """Setup external integrations"""
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

    def _initialize_rag_system(self):
        """Initialize the RAG system"""
        try:
            self.rag_system = EnhancedBMasterAIRAGSystem(self.config)
            self.system_status = "✅ Enhanced RAG System Initialized with BMasterAI Framework"
        except Exception as e:
            get_logger().log_event(
                "app",
                EventType.TASK_ERROR,
                f"Failed to initialize RAG system: {e}",
                metadata={"error": str(e)}
            )
            self.system_status = f"❌ System Error: {e}"
            self.rag_system = None

    def upload_file(self, file) -> str:
        """Handle single file upload"""
        if not self.rag_system:
            return "❌ System not initialized"

        if file is None:
            return "❌ No file selected"

        try:
            filename = os.path.basename(file.name)
            file_path = file.name

            # Check file type
            allowed_extensions = ['.pdf', '.docx', '.txt']
            file_ext = os.path.splitext(filename)[1].lower()

            if file_ext not in allowed_extensions:
                return f"❌ Unsupported file type: {file_ext}. Supported: {', '.join(allowed_extensions)}"

            # Use async upload with asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                success, message = loop.run_until_complete(
                    self.rag_system.upload_document_async(file_path, filename)
                )

                if success:
                    return f"✅ {message}"
                else:
                    return f"❌ {message}"
            finally:
                loop.close()

        except Exception as e:
            return f"❌ Error uploading file: {str(e)}"

    def upload_multiple_files(self, files) -> str:
        """Handle multiple file uploads"""
        if not self.rag_system:
            return "❌ System not initialized"

        if not files:
            return "❌ No files selected"

        try:
            # Prepare file paths and names
            file_paths_and_names = []
            invalid_files = []

            for file in files:
                filename = os.path.basename(file.name)
                file_path = file.name

                # Check file type
                allowed_extensions = ['.pdf', '.docx', '.txt']
                file_ext = os.path.splitext(filename)[1].lower()

                if file_ext not in allowed_extensions:
                    invalid_files.append(f"❌ {filename}: Unsupported file type")
                    continue

                file_paths_and_names.append((file_path, filename))

            if not file_paths_and_names:
                return "❌ No valid files to upload"

            # Use async batch upload
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                success_count, total_count, error_messages = loop.run_until_complete(
                    self.rag_system.upload_documents_async(file_paths_and_names)
                )

                results = []
                results.append(f"📊 Summary: {success_count}/{total_count} files uploaded successfully")

                if invalid_files:
                    results.extend(invalid_files)

                if error_messages:
                    results.extend([f"❌ {msg}" for msg in error_messages])

                if success_count > 0:
                    results.append(f"✅ {success_count} files processed successfully")

                return "\n".join(results)
            finally:
                loop.close()

        except Exception as e:
            return f"❌ Error uploading files: {str(e)}"

    def chat_interface(self, message: str, history: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
        """Enhanced chat interface for questions"""
        # Ensure message is a string
        if not isinstance(message, str):
            message = str(message) if message is not None else ""
        
        if not self.rag_system:
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": "❌ System not initialized"})
            return "", history

        if not message.strip():
            return "", history

        try:
            # Add user message to history
            history.append({"role": "user", "content": message})
            
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

            # Add assistant response to history
            history.append({"role": "assistant", "content": full_response})
            return "", history

        except Exception as e:
            error_response = f"❌ Error processing question: {str(e)}"
            history.append({"role": "assistant", "content": error_response})
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

### ⚡ Performance Metrics:
- **Average Upload Time**: {status['performance_metrics']['avg_upload_time']:.2f}s
- **Average Query Time**: {status['performance_metrics']['avg_query_time']:.2f}s
- **Success Rate**: {status['performance_metrics']['success_rate']:.1f}%
- **Total Errors**: {status['performance_metrics']['total_errors']}

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
- **Max Concurrent Uploads**: {status['config']['max_concurrent_uploads']}
- **Caching**: {'✅ Enabled' if status['config']['caching_enabled'] else '❌ Disabled'}

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
        """Get enhanced performance metrics"""
        if not self.rag_system:
            return "❌ System not initialized"

        try:
            dashboard = self.rag_system.monitor.get_agent_dashboard(self.rag_system.agent_id)

            metrics_text = "📈 **Performance Metrics:**\n\n"

            # Task performance
            if dashboard.get('performance'):
                for task_name, metrics in dashboard['performance'].items():
                    metrics_text += f"**{task_name.replace('_', ' ').title()}:**\n"
                    metrics_text += f"- Average Duration: {metrics.get('avg_duration_ms', 0):.2f}ms\n"
                    metrics_text += f"- Min Duration: {metrics.get('min_duration_ms', 0):.2f}ms\n"
                    metrics_text += f"- Max Duration: {metrics.get('max_duration_ms', 0):.2f}ms\n"
                    metrics_text += f"- Total Calls: {metrics.get('total_calls', 0)}\n\n"

            # System metrics
            metrics_text += f"**System Metrics:**\n"
            metrics_text += f"- Total Errors: {dashboard.get('metrics', {}).get('total_errors', 0)}\n"
            metrics_text += f"- Agent Status: {dashboard.get('status', 'Unknown')}\n"

            # Cache performance
            metrics_text += f"- Cache Performance: Enabled\n"
            metrics_text += f"- Async Processing: Enabled\n"

            return metrics_text

        except Exception as e:
            return f"❌ Error getting performance metrics: {str(e)}"

    def clear_cache(self) -> str:
        """Clear system caches"""
        if not self.rag_system:
            return "❌ System not initialized"

        try:
            # Clear embedding cache
            if hasattr(self.rag_system.vector_store.embedding_model, 'cache'):
                self.rag_system.vector_store.embedding_model.cache.clear()

            # Clear response cache
            if hasattr(self.rag_system.chat, 'response_cache'):
                self.rag_system.chat.response_cache.clear()

            return "✅ Cache cleared successfully"

        except Exception as e:
            return f"❌ Error clearing cache: {str(e)}"

    def create_interface(self) -> gr.Blocks:
        """Create the complete enhanced Gradio interface"""

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
        .performance-box {
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #ffc107;
            margin: 10px 0;
        }
        """

        with gr.Blocks(css=custom_css, title="Enhanced BMasterAI RAG System", theme=gr.themes.Soft()) as demo:

            # Header
            gr.HTML("""
            <div class="header-text">
            🧠 Enhanced BMasterAI RAG System
            </div>
            <div style="text-align: center; margin-bottom: 30px;">
            <p style="font-size: 1.2em; color: #666;">
            Advanced Document Q&A with Async Processing, Caching & Performance Optimization
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
                                type="messages"
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
                                    "What information is in the database"                             
                                ]

                                for question in example_questions:
                                    example_q_btn = gr.Button(f"❓ {question}", size="sm")
                                    # Just set the question text in the input box
                                    example_q_btn.click(
                                        fn=lambda q=question: q,
                                        inputs=None,
                                        outputs=[msg]
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
                            <p>Enhanced with async processing and batch uploads</p>
                            <p>Maximum file size: 50MB per file</p>
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
                                gr.HTML("<h4>Batch File Upload (Async)</h4>")
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

                            # Cache management
                            gr.HTML("<h3>⚡ Cache Management</h3>")
                            cache_info = gr.Markdown("Cache status: Enabled")
                            clear_cache_btn = gr.Button("Clear Cache", variant="secondary")
                            cache_result = gr.Textbox(label="Cache Result", interactive=False, lines=2)

                # System Status Tab
                with gr.TabItem("🖥️ System Status", elem_id="status-tab"):
                    system_status_md = gr.Markdown(self.get_system_status())

            # Event bindings

            # Chat interactions
            submit_btn.click(
                self.chat_interface,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            clear_btn.click(
                lambda: ([], []),
                inputs=None,
                outputs=[msg, chatbot]
            )
            example_btn.click(
                lambda: ("", []),
                inputs=None,
                outputs=[msg, chatbot]
            )

            # Quick search
            search_btn.click(
                self.search_documents,
                inputs=search_input,
                outputs=search_results
            )

            # Single file upload
            single_upload_btn.click(
                self.upload_file,
                inputs=single_file,
                outputs=single_result
            )

            # Multiple file upload
            multiple_upload_btn.click(
                self.upload_multiple_files,
                inputs=multiple_files,
                outputs=multiple_result
            )

            # Refresh document list
            refresh_docs_btn.click(
                self.list_documents,
                inputs=None,
                outputs=document_list
            )

            # Refresh upload stats
            refresh_stats_btn.click(
                self.get_system_status,
                inputs=None,
                outputs=upload_stats
            )

            # Clear cache
            clear_cache_btn.click(
                self.clear_cache,
                inputs=None,
                outputs=cache_result
            )

        return demo


def main():
    """Main function to run the Enhanced BMasterAI RAG System"""
    try:
        print("🚀 Starting Enhanced BMasterAI RAG System...")
        
        # Load and validate configuration
        config = BMasterAIRAGConfig()
        
        # Validate configuration
        issues = config.validate_config()
        if issues:
            print("❌ Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
            exit(1)
        
        # Print configuration summary if in debug mode
        if config.debug_mode:
            config.print_config_summary()
        
        # Configure logging based on environment
        try:
            # Try to configure BMasterAI logging
            configure_logging()
        except Exception as e:
            print(f"⚠️  Could not configure BMasterAI logging: {e}")
            # Fall back to basic Python logging
            import logging
            logging.basicConfig(
                level=getattr(logging, config.log_level.upper(), logging.INFO),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Create the Gradio app (it will initialize its own RAG system)
        app = BMasterAIRAGApp()
        demo = app.create_interface()
        
        # Prepare launch arguments
        launch_kwargs = {
            'server_name': config.gradio_server_name,
            'server_port': config.gradio_server_port,
            'share': config.gradio_share,
            'debug': config.debug_mode,
            'show_error': config.debug_mode,
            'quiet': not config.verbose_logging
        }
        
        # Add authentication if configured
        if config.gradio_auth and config.gradio_auth.strip():
            # Remove any inline comments
            auth_value = config.gradio_auth.split('#')[0].strip()
            if auth_value and ':' in auth_value:
                username, password = auth_value.split(':', 1)
                launch_kwargs['auth'] = (username.strip(), password.strip())
                print(f"🔐 Authentication enabled for user: {username.strip()}")
            elif auth_value:
                print("⚠️  GRADIO_AUTH format should be 'username:password'")
            else:
                print("ℹ️  Authentication disabled (GRADIO_AUTH is empty)")
        
        print(f"🌐 Starting server on {config.gradio_server_name}:{config.gradio_server_port}")
        print(f"📊 Performance monitoring: {'enabled' if config.enable_performance_monitoring else 'disabled'}")
        print(f"💾 Caching: {'enabled' if config.enable_response_cache else 'disabled'}")
        
        # Launch the application
        demo.launch(**launch_kwargs)
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Enhanced BMasterAI RAG System...")
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        if config and config.debug_mode:
            import traceback
            traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()