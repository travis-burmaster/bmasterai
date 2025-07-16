# Enhanced BMasterAI RAG System

A production-ready **Retrieval-Augmented Generation (RAG)** system built with the BMasterAI framework, featuring **async processing**, **intelligent caching**, and **real-time performance monitoring**.

## 🚀 Features

### Core Capabilities
- **Document Upload & Processing**: Support for PDF, DOCX, and TXT files
- **Semantic Search**: Advanced vector similarity search with Qdrant
- **Q&A Chat Interface**: Interactive document-based question answering
- **Real-time Monitoring**: Performance metrics and system health tracking

### Performance Enhancements
- **🔄 Async Processing**: Concurrent document processing for faster uploads
- **⚡ Intelligent Caching**: Persistent caching for embeddings and responses
- **🔗 Connection Pooling**: Optimized database connections
- **🔁 Retry Logic**: Automatic retry with exponential backoff
- **📊 Batch Operations**: Efficient bulk document processing

### Advanced Features
- **📈 Performance Analytics**: Real-time metrics and success rate tracking
- **🔍 Advanced Search**: Configurable similarity thresholds and result limits
- **💾 Export Functionality**: Data export in multiple formats
- **🧹 Cache Management**: Built-in cache clearing and optimization
- **📱 Modern UI**: Enhanced Gradio interface with multiple tabs

## 📋 Requirements

### System Requirements
- Python 3.8+
- 4GB+ RAM (8GB+ recommended for large documents)
- 1GB+ free disk space for caching
- Internet connection for Anthropic API

### External Services
- **Anthropic API**: Claude model access (required)
- **Qdrant Database**: Vector storage (local or cloud)
- **Slack** (optional): Notifications integration
- **SMTP Server** (optional): Email notifications

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai/examples/rag-qdrant
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Qdrant (Choose one option)

#### Option A: Local Qdrant with Docker
```bash
docker run -p 6333:6333 qdrant/qdrant
```

#### Option B: Qdrant Cloud
1. Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create a cluster and get your API key
3. Set `QDRANT_URL` and `QDRANT_API_KEY` environment variables

### 4. Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Required
ANTHROPIC_API_KEY=your-anthropic-api-key

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key  # Optional for local

# Model Configuration
MODEL_NAME=claude-3-5-sonnet-20241022
EMBEDDING_MODEL=all-MiniLM-L6-v2
COLLECTION_NAME=bmasterai_documents

# Performance Configuration
MAX_CONCURRENT_UPLOADS=5
MAX_FILE_SIZE=52428800  # 50MB in bytes
CACHE_DIR=/tmp/bmasterai_cache
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=5
SIMILARITY_THRESHOLD=0.7

# API Configuration
MAX_TOKENS=4096
TEMPERATURE=0.7

# Server Configuration
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
GRADIO_SHARE=false

# Logging Configuration
ENABLE_JSON_LOGS=false
ENABLE_FILE_LOGS=true

# Optional Integrations
SLACK_WEBHOOK_URL=your-slack-webhook-url
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 🚀 Quick Start

### 1. Start the Application
```bash
python bmasterai-gradio-rag.py
```

### 2. Access the Interface
Open your browser to `http://localhost:7860`

### 3. Upload Documents
- Navigate to the "Upload Documents" tab
- Upload PDF, DOCX, or TXT files
- Use batch upload for multiple files

### 4. Ask Questions
- Go to the "Chat with Documents" tab
- Ask questions about your uploaded documents
- Get responses with source citations

## 📖 Usage Guide

### Document Upload
- **Single Upload**: Upload one document at a time
- **Batch Upload**: Upload multiple documents simultaneously with async processing
- **Supported Formats**: PDF, DOCX, TXT (up to 50MB each)

### Chat Interface
- Ask natural language questions about your documents
- Get answers with source citations and relevance scores
- Use example questions for quick starts

### Advanced Search
- Configure similarity thresholds
- Adjust number of results
- Fine-tune search parameters

### Performance Monitoring
- View real-time system metrics
- Track upload and query performance
- Monitor cache hit rates and success rates

### Cache Management
- Clear caches to free up space
- Monitor cache performance
- Optimize system resources

## 🔧 Configuration

### Performance Tuning
- **MAX_CONCURRENT_UPLOADS**: Increase for faster batch processing (default: 5)
- **CHUNK_SIZE**: Adjust for document granularity (default: 1000)
- **CACHE_DIR**: Set to SSD location for better performance
- **TOP_K**: Increase for more comprehensive results (default: 5)

### Memory Optimization
- **MAX_FILE_SIZE**: Limit individual file sizes
- **SIMILARITY_THRESHOLD**: Filter low-relevance results
- **CHUNK_OVERLAP**: Balance context vs. memory usage

### API Optimization
- **MAX_TOKENS**: Adjust response length
- **TEMPERATURE**: Control response creativity
- **MODEL_NAME**: Choose appropriate Claude model

## 📊 Architecture

### Core Components
- **AsyncDocumentProcessor**: Concurrent document processing
- **CachedEmbeddingModel**: Persistent embedding caching
- **ImprovedVectorStore**: Connection pooling and batch operations
- **ImprovedAnthropicChat**: Retry logic and response caching
- **EnhancedBMasterAIRAGSystem**: Main system orchestration

### Data Flow
1. **Document Upload** → Text extraction → Chunking → Embedding → Vector storage
2. **Query Processing** → Embedding → Similarity search → Context preparation → LLM response
3. **Caching Layer** → Embedding cache → Response cache → Performance optimization

### Integration Points
- **BMasterAI Framework**: Logging, monitoring, and integration management
- **Qdrant Database**: Vector storage and similarity search
- **Anthropic API**: Language model for response generation
- **External Services**: Slack, email notifications

## 🔍 Troubleshooting

### Common Issues

#### Upload Failures
- **Solution**: Check file format, size limits, and disk space
- **Debug**: Check system status tab for detailed error messages

#### Slow Performance
- **Solution**: Clear cache, increase concurrent uploads, check system resources
- **Debug**: Monitor performance metrics in real-time

#### API Errors
- **Solution**: Verify API keys, check network connectivity, review rate limits
- **Debug**: Check logs for specific error messages

#### Memory Issues
- **Solution**: Reduce chunk size, clear cache, limit concurrent uploads
- **Debug**: Monitor system resources and adjust configuration

### Performance Optimization

#### For Large Document Sets
```bash
# Increase concurrent processing
export MAX_CONCURRENT_UPLOADS=10

# Optimize chunk size
export CHUNK_SIZE=800
export CHUNK_OVERLAP=100

# Use SSD for cache
export CACHE_DIR=/path/to/ssd/cache
```

#### For High Query Volume
```bash
# Increase cache size
export CACHE_DIR=/path/to/large/cache

# Optimize search parameters
export TOP_K=3
export SIMILARITY_THRESHOLD=0.8
```

## 📈 Monitoring & Analytics

### System Metrics
- Document upload success rates
- Query processing times
- Cache hit rates
- Error tracking and classification

### Performance Analytics
- Average processing times
- System resource utilization
- API usage statistics
- User interaction patterns

### Health Checks
- Database connectivity
- API availability
- Cache performance
- System resource status

## 🔐 Security Considerations

### Data Security
- Documents are processed locally before vectorization
- Sensitive data should be reviewed before upload
- API keys should be kept secure and rotated regularly

### Network Security
- Use HTTPS in production
- Implement proper authentication if exposed publicly
- Consider VPN for sensitive deployments

### File Security
- Validate file types and sizes
- Scan for malicious content if needed
- Implement access controls for uploaded documents

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 7860

CMD ["python", "bmasterai-gradio-rag.py"]
```

### Environment Variables for Production
```bash
# Production settings
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
ENABLE_JSON_LOGS=true
ENABLE_FILE_LOGS=true

# Security settings
MAX_FILE_SIZE=104857600  # 100MB
MAX_CONCURRENT_UPLOADS=3  # Conservative for production

# Performance settings
CACHE_DIR=/app/cache
CHUNK_SIZE=1000
TOP_K=5
```

### Scaling Considerations
- Use external Qdrant cluster for horizontal scaling
- Implement load balancing for multiple instances
- Consider Redis for shared caching
- Monitor resource usage and auto-scaling

## 📚 API Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key | None | Yes |
| `QDRANT_URL` | Qdrant database URL | `http://localhost:6333` | No |
| `QDRANT_API_KEY` | Qdrant API key | None | No |
| `MODEL_NAME` | Claude model name | `claude-3-5-sonnet-20241022` | No |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` | No |
| `MAX_CONCURRENT_UPLOADS` | Async upload limit | 5 | No |
| `MAX_FILE_SIZE` | Max file size in bytes | 52428800 | No |
| `CACHE_DIR` | Cache directory path | `/tmp/bmasterai_cache` | No |
| `CHUNK_SIZE` | Document chunk size | 1000 | No |
| `TOP_K` | Search result limit | 5 | No |
| `SIMILARITY_THRESHOLD` | Minimum similarity score | 0.7 | No |

### Performance Metrics

The system tracks various performance metrics:
- **Upload Time**: Average document processing time
- **Query Time**: Average question answering time
- **Success Rate**: Percentage of successful operations
- **Cache Hit Rate**: Percentage of cached responses
- **Error Count**: Total number of errors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/travis-burmaster/bmasterai/issues)
- **Email**: travis@burmaster.com
- **Documentation**: [BMasterAI Documentation](https://github.com/travis-burmaster/bmasterai)

## 🔄 Changelog

### Version 2.0.0 (Enhanced)
- ✅ Added async document processing
- ✅ Implemented intelligent caching
- ✅ Added connection pooling
- ✅ Enhanced performance monitoring
- ✅ Added advanced search features
- ✅ Improved error handling and retry logic
- ✅ Added export functionality
- ✅ Enhanced UI with new tabs and features

### Version 1.0.0 (Original)
- ✅ Basic RAG functionality
- ✅ Document upload and processing
- ✅ Vector search and Q&A
- ✅ BMasterAI integration
- ✅ Gradio web interface

## 📊 Performance Benchmarks

### Document Processing
- **Single Document**: ~2-5 seconds (depends on size)
- **Batch Processing**: ~30-50% faster than sequential
- **Cache Hit Rate**: ~80-90% for repeated content

### Query Performance
- **Simple Queries**: ~1-3 seconds
- **Complex Queries**: ~3-8 seconds
- **Cached Responses**: ~100-500ms

### System Resources
- **Memory Usage**: ~2-4GB during processing
- **CPU Usage**: ~50-80% during batch uploads
- **Disk Usage**: ~10-20MB per document (cached)

---

**Built with ❤️ using the BMasterAI Framework**