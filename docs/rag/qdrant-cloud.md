# Qdrant Cloud Integration

This guide covers setting up and using Qdrant Cloud as your vector database for BMasterAI RAG systems.

## 🌐 What is Qdrant Cloud?

Qdrant Cloud is a managed vector database service that provides:
- **High-performance vector search** with sub-millisecond latency
- **Scalable infrastructure** that grows with your needs
- **Enterprise security** with encryption and access controls
- **Global availability** with multiple regions
- **Easy management** through web console and APIs

## 🚀 Getting Started with Qdrant Cloud

### 1. Create Your Account

1. Visit [https://cloud.qdrant.io/](https://cloud.qdrant.io/)
2. Sign up for a free account
3. Verify your email address

### 2. Create a Cluster

1. **Choose Region**: Select the region closest to your users
2. **Select Plan**: Start with the free tier for development
3. **Configure Cluster**: Set cluster name and basic settings
4. **Deploy**: Wait for cluster provisioning (usually 2-3 minutes)

### 3. Get Your Credentials

Once your cluster is ready:

1. **Cluster URL**: Copy your cluster URL (e.g., `https://xyz-example.qdrant.io`)
2. **API Key**: Generate an API key from the dashboard
3. **Save Credentials**: Store them securely

## 🔧 BMasterAI Integration

### Environment Setup

Set up your environment variables:

```bash
# Qdrant Cloud configuration
export QDRANT_URL="https://your-cluster.qdrant.io"
export QDRANT_API_KEY="your-qdrant-api-key"

# OpenAI configuration (for embeddings and LLM)
export OPENAI_API_KEY="your-openai-api-key"
```

Or create a `.env` file:

```env
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
OPENAI_API_KEY=your-openai-api-key
```

### Basic Configuration

```python
from examples.minimal_rag.bmasterai_rag_qdrant_cloud import QdrantConfig, RAGConfig

# Qdrant Cloud configuration
qdrant_config = QdrantConfig(
    url="https://your-cluster.qdrant.io",
    api_key="your-qdrant-api-key",
    collection_name="bmasterai_knowledge",
    vector_size=384,  # Matches embedding model dimensions
    distance=Distance.COSINE,  # Similarity metric
    timeout=30  # Request timeout in seconds
)

# RAG system configuration
rag_config = RAGConfig(
    openai_api_key="your-openai-api-key",
    embedding_model="all-MiniLM-L6-v2",  # SentenceTransformers model
    llm_model="gpt-3.5-turbo",  # OpenAI model
    max_tokens=1000,
    temperature=0.7,
    top_k_results=5,
    similarity_threshold=0.7
)
```

## 🧪 Testing Your Connection

Use the provided test script to verify your setup:

```bash
# Test all connections
python examples/minimal-rag/test_qdrant_connection.py
```

Expected output:
```
🧪 BMasterAI Qdrant Cloud RAG - Connection Tests
==================================================

1. Testing Qdrant Cloud connection...
   ✅ Successfully connected to Qdrant Cloud!
   URL: https://your-cluster.qdrant.io
   Collections: 0

2. Testing OpenAI API connection...
   ✅ Successfully connected to OpenAI API!
   Model: gpt-3.5-turbo
   Test tokens used: 15

3. Testing embedding model...
   ✅ Embedding model loaded successfully!
   Model: all-MiniLM-L6-v2
   Embedding size: 384

==================================================
🎉 All tests passed! You're ready to run the RAG example.
```

## 📊 Collection Management

### Creating Collections

Collections are automatically created when you first add documents:

```python
from examples.minimal_rag.bmasterai_rag_qdrant_cloud import BMasterAIQdrantRAG

# Initialize RAG system
rag_system = BMasterAIQdrantRAG(qdrant_config, rag_config)

# Create collection (automatic)
rag_system.create_collection()
```

### Collection Configuration

```python
# Advanced collection configuration
qdrant_config = QdrantConfig(
    url="https://your-cluster.qdrant.io",
    api_key="your-qdrant-api-key",
    collection_name="my_knowledge_base",
    vector_size=384,  # Must match your embedding model
    distance=Distance.COSINE,  # Options: COSINE, DOT, EUCLID
    timeout=30
)
```

### Collection Information

```python
# Get collection details
info = rag_system.get_collection_info()
print(f"Collection: {info['name']}")
print(f"Documents: {info['points_count']}")
print(f"Vector size: {info['vector_size']}")
print(f"Status: {info['status']}")
```

## 📚 Document Management

### Adding Documents

```python
# Single document
documents = [
    {
        "text": "BMasterAI is an advanced multi-agent AI framework...",
        "metadata": {
            "category": "framework",
            "topic": "bmasterai",
            "author": "documentation_team",
            "date": "2025-01-15"
        },
        "source": "documentation"
    }
]

# Add to Qdrant
result = rag_system.add_documents(documents)
print(result)  # ✅ Successfully added 1 documents in 1247ms
```

### Batch Document Processing

```python
# Process large document sets
import json

# Load documents from file
with open('knowledge_base.json', 'r') as f:
    documents = json.load(f)

# Add in batches for better performance
batch_size = 100
for i in range(0, len(documents), batch_size):
    batch = documents[i:i + batch_size]
    result = rag_system.add_documents(batch)
    print(f"Batch {i//batch_size + 1}: {result}")
```

### Document Metadata

Enhance your documents with rich metadata:

```python
document = {
    "text": "Your document content here...",
    "metadata": {
        "title": "Document Title",
        "author": "John Doe",
        "department": "Engineering",
        "tags": ["ai", "machine-learning", "rag"],
        "created_date": "2025-01-15",
        "document_type": "technical_spec",
        "version": "1.0",
        "language": "en",
        "classification": "internal"
    },
    "source": "internal_docs"
}
```

## 🔍 Search and Retrieval

### Basic Search

```python
# Simple similarity search
results = rag_system.search_similar("What is machine learning?", limit=5)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Text: {result['text'][:100]}...")
    print(f"Source: {result['source']}")
    print("---")
```

### Advanced Search Configuration

```python
# Configure search parameters
rag_config.top_k_results = 10  # Return top 10 results
rag_config.similarity_threshold = 0.8  # Higher threshold for better quality

# Search with custom parameters
results = rag_system.search_similar(
    query="artificial intelligence applications",
    limit=10
)
```

### Search Result Analysis

```python
# Analyze search results
results = rag_system.search_similar("deep learning")

if results:
    scores = [r['score'] for r in results]
    print(f"Results found: {len(results)}")
    print(f"Average score: {sum(scores) / len(scores):.3f}")
    print(f"Best score: {max(scores):.3f}")
    print(f"Worst score: {min(scores):.3f}")
else:
    print("No results found")
```

## 🤖 RAG Query Processing

### Complete RAG Pipeline

```python
# Full RAG query with retrieval and generation
result = rag_system.query("How does machine learning work?")

print(f"Answer: {result['answer']}")
print(f"Sources used: {result['metadata']['documents_found']}")
print(f"Processing time: {result['metadata']['processing_time_ms']:.2f}ms")
print(f"Average similarity: {result['metadata']['avg_similarity_score']:.3f}")

# Access source documents
for i, source in enumerate(result['sources']):
    print(f"\nSource {i+1}:")
    print(f"  Score: {source['score']:.3f}")
    print(f"  Text: {source['text'][:200]}...")
    print(f"  Metadata: {source['metadata']}")
```

### Custom Prompt Engineering

```python
# The RAG system uses optimized prompts, but you can customize:
# (This would require extending the base class)

class CustomRAGSystem(BMasterAIQdrantRAG):
    def generate_answer(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        # Custom prompt template
        context_text = "\n\n".join([doc['text'] for doc in context_docs])
        
        custom_prompt = f"""
        You are an expert AI assistant. Based on the provided context, 
        answer the question with high accuracy and detail.
        
        Context:
        {context_text}
        
        Question: {query}
        
        Instructions:
        - Provide a comprehensive answer
        - Cite specific information from the context
        - If uncertain, acknowledge limitations
        - Use clear, professional language
        
        Answer:
        """
        
        # Use the custom prompt with OpenAI
        # ... (implementation details)
```

## 📈 Performance Optimization

### Vector Configuration

```python
# Optimize for your use case
qdrant_config = QdrantConfig(
    vector_size=384,  # Smaller = faster, larger = more accurate
    distance=Distance.COSINE,  # COSINE for semantic similarity
    timeout=60  # Increase for large queries
)
```

### Embedding Model Selection

```python
# Different models for different needs
embedding_models = {
    "fast": "all-MiniLM-L6-v2",  # 384 dimensions, fast
    "balanced": "all-mpnet-base-v2",  # 768 dimensions, good quality
    "accurate": "all-MiniLM-L12-v2",  # 384 dimensions, high quality
}

rag_config = RAGConfig(
    embedding_model=embedding_models["balanced"]
)
```

### Batch Processing

```python
# Process documents in batches for better performance
def add_documents_batch(rag_system, documents, batch_size=50):
    results = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        result = rag_system.add_documents(batch)
        results.append(result)
        print(f"Processed batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
    return results
```

## 🔒 Security Best Practices

### API Key Management

```python
import os
from pathlib import Path

# Use environment variables
qdrant_api_key = os.getenv("QDRANT_API_KEY")
if not qdrant_api_key:
    raise ValueError("QDRANT_API_KEY environment variable not set")

# Or load from secure file
def load_api_key():
    key_file = Path.home() / ".config" / "bmasterai" / "qdrant_key"
    if key_file.exists():
        return key_file.read_text().strip()
    raise FileNotFoundError("API key file not found")
```

### Data Privacy

```python
# Sanitize sensitive data before adding to vector database
def sanitize_document(doc_text):
    import re
    
    # Remove email addresses
    doc_text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', doc_text)
    
    # Remove phone numbers
    doc_text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', doc_text)
    
    # Remove SSNs
    doc_text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', doc_text)
    
    return doc_text

# Apply sanitization
documents = [
    {
        "text": sanitize_document(original_text),
        "metadata": metadata,
        "source": source
    }
    for original_text, metadata, source in raw_documents
]
```

## 📊 Monitoring and Analytics

### BMasterAI Integration

The RAG system automatically provides comprehensive monitoring:

```python
# Get performance metrics
dashboard = monitor.get_agent_dashboard("qdrant-rag-agent")

print("Performance Metrics:")
for task_name, metrics in dashboard.get('performance', {}).items():
    print(f"  {task_name}:")
    print(f"    Average: {metrics['avg_duration_ms']:.2f}ms")
    print(f"    Total calls: {metrics['total_calls']}")

# Get system health
health = monitor.get_system_health()
print(f"Active agents: {health['active_agents']}")
print(f"System CPU: {health['system_metrics']['cpu']['avg']:.1f}%")
```

### Custom Metrics

```python
# Track custom business metrics
def track_query_quality(rag_system, query, result):
    # Track answer length
    answer_length = len(result['answer'])
    rag_system.monitor.metrics_collector.record_custom_metric(
        "answer_length", answer_length, {"query_type": "general"}
    )
    
    # Track source count
    source_count = len(result['sources'])
    rag_system.monitor.metrics_collector.record_custom_metric(
        "sources_used", source_count, {"query_type": "general"}
    )
    
    # Track similarity scores
    if result['sources']:
        avg_score = sum(s['score'] for s in result['sources']) / len(result['sources'])
        rag_system.monitor.metrics_collector.record_custom_metric(
            "avg_similarity_score", avg_score, {"query_type": "general"}
        )
```

## 🚨 Troubleshooting

### Common Issues

#### Connection Errors
```python
# Test connection with detailed error handling
try:
    collections = qdrant_client.get_collections()
    print("✅ Connection successful")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("Check:")
    print("  - Cluster URL is correct")
    print("  - API key is valid")
    print("  - Cluster is running")
    print("  - Network connectivity")
```

#### Performance Issues
```python
# Monitor query performance
import time

def benchmark_query(rag_system, query, iterations=5):
    times = []
    for i in range(iterations):
        start = time.time()
        result = rag_system.query(query)
        duration = time.time() - start
        times.append(duration)
        print(f"Query {i+1}: {duration:.2f}s")
    
    avg_time = sum(times) / len(times)
    print(f"Average query time: {avg_time:.2f}s")
    return avg_time
```

#### Memory Issues
```python
# Monitor memory usage during document processing
import psutil
import os

def monitor_memory_usage():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")
    return memory_mb

# Use during batch processing
for i, batch in enumerate(document_batches):
    rag_system.add_documents(batch)
    memory_mb = monitor_memory_usage()
    if memory_mb > 1000:  # 1GB threshold
        print("⚠️ High memory usage detected")
```

## 🎯 Next Steps

### Advanced Features
- **[RAG Web Interface](gradio-ui.md)** - Interactive web interface
- **[Custom Integrations](../integrations/custom.md)** - Build custom connectors
- **[Performance Optimization](../advanced/performance.md)** - Production optimization

### Production Deployment
- **[Security Best Practices](../advanced/security.md)** - Secure your deployment
- **[Production Deployment](../advanced/deployment.md)** - Deploy to production
- **[Monitoring & Alerting](../monitoring/alerts.md)** - Set up alerts

---

*Ready to build powerful RAG systems with Qdrant Cloud? Let's go! 🚀*