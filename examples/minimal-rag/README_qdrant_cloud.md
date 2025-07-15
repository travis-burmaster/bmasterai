# BMasterAI Qdrant Cloud RAG Example

This example demonstrates how to build an advanced RAG (Retrieval-Augmented Generation) system using BMasterAI framework with Qdrant Cloud vector database.

## 🌟 Features

- **Qdrant Cloud Integration**: Connect to Qdrant's managed cloud service
- **Advanced RAG Pipeline**: Document ingestion, vector search, and answer generation
- **BMasterAI Monitoring**: Full logging, monitoring, and performance tracking
- **Production Ready**: Error handling, retries, and comprehensive metrics
- **Flexible Configuration**: Environment-based configuration for different deployments

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Qdrant Cloud account and API key
- OpenAI API key

### 2. Installation

```bash
# Install dependencies
pip install -r requirements_qdrant.txt

# Or install individually
pip install bmasterai qdrant-client openai sentence-transformers numpy
```

### 3. Setup Qdrant Cloud

1. **Create Account**: Sign up at [https://cloud.qdrant.io/](https://cloud.qdrant.io/)
2. **Create Cluster**: Set up a new cluster in your preferred region
3. **Get API Key**: Generate an API key from the dashboard
4. **Get Cluster URL**: Copy your cluster URL (e.g., `https://xyz-example.qdrant.io`)

### 4. Configuration

Set up environment variables:

```bash
# Qdrant Cloud configuration
export QDRANT_URL="https://your-cluster.qdrant.io"
export QDRANT_API_KEY="your-qdrant-api-key"

# OpenAI configuration
export OPENAI_API_KEY="your-openai-api-key"
```

Or create a `.env` file:

```env
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
OPENAI_API_KEY=your-openai-api-key
```

### 5. Run the Example

```bash
python bmasterai_rag_qdrant_cloud.py
```

## 📋 Example Output

```
🚀 Initializing BMasterAI Qdrant RAG system...
📦 Creating Qdrant collection...
📚 Adding sample documents...
ℹ️ Collection information:
{
  "name": 384,
  "vector_size": 384,
  "distance": "Cosine",
  "points_count": 4,
  "status": "green"
}

🤖 Running example queries...

❓ Query: What is BMasterAI?
💬 Answer: BMasterAI is an advanced multi-agent AI framework for Python that provides comprehensive logging, monitoring, and integrations for building production-ready AI systems.
📊 Sources found: 1
⏱️ Processing time: 1247.32ms
📄 Top source:
   Score: 0.892
   Text: BMasterAI is an advanced multi-agent AI framework for Python that provides comprehensive...

❓ Query: How does RAG work?
💬 Answer: RAG (Retrieval-Augmented Generation) combines information retrieval with language generation to provide more accurate and contextual responses by grounding answers in retrieved documents.
📊 Sources found: 2
⏱️ Processing time: 1156.78ms
```

## 🏗️ Architecture

The RAG system consists of several key components:

### 1. Document Processing

- **Text Chunking**: Splits documents into manageable chunks
- **Embedding Generation**: Uses SentenceTransformers for vector embeddings
- **Metadata Handling**: Preserves document metadata and source information

### 2. Vector Storage (Qdrant Cloud)

- **Collection Management**: Automatic collection creation and configuration
- **Vector Indexing**: Efficient similarity search with cosine distance
- **Payload Storage**: Stores original text and metadata alongside vectors

### 3. Retrieval System

- **Semantic Search**: Finds most relevant documents using vector similarity
- **Filtering**: Supports metadata-based filtering
- **Ranking**: Returns results sorted by relevance score

### 4. Generation Pipeline

- **Context Assembly**: Combines retrieved documents into coherent context
- **Prompt Engineering**: Optimized prompts for accurate answer generation
- **Response Processing**: Handles OpenAI API responses and errors

### 5. BMasterAI Integration

- **Comprehensive Logging**: All operations logged with structured data
- **Performance Monitoring**: Tracks latency, token usage, and success rates
- **Error Handling**: Robust error handling with detailed error tracking
- **Metrics Collection**: Custom metrics for RAG-specific operations

## 🔧 Configuration Options

### Qdrant Configuration

```python
qdrant_config = QdrantConfig(
    url="https://your-cluster.qdrant.io",
    api_key="your-api-key",
    collection_name="knowledge_base",
    vector_size=384,  # Embedding dimension
    distance=Distance.COSINE,  # Similarity metric
    timeout=30  # Request timeout
)
```

### RAG Configuration

```python
rag_config = RAGConfig(
    openai_api_key="your-openai-key",
    embedding_model="all-MiniLM-L6-v2",  # SentenceTransformer model
    llm_model="gpt-3.5-turbo",  # OpenAI model
    max_tokens=1000,  # Max response length
    temperature=0.7,  # Response creativity
    top_k_results=5,  # Number of documents to retrieve
    similarity_threshold=0.7  # Minimum similarity score
)
```

## 📊 Monitoring and Metrics

The system provides comprehensive monitoring through BMasterAI:

### Key Metrics Tracked

- **Document Ingestion**: Processing time, success/failure rates
- **Vector Search**: Query latency, result counts, similarity scores
- **LLM Calls**: Token usage, response time, model performance
- **End-to-End RAG**: Complete pipeline performance

### Available Dashboards

```python
# Get agent-specific dashboard
dashboard = monitor.get_agent_dashboard("qdrant-rag-agent")

# Get system health
health = monitor.get_system_health()
```

### Log Events

All operations generate structured log events:

- `AGENT_START`: System initialization
- `TASK_START/COMPLETE`: Operation tracking
- `LLM_CALL`: Language model interactions
- `AGENT_COMMUNICATION`: External service calls
- `TASK_ERROR`: Error conditions

## 🔍 Advanced Usage

### Custom Document Processing

```python
# Add documents with custom metadata
documents = [
    {
        "text": "Your document content here...",
        "metadata": {
            "category": "technical",
            "author": "John Doe",
            "date": "2024-01-15",
            "tags": ["ai", "rag", "vector-db"]
        },
        "source": "internal_docs"
    }
]

rag_system.add_documents(documents)
```

### Advanced Search with Filtering

```python
# Search with metadata filtering (requires custom implementation)
results = rag_system.search_similar(
    query="machine learning concepts",
    limit=10,
    # filter_conditions={"category": "technical"}  # Custom filtering
)
```

### Batch Processing

```python
# Process multiple queries efficiently
queries = [
    "What is machine learning?",
    "How does deep learning work?",
    "What are neural networks?"
]

results = []
for query in queries:
    result = rag_system.query(query)
    results.append(result)
```

## 🚨 Error Handling

The system includes comprehensive error handling:

- **Connection Errors**: Automatic retry with exponential backoff
- **API Rate Limits**: Graceful handling of rate limit responses
- **Invalid Queries**: Validation and sanitization of user input
- **Resource Limits**: Memory and timeout management

## 🔒 Security Best Practices

- **API Key Management**: Use environment variables, never hardcode keys
- **Input Validation**: Sanitize all user inputs
- **Access Control**: Implement proper authentication for production use
- **Data Privacy**: Consider data residency and privacy requirements

## 📈 Performance Optimization

### Tips for Better Performance

1. **Batch Operations**: Process documents in batches for better throughput
2. **Embedding Caching**: Cache embeddings for frequently accessed documents
3. **Index Optimization**: Use appropriate vector index settings in Qdrant
4. **Connection Pooling**: Reuse connections for better performance

### Scaling Considerations

- **Horizontal Scaling**: Use multiple Qdrant clusters for large datasets
- **Load Balancing**: Distribute queries across multiple instances
- **Caching Layer**: Implement Redis or similar for frequently accessed results
- **Async Processing**: Use async/await for better concurrency

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest test_qdrant_rag.py -v
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📚 Additional Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [BMasterAI Framework](https://github.com/travis-burmaster/bmasterai)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [SentenceTransformers](https://www.sbert.net/)

## 🆘 Troubleshooting

### Common Issues

**Connection to Qdrant fails:**

- Verify your cluster URL and API key
- Check network connectivity
- Ensure cluster is running

**OpenAI API errors:**

- Verify API key is valid
- Check rate limits and quotas
- Ensure sufficient credits

**Embedding model download fails:**

- Check internet connection
- Verify disk space
- Try different model if needed

**Performance issues:**

- Reduce batch sizes
- Optimize vector dimensions
- Check system resources

### Getting Help

- Check the logs for detailed error messages
- Review the BMasterAI monitoring dashboard
- Open an issue on GitHub with full error details

## 📄 License

This example is part of the BMasterAI framework and is licensed under the MIT License.
