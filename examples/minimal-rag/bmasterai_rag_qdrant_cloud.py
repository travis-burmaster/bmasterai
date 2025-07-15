#!/usr/bin/env python3
"""
BMasterAI RAG with Qdrant Cloud Integration
Advanced RAG system using Qdrant Cloud vector database with BMasterAI framework
"""

import os
import json
import time
import uuid
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# BMasterAI imports
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor

# External dependencies
try:
    import openai
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    import numpy as np
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Install with: pip install openai qdrant-client sentence-transformers numpy")
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

class BMasterAIQdrantRAG:
    """
    Advanced RAG system using Qdrant Cloud and BMasterAI framework
    """
    
    def __init__(self, qdrant_config: QdrantConfig, rag_config: RAGConfig):
        self.qdrant_config = qdrant_config
        self.rag_config = rag_config
        
        # Initialize BMasterAI components
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.agent_id = "qdrant-rag-agent"
        
        # Initialize clients
        self._init_qdrant_client()
        self._init_openai_client()
        self._init_embedding_model()
        
        # Log initialization
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            "BMasterAI Qdrant RAG system initialized",
            metadata={
                "qdrant_url": self.qdrant_config.url,
                "collection": self.qdrant_config.collection_name,
                "embedding_model": self.rag_config.embedding_model,
                "llm_model": self.rag_config.llm_model
            }
        )
    
    def _init_qdrant_client(self):
        """Initialize Qdrant Cloud client"""
        try:
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
            
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Failed to connect to Qdrant Cloud: {str(e)}",
                level=LogLevel.ERROR
            )
            raise
    
    def _init_openai_client(self):
        """Initialize OpenAI client"""
        try:
            openai.api_key = self.rag_config.openai_api_key
            self.openai_client = openai
            
            self.logger.log_event(
                self.agent_id,
                EventType.AGENT_COMMUNICATION,
                "OpenAI client initialized",
                metadata={"model": self.rag_config.llm_model}
            )
            
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Failed to initialize OpenAI client: {str(e)}",
                level=LogLevel.ERROR
            )
            raise
    
    def _init_embedding_model(self):
        """Initialize sentence transformer model for embeddings"""
        try:
            self.embedding_model = SentenceTransformer(self.rag_config.embedding_model)
            
            self.logger.log_event(
                self.agent_id,
                EventType.AGENT_START,
                "Embedding model loaded successfully",
                metadata={"model": self.rag_config.embedding_model}
            )
            
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Failed to load embedding model: {str(e)}",
                level=LogLevel.ERROR
            )
            raise
    
    def create_collection(self) -> bool:
        """Create Qdrant collection if it doesn't exist"""
        start_time = time.time()
        
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.qdrant_config.collection_name in collection_names:
                self.logger.log_event(
                    self.agent_id,
                    EventType.TASK_COMPLETE,
                    f"Collection '{self.qdrant_config.collection_name}' already exists"
                )
                return True
            
            # Create collection
            self.qdrant_client.create_collection(
                collection_name=self.qdrant_config.collection_name,
                vectors_config=VectorParams(
                    size=self.qdrant_config.vector_size,
                    distance=self.qdrant_config.distance
                )
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Created collection '{self.qdrant_config.collection_name}'",
                duration_ms=duration_ms,
                metadata={
                    "vector_size": self.qdrant_config.vector_size,
                    "distance": self.qdrant_config.distance.value
                }
            )
            
            self.monitor.track_task_duration(self.agent_id, "create_collection", duration_ms)
            return True
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Failed to create collection: {str(e)}",
                level=LogLevel.ERROR,
                duration_ms=duration_ms
            )
            
            self.monitor.track_error(self.agent_id, "create_collection")
            return False
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents to Qdrant collection
        
        Args:
            documents: List of documents with 'text', 'metadata' fields
        """
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
                
                # Log progress for large batches
                if (i + 1) % 100 == 0:
                    self.logger.log_event(
                        self.agent_id,
                        EventType.PERFORMANCE_METRIC,
                        f"Processed {i + 1}/{len(documents)} documents",
                        metadata={"task_id": task_id}
                    )
            
            # Upload to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.qdrant_config.collection_name,
                points=points
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Successfully added {len(documents)} documents",
                duration_ms=duration_ms,
                metadata={
                    "task_id": task_id,
                    "document_count": len(documents),
                    "collection": self.qdrant_config.collection_name
                }
            )
            
            self.monitor.track_task_duration(self.agent_id, "add_documents", duration_ms)
            return True
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Failed to add documents: {str(e)}",
                level=LogLevel.ERROR,
                duration_ms=duration_ms,
                metadata={"task_id": task_id}
            )
            
            self.monitor.track_error(self.agent_id, "add_documents")
            return False
    
    def search_similar(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents in Qdrant
        
        Args:
            query: Search query text
            limit: Maximum number of results (default: top_k_results from config)
        
        Returns:
            List of similar documents with scores
        """
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        if limit is None:
            limit = self.rag_config.top_k_results
        
        try:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_START,
                f"Searching for similar documents: '{query[:50]}...'",
                metadata={"task_id": task_id, "limit": limit}
            )
            
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
                    "task_id": task_id,
                    "query_length": len(query),
                    "results_count": len(results),
                    "avg_score": np.mean([r["score"] for r in results]) if results else 0
                }
            )
            
            self.monitor.track_task_duration(self.agent_id, "search_similar", duration_ms)
            return results
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Failed to search documents: {str(e)}",
                level=LogLevel.ERROR,
                duration_ms=duration_ms,
                metadata={"task_id": task_id}
            )
            
            self.monitor.track_error(self.agent_id, "search_similar")
            return []
    
    def generate_answer(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Generate answer using OpenAI with retrieved context
        
        Args:
            query: User question
            context_docs: Retrieved documents for context
        
        Returns:
            Generated answer
        """
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        try:
            self.logger.log_event(
                self.agent_id,
                EventType.LLM_CALL,
                f"Generating answer for query: '{query[:50]}...'",
                metadata={
                    "task_id": task_id,
                    "context_docs_count": len(context_docs),
                    "model": self.rag_config.llm_model
                }
            )
            
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
                    "task_id": task_id,
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
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Failed to generate answer: {str(e)}",
                level=LogLevel.ERROR,
                duration_ms=duration_ms,
                metadata={"task_id": task_id}
            )
            
            self.monitor.track_error(self.agent_id, "generate_answer")
            return f"Error generating answer: {str(e)}"
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Complete RAG query: search + generate answer
        
        Args:
            question: User question
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        try:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_START,
                f"Processing RAG query: '{question[:50]}...'",
                metadata={"task_id": task_id}
            )
            
            # Step 1: Search for similar documents
            similar_docs = self.search_similar(question)
            
            if not similar_docs:
                return {
                    "answer": "I couldn't find relevant information to answer your question.",
                    "sources": [],
                    "metadata": {
                        "task_id": task_id,
                        "documents_found": 0,
                        "processing_time_ms": (time.time() - start_time) * 1000
                    }
                }
            
            # Step 2: Generate answer
            answer = self.generate_answer(question, similar_docs)
            
            duration_ms = (time.time() - start_time) * 1000
            
            result = {
                "answer": answer,
                "sources": similar_docs,
                "metadata": {
                    "task_id": task_id,
                    "documents_found": len(similar_docs),
                    "processing_time_ms": duration_ms,
                    "avg_similarity_score": np.mean([doc["score"] for doc in similar_docs])
                }
            }
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                "RAG query completed successfully",
                duration_ms=duration_ms,
                metadata={
                    "task_id": task_id,
                    "question_length": len(question),
                    "answer_length": len(answer),
                    "sources_count": len(similar_docs)
                }
            )
            
            self.monitor.track_task_duration(self.agent_id, "rag_query", duration_ms)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"RAG query failed: {str(e)}",
                level=LogLevel.ERROR,
                duration_ms=duration_ms,
                metadata={"task_id": task_id}
            )
            
            self.monitor.track_error(self.agent_id, "rag_query")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "metadata": {
                    "task_id": task_id,
                    "error": str(e),
                    "processing_time_ms": duration_ms
                }
            }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the Qdrant collection"""
        try:
            collection_info = self.qdrant_client.get_collection(self.qdrant_config.collection_name)
            
            return {
                "name": collection_info.config.params.vectors.size,
                "vector_size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance.value,
                "points_count": collection_info.points_count,
                "status": collection_info.status.value
            }
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Failed to get collection info: {str(e)}",
                level=LogLevel.ERROR
            )
            return {"error": str(e)}

def main():
    """
    Example usage of BMasterAI Qdrant RAG system
    """
    
    # Configure logging
    configure_logging(log_level=LogLevel.INFO)
    
    # Start monitoring
    monitor = get_monitor()
    monitor.start_monitoring()
    
    # Configuration
    qdrant_config = QdrantConfig(
        url=os.getenv("QDRANT_URL", "https://your-cluster.qdrant.io"),
        api_key=os.getenv("QDRANT_API_KEY", ""),
        collection_name="bmasterai_knowledge_base"
    )
    
    rag_config = RAGConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        embedding_model="all-MiniLM-L6-v2",
        llm_model="gpt-3.5-turbo",
        top_k_results=3
    )
    
    # Validate configuration
    if not qdrant_config.api_key:
        print("❌ QDRANT_API_KEY environment variable not set!")
        print("Get your API key from: https://cloud.qdrant.io/")
        return
    
    if not rag_config.openai_api_key:
        print("❌ OPENAI_API_KEY environment variable not set!")
        return
    
    try:
        # Initialize RAG system
        print("🚀 Initializing BMasterAI Qdrant RAG system...")
        rag_system = BMasterAIQdrantRAG(qdrant_config, rag_config)
        
        # Create collection
        print("📦 Creating Qdrant collection...")
        rag_system.create_collection()
        
        # Sample documents
        sample_docs = [
            {
                "text": "BMasterAI is an advanced multi-agent AI framework for Python that provides comprehensive logging, monitoring, and integrations for building production-ready AI systems.",
                "metadata": {"category": "framework", "topic": "bmasterai"},
                "source": "documentation"
            },
            {
                "text": "Qdrant is a vector database that enables similarity search and recommendations. It supports high-performance vector operations and can be deployed in the cloud.",
                "metadata": {"category": "database", "topic": "qdrant"},
                "source": "documentation"
            },
            {
                "text": "RAG (Retrieval-Augmented Generation) combines information retrieval with language generation to provide more accurate and contextual responses by grounding answers in retrieved documents.",
                "metadata": {"category": "technique", "topic": "rag"},
                "source": "research"
            },
            {
                "text": "Vector embeddings are numerical representations of text that capture semantic meaning, enabling similarity search and clustering of documents based on their content.",
                "metadata": {"category": "concept", "topic": "embeddings"},
                "source": "tutorial"
            }
        ]
        
        # Add documents
        print("📚 Adding sample documents...")
        rag_system.add_documents(sample_docs)
        
        # Get collection info
        print("ℹ️ Collection information:")
        info = rag_system.get_collection_info()
        print(json.dumps(info, indent=2))
        
        # Example queries
        queries = [
            "What is BMasterAI?",
            "How does RAG work?",
            "What are vector embeddings?",
            "Tell me about Qdrant database"
        ]
        
        print("\n🤖 Running example queries...")
        for query in queries:
            print(f"\n❓ Query: {query}")
            result = rag_system.query(query)
            
            print(f"💬 Answer: {result['answer']}")
            print(f"📊 Sources found: {result['metadata']['documents_found']}")
            print(f"⏱️ Processing time: {result['metadata']['processing_time_ms']:.2f}ms")
            
            if result['sources']:
                print("📄 Top source:")
                top_source = result['sources'][0]
                print(f"   Score: {top_source['score']:.3f}")
                print(f"   Text: {top_source['text'][:100]}...")
        
        # Get system dashboard
        print("\n📊 System Performance Dashboard:")
        dashboard = monitor.get_agent_dashboard("qdrant-rag-agent")
        print(json.dumps(dashboard, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        # Stop monitoring
        monitor.stop_monitoring()
        print("\n✅ BMasterAI Qdrant RAG example completed!")

if __name__ == "__main__":
    main()