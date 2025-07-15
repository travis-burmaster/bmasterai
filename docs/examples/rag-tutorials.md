# RAG Tutorials

Complete step-by-step tutorials for building Retrieval-Augmented Generation systems with BMasterAI and Qdrant Cloud.

## 🎯 Tutorial Overview

This tutorial series covers:
1. **[Basic RAG Setup](#tutorial-1-basic-rag-setup)** - Your first RAG system
2. **[Web Interface](#tutorial-2-web-interface)** - Interactive Gradio UI
3. **[Advanced Features](#tutorial-3-advanced-features)** - Custom configurations and optimization
4. **[Production Deployment](#tutorial-4-production-deployment)** - Deploy to production

## 📋 Prerequisites

Before starting, ensure you have:
- Python 3.8+ installed
- BMasterAI framework installed (`pip install bmasterai`)
- Qdrant Cloud account and API key
- OpenAI API key

## Tutorial 1: Basic RAG Setup

### Step 1: Environment Setup

Create a new directory for your RAG project:

```bash
mkdir my-rag-system
cd my-rag-system
```

Install required dependencies:

```bash
pip install bmasterai qdrant-client openai sentence-transformers numpy
```

### Step 2: Get Your API Keys

#### Qdrant Cloud Setup
1. Visit [https://cloud.qdrant.io/](https://cloud.qdrant.io/)
2. Create a free account
3. Create a new cluster
4. Copy your cluster URL and API key

#### OpenAI Setup
1. Visit [https://platform.openai.com/](https://platform.openai.com/)
2. Create an account or log in
3. Generate an API key

### Step 3: Set Environment Variables

```bash
export QDRANT_URL="https://your-cluster.qdrant.io"
export QDRANT_API_KEY="your-qdrant-api-key"
export OPENAI_API_KEY="your-openai-api-key"
```

Or create a `.env` file:

```env
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
OPENAI_API_KEY=your-openai-api-key
```

### Step 4: Test Your Connections

Create `test_connections.py`:

```python
#!/usr/bin/env python3
"""Test script for API connections"""

import os
from qdrant_client import QdrantClient
import openai
from sentence_transformers import SentenceTransformer

def test_qdrant():
    """Test Qdrant Cloud connection"""
    try:
        client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        collections = client.get_collections()
        print("✅ Qdrant Cloud: Connected successfully")
        return True
    except Exception as e:
        print(f"❌ Qdrant Cloud: {e}")
        return False

def test_openai():
    """Test OpenAI API connection"""
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print("✅ OpenAI API: Connected successfully")
        return True
    except Exception as e:
        print(f"❌ OpenAI API: {e}")
        return False

def test_embeddings():
    """Test embedding model"""
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = model.encode("Test sentence")
        print(f"✅ Embeddings: Model loaded (size: {len(embedding)})")
        return True
    except Exception as e:
        print(f"❌ Embeddings: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing API connections...")
    
    qdrant_ok = test_qdrant()
    openai_ok = test_openai()
    embeddings_ok = test_embeddings()
    
    if all([qdrant_ok, openai_ok, embeddings_ok]):
        print("\n🎉 All connections successful! Ready to build RAG system.")
    else:
        print("\n⚠️ Some connections failed. Please check your configuration.")
```

Run the test:

```bash
python test_connections.py
```

### Step 5: Create Your First RAG System

Create `basic_rag.py`:

```python
#!/usr/bin/env python3
"""Basic RAG system with BMasterAI and Qdrant Cloud"""

import os
import time
from typing import List, Dict, Any

# BMasterAI imports
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor

# RAG imports
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import openai
import hashlib

class SimpleRAGSystem:
    def __init__(self):
        # Configure BMasterAI
        configure_logging(log_level=LogLevel.INFO)
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.monitor.start_monitoring()
        
        self.agent_id = "simple-rag"
        
        # Initialize components
        self._init_qdrant()
        self._init_openai()
        self._init_embeddings()
        
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            "Simple RAG system initialized"
        )
    
    def _init_qdrant(self):
        """Initialize Qdrant client"""
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = "simple_rag_demo"
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        openai.api_key = os.getenv("OPENAI_API_KEY")
    
    def _init_embeddings(self):
        """Initialize embedding model"""
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def create_collection(self):
        """Create Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            if self.collection_name in [c.name for c in collections.collections]:
                print(f"✅ Collection '{self.collection_name}' already exists")
                return
            
            # Create collection
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"✅ Created collection '{self.collection_name}'")
            
        except Exception as e:
            print(f"❌ Error creating collection: {e}")
    
    def add_documents(self, documents: List[str]):
        """Add documents to the knowledge base"""
        start_time = time.time()
        
        try:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_START,
                f"Adding {len(documents)} documents"
            )
            
            points = []
            for i, doc in enumerate(documents):
                # Generate embedding
                embedding = self.embedding_model.encode(doc).tolist()
                
                # Create unique ID
                doc_id = hashlib.md5(doc.encode()).hexdigest()
                
                # Create point
                point = PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={"text": doc, "index": i}
                )
                points.append(point)
            
            # Upload to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Added {len(documents)} documents",
                duration_ms=duration_ms
            )
            
            print(f"✅ Added {len(documents)} documents in {duration_ms:.0f}ms")
            
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Failed to add documents: {e}",
                level=LogLevel.ERROR
            )
            print(f"❌ Error adding documents: {e}")
    
    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search in Qdrant
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=0.5
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "text": result.payload["text"],
                    "score": result.score,
                    "id": result.id
                })
            
            print(f"🔍 Found {len(formatted_results)} relevant documents")
            return formatted_results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def generate_answer(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate answer using OpenAI"""
        try:
            # Prepare context
            context = "\n\n".join([doc["text"] for doc in context_docs])
            
            # Create prompt
            prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer:"""
            
            # Call OpenAI
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            
            self.logger.log_event(
                self.agent_id,
                EventType.LLM_CALL,
                "Generated answer",
                metadata={"tokens": response.usage.total_tokens}
            )
            
            return answer
            
        except Exception as e:
            print(f"❌ Error generating answer: {e}")
            return "Sorry, I couldn't generate an answer."
    
    def query(self, question: str) -> str:
        """Complete RAG query"""
        print(f"\n❓ Question: {question}")
        
        # Search for relevant documents
        relevant_docs = self.search(question)
        
        if not relevant_docs:
            return "I couldn't find relevant information to answer your question."
        
        # Generate answer
        answer = self.generate_answer(question, relevant_docs)
        
        print(f"💬 Answer: {answer}")
        print(f"📚 Based on {len(relevant_docs)} sources")
        
        return answer

def main():
    """Main function"""
    print("🚀 Starting Simple RAG System...")
    
    # Initialize RAG system
    rag = SimpleRAGSystem()
    
    # Create collection
    rag.create_collection()
    
    # Sample documents
    documents = [
        "BMasterAI is an advanced multi-agent AI framework for Python that provides comprehensive logging, monitoring, and integrations.",
        "Qdrant is a vector database that enables similarity search and recommendations using high-performance vector operations.",
        "RAG (Retrieval-Augmented Generation) combines information retrieval with language generation to provide accurate responses.",
        "Vector embeddings are numerical representations of text that capture semantic meaning for similarity search.",
        "Machine learning is a subset of artificial intelligence that enables computers to learn from data without explicit programming.",
        "Natural language processing (NLP) is a field of AI that focuses on the interaction between computers and human language."
    ]
    
    # Add documents to knowledge base
    print("\n📚 Adding documents to knowledge base...")
    rag.add_documents(documents)
    
    # Example queries
    queries = [
        "What is BMasterAI?",
        "How does RAG work?",
        "What are vector embeddings?",
        "Tell me about machine learning"
    ]
    
    # Process queries
    print("\n🤖 Processing queries...")
    for query in queries:
        rag.query(query)
        print("-" * 50)
    
    # Show performance metrics
    print("\n📊 Performance Metrics:")
    dashboard = rag.monitor.get_agent_dashboard("simple-rag")
    if dashboard.get('performance'):
        for task, metrics in dashboard['performance'].items():
            print(f"  {task}: {metrics['avg_duration_ms']:.2f}ms avg")
    
    print("\n✅ RAG system demo completed!")

if __name__ == "__main__":
    main()
```

### Step 6: Run Your RAG System

```bash
python basic_rag.py
```

Expected output:
```
🚀 Starting Simple RAG System...
✅ Collection 'simple_rag_demo' created
📚 Adding documents to knowledge base...
✅ Added 6 documents in 1247ms

🤖 Processing queries...

❓ Question: What is BMasterAI?
🔍 Found 1 relevant documents
💬 Answer: BMasterAI is an advanced multi-agent AI framework for Python that provides comprehensive logging, monitoring, and integrations for building production-ready AI systems.
📚 Based on 1 sources
```

## Tutorial 2: Web Interface

### Step 1: Install Gradio

```bash
pip install gradio
```

### Step 2: Create Web Interface

Create `rag_web_interface.py`:

```python
#!/usr/bin/env python3
"""Simple RAG Web Interface with Gradio"""

import gradio as gr
from basic_rag import SimpleRAGSystem

class RAGWebInterface:
    def __init__(self):
        self.rag_system = SimpleRAGSystem()
        self.rag_system.create_collection()
        
        # Add some default documents
        default_docs = [
            "BMasterAI is an advanced multi-agent AI framework for Python.",
            "Qdrant is a vector database for similarity search.",
            "RAG combines retrieval with generation for better AI responses.",
            "Vector embeddings represent text as numerical vectors.",
        ]
        self.rag_system.add_documents(default_docs)
    
    def chat_interface(self, message, history):
        """Chat interface for Gradio"""
        if not message.strip():
            return history, ""
        
        # Get answer from RAG system
        answer = self.rag_system.query(message)
        
        # Add to history
        history.append([message, answer])
        
        return history, ""
    
    def add_document(self, document_text):
        """Add new document to knowledge base"""
        if not document_text.strip():
            return "Please enter document text"
        
        try:
            self.rag_system.add_documents([document_text])
            return f"✅ Document added successfully!"
        except Exception as e:
            return f"❌ Error adding document: {e}"
    
    def create_interface(self):
        """Create Gradio interface"""
        with gr.Blocks(title="Simple RAG System") as demo:
            gr.HTML("<h1>🧠 Simple RAG System</h1>")
            gr.HTML("<p>Ask questions and get answers from your knowledge base!</p>")
            
            with gr.Tab("💬 Chat"):
                chatbot = gr.Chatbot(height=400)
                msg = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask me anything...",
                    lines=2
                )
                
                with gr.Row():
                    submit_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear")
                
                # Event handlers
                submit_btn.click(
                    self.chat_interface,
                    inputs=[msg, chatbot],
                    outputs=[chatbot, msg]
                )
                
                msg.submit(
                    self.chat_interface,
                    inputs=[msg, chatbot],
                    outputs=[chatbot, msg]
                )
                
                clear_btn.click(
                    lambda: ([], ""),
                    outputs=[chatbot, msg]
                )
            
            with gr.Tab("📚 Add Documents"):
                doc_input = gr.Textbox(
                    label="Document Text",
                    placeholder="Enter your document content here...",
                    lines=5
                )
                add_btn = gr.Button("Add Document", variant="primary")
                result = gr.Textbox(label="Result", interactive=False)
                
                add_btn.click(
                    self.add_document,
                    inputs=[doc_input],
                    outputs=[result]
                )
        
        return demo

def main():
    """Launch web interface"""
    print("🌐 Starting RAG Web Interface...")
    
    interface = RAGWebInterface()
    demo = interface.create_interface()
    
    print("🚀 Launching web interface at http://localhost:7860")
    demo.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    main()
```

### Step 3: Launch Web Interface

```bash
python rag_web_interface.py
```

Open your browser to `http://localhost:7860` to access the interface!

## Tutorial 3: Advanced Features

### Step 1: Custom Configuration

Create `advanced_rag.py` with custom settings:

```python
#!/usr/bin/env python3
"""Advanced RAG system with custom configuration"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any
from basic_rag import SimpleRAGSystem

@dataclass
class RAGConfig:
    """Advanced RAG configuration"""
    # Vector database settings
    collection_name: str = "advanced_rag"
    vector_size: int = 384
    similarity_threshold: float = 0.7
    
    # LLM settings
    llm_model: str = "gpt-3.5-turbo"
    max_tokens: int = 500
    temperature: float = 0.7
    
    # Retrieval settings
    top_k_results: int = 5
    
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"

class AdvancedRAGSystem(SimpleRAGSystem):
    def __init__(self, config: RAGConfig):
        self.config = config
        super().__init__()
        self.collection_name = config.collection_name
    
    def search(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """Enhanced search with configurable parameters"""
        if limit is None:
            limit = self.config.top_k_results
        
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=self.config.similarity_threshold
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "text": result.payload["text"],
                    "score": result.score,
                    "id": result.id,
                    "metadata": result.payload.get("metadata", {})
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def generate_answer(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Enhanced answer generation with custom prompt"""
        try:
            # Enhanced context with scores
            context_parts = []
            for i, doc in enumerate(context_docs):
                context_parts.append(
                    f"Source {i+1} (Relevance: {doc['score']:.3f}):\n{doc['text']}"
                )
            context = "\n\n".join(context_parts)
            
            # Enhanced prompt
            prompt = f"""You are an AI assistant that answers questions based on provided context.

Context Sources:
{context}

Question: {query}

Instructions:
- Provide a comprehensive answer based on the context
- If the context doesn't contain enough information, say so
- Cite which sources you used in your answer
- Be accurate and helpful

Answer:"""
            
            response = openai.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful and accurate AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating answer: {e}"

def main():
    """Advanced RAG demo"""
    print("🚀 Starting Advanced RAG System...")
    
    # Custom configuration
    config = RAGConfig(
        collection_name="advanced_demo",
        similarity_threshold=0.6,
        top_k_results=3,
        max_tokens=300,
        temperature=0.5
    )
    
    # Initialize system
    rag = AdvancedRAGSystem(config)
    rag.create_collection()
    
    # Enhanced documents with metadata
    documents = [
        "BMasterAI is a comprehensive Python framework for building multi-agent AI systems with enterprise-grade logging and monitoring.",
        "Qdrant Cloud provides managed vector database services with high-performance similarity search capabilities.",
        "RAG (Retrieval-Augmented Generation) enhances language models by incorporating relevant information from external knowledge bases.",
        "Vector embeddings transform text into numerical representations that capture semantic meaning for similarity comparisons.",
        "Machine learning algorithms enable computers to learn patterns from data and make predictions without explicit programming.",
        "Natural language processing combines computational linguistics with machine learning to help computers understand human language."
    ]
    
    rag.add_documents(documents)
    
    # Test queries
    queries = [
        "What makes BMasterAI different from other AI frameworks?",
        "How does vector similarity search work in Qdrant?",
        "Explain the benefits of using RAG for AI applications"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        answer = rag.query(query)
        print(f"{'='*60}")

if __name__ == "__main__":
    main()
```

### Step 2: Run Advanced System

```bash
python advanced_rag.py
```

## Tutorial 4: Production Deployment

### Step 1: Environment Configuration

Create `production_config.yaml`:

```yaml
# Production RAG Configuration
rag:
  collection_name: "production_knowledge_base"
  similarity_threshold: 0.75
  top_k_results: 5
  max_tokens: 800
  temperature: 0.3

logging:
  level: INFO
  enable_file: true
  enable_json: true
  log_file: "rag_system.log"

monitoring:
  collection_interval: 30
  enable_alerts: true

alerts:
  - metric: "query_latency"
    threshold: 5000  # 5 seconds
    condition: "greater_than"
  - metric: "error_rate"
    threshold: 0.05  # 5%
    condition: "greater_than"

integrations:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
```

### Step 2: Production RAG System

Create `production_rag.py`:

```python
#!/usr/bin/env python3
"""Production-ready RAG system"""

import os
import yaml
import logging
from typing import Dict, Any
from advanced_rag import AdvancedRAGSystem, RAGConfig
from bmasterai.logging import configure_logging, LogLevel
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager

class ProductionRAGSystem:
    def __init__(self, config_file: str = "production_config.yaml"):
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Configure logging
        configure_logging(
            log_level=LogLevel[self.config['logging']['level']],
            enable_file=self.config['logging']['enable_file'],
            enable_json=self.config['logging']['enable_json'],
            log_file=self.config['logging']['log_file']
        )
        
        # Setup monitoring
        self.monitor = get_monitor()
        self.monitor.start_monitoring()
        
        # Setup integrations
        self.integration_manager = get_integration_manager()
        self._setup_integrations()
        
        # Setup alerts
        self._setup_alerts()
        
        # Initialize RAG system
        rag_config = RAGConfig(
            collection_name=self.config['rag']['collection_name'],
            similarity_threshold=self.config['rag']['similarity_threshold'],
            top_k_results=self.config['rag']['top_k_results'],
            max_tokens=self.config['rag']['max_tokens'],
            temperature=self.config['rag']['temperature']
        )
        
        self.rag_system = AdvancedRAGSystem(rag_config)
        self.rag_system.create_collection()
    
    def _setup_integrations(self):
        """Setup production integrations"""
        if self.config.get('integrations', {}).get('slack', {}).get('enabled'):
            from bmasterai.integrations import SlackConnector
            slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
            if slack_webhook:
                slack = SlackConnector(webhook_url=slack_webhook)
                self.integration_manager.add_connector("slack", slack)
    
    def _setup_alerts(self):
        """Setup production alerts"""
        for alert_config in self.config.get('alerts', []):
            self.monitor.metrics_collector.add_alert_rule(
                metric_name=alert_config['metric'],
                threshold=alert_config['threshold'],
                condition=alert_config['condition'],
                callback=self._alert_callback
            )
    
    def _alert_callback(self, alert_data):
        """Handle alert notifications"""
        message = f"🚨 RAG System Alert: {alert_data['message']}"
        self.integration_manager.send_alert_to_all(alert_data)
        logging.warning(message)
    
    def query(self, question: str) -> Dict[str, Any]:
        """Production query with comprehensive monitoring"""
        import time
        start_time = time.time()
        
        try:
            # Process query
            answer = self.rag_system.query(question)
            
            # Track metrics
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.metrics_collector.record_custom_metric(
                "query_latency", duration_ms, {"status": "success"}
            )
            
            return {
                "answer": answer,
                "status": "success",
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            # Track error
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.metrics_collector.record_custom_metric(
                "query_latency", duration_ms, {"status": "error"}
            )
            self.monitor.track_error("production-rag", "query_processing")
            
            logging.error(f"Query processing error: {e}")
            
            return {
                "answer": "I'm sorry, I encountered an error processing your question.",
                "status": "error",
                "error": str(e),
                "duration_ms": duration_ms
            }
    
    def health_check(self) -> Dict[str, Any]:
        """System health check"""
        try:
            # Test Qdrant connection
            collections = self.rag_system.qdrant_client.get_collections()
            qdrant_status = "healthy"
        except Exception as e:
            qdrant_status = f"error: {e}"
        
        # Get system metrics
        health = self.monitor.get_system_health()
        
        return {
            "status": "healthy" if qdrant_status == "healthy" else "degraded",
            "qdrant": qdrant_status,
            "system_metrics": health['system_metrics'],
            "active_agents": health['active_agents'],
            "timestamp": health['timestamp']
        }

def main():
    """Production RAG system demo"""
    print("🏭 Starting Production RAG System...")
    
    try:
        # Initialize production system
        prod_rag = ProductionRAGSystem()
        
        # Health check
        health = prod_rag.health_check()
        print(f"System Status: {health['status']}")
        
        # Sample queries
        queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "Explain neural networks"
        ]
        
        for query in queries:
            print(f"\n🔍 Query: {query}")
            result = prod_rag.query(query)
            print(f"Status: {result['status']}")
            print(f"Duration: {result['duration_ms']:.2f}ms")
            if result['status'] == 'success':
                print(f"Answer: {result['answer'][:200]}...")
        
        print("\n✅ Production RAG system demo completed!")
        
    except Exception as e:
        print(f"❌ Production system error: {e}")

if __name__ == "__main__":
    main()
```

### Step 3: Deploy with Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 7860

# Run application
CMD ["python", "production_rag.py"]
```

Create `requirements.txt`:

```txt
bmasterai>=0.2.0
qdrant-client>=1.7.0
openai>=1.0.0
sentence-transformers>=2.2.0
numpy>=1.24.0
gradio>=4.0.0
pyyaml>=6.0
```

Build and run:

```bash
# Build Docker image
docker build -t my-rag-system .

# Run container
docker run -p 7860:7860 \
  -e QDRANT_URL="https://your-cluster.qdrant.io" \
  -e QDRANT_API_KEY="your-api-key" \
  -e OPENAI_API_KEY="your-openai-key" \
  my-rag-system
```

## 🎯 Next Steps

### Advanced Topics
- **[Performance Optimization](../advanced/performance.md)** - Optimize for production
- **[Security Best Practices](../advanced/security.md)** - Secure your RAG system
- **[Monitoring & Alerting](../monitoring/alerts.md)** - Advanced monitoring

### Integration Examples
- **[Slack Integration](../integrations/slack.md)** - Get notifications in Slack
- **[Custom Integrations](../integrations/custom.md)** - Build custom connectors

### Web Interfaces
- **[Advanced Gradio UI](../web/gradio.md)** - Build sophisticated interfaces
- **[Dashboard Creation](../web/dashboards.md)** - Create monitoring dashboards

## 🆘 Troubleshooting

### Common Issues

1. **Connection Errors**: Check API keys and network connectivity
2. **Memory Issues**: Reduce batch sizes or use smaller embedding models
3. **Performance Issues**: Optimize similarity thresholds and result limits
4. **Integration Failures**: Verify webhook URLs and credentials

### Getting Help

- **[GitHub Issues](https://github.com/travis-burmaster/bmasterai/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/travis-burmaster/bmasterai/discussions)** - Ask questions
- **Email**: travis@burmaster.com

---

*Ready to build production-ready RAG systems? Start with Tutorial 1! 🚀*