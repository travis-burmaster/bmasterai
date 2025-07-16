#!/bin/bash

# Enhanced BMasterAI RAG System Setup Script
# This script sets up the complete environment for the enhanced RAG system

set -e  # Exit on any error

echo "🚀 Setting up Enhanced BMasterAI RAG System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check Python version
print_step "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.8"

if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_status "Python $python_version is compatible"
else
    print_error "Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

# Check if virtual environment exists
print_step "Setting up virtual environment..."
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_step "Upgrading pip..."
pip install --upgrade pip

# Install requirements
print_step "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_error "requirements.txt not found"
    exit 1
fi

# Create cache directory
print_step "Setting up cache directory..."
mkdir -p /tmp/bmasterai_cache
print_status "Cache directory created at /tmp/bmasterai_cache"

# Check for Docker (for Qdrant)
print_step "Checking for Docker..."
if command -v docker &> /dev/null; then
    print_status "Docker is installed"
    
    # Check if Qdrant is already running
    if docker ps | grep -q qdrant; then
        print_status "Qdrant container is already running"
    else
        print_step "Starting Qdrant container..."
        docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest
        print_status "Qdrant container started on port 6333"
    fi
else
    print_warning "Docker not found. You'll need to set up Qdrant manually or use Qdrant Cloud"
fi

# Create .env file template
print_step "Creating environment configuration..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Enhanced BMasterAI RAG Configuration
# Copy this file and fill in your actual values

# =============================================================================
# REQUIRED CONFIGURATION
# =============================================================================

# Anthropic API Key - Get from https://console.anthropic.com/
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# =============================================================================
# VECTOR DATABASE CONFIGURATION
# =============================================================================

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Optional for local instance, required for Qdrant Cloud

# For Qdrant Cloud, use:
# QDRANT_URL=https://your-cluster-url.qdrant.tech
# QDRANT_API_KEY=your-qdrant-cloud-api-key

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# LLM Model Configuration
MODEL_NAME=claude-3-5-sonnet-20241022
MAX_TOKENS=4096
TEMPERATURE=0.7

# Embedding Model Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
COLLECTION_NAME=bmasterai_documents

# =============================================================================
# DOCUMENT PROCESSING CONFIGURATION
# =============================================================================

# Text Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Search Configuration
TOP_K=5
SIMILARITY_THRESHOLD=0.7

# File Upload Configuration
MAX_FILE_SIZE=52428800  # 50MB in bytes
MAX_CONCURRENT_UPLOADS=5

# =============================================================================
# PERFORMANCE & CACHING
# =============================================================================

# Cache Configuration
CACHE_DIR=/tmp/bmasterai_cache
ENABLE_RESPONSE_CACHE=true
ENABLE_EMBEDDING_CACHE=true

# Connection Pooling
MAX_CONNECTIONS=5
CONNECTION_TIMEOUT=30

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================

# Gradio Server Settings
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
GRADIO_SHARE=false
GRADIO_AUTH=  # Optional: username:password for basic auth

# =============================================================================
# LOGGING & MONITORING
# =============================================================================

# Logging Configuration
LOG_LEVEL=INFO
ENABLE_JSON_LOGS=false
ENABLE_FILE_LOGS=true
LOG_FILE_PATH=logs/bmasterai_rag.log

# Monitoring
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_USAGE_TRACKING=true

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

# Slack Integration (optional)
SLACK_WEBHOOK_URL=
SLACK_CHANNEL=#ai-notifications

# Email Integration (optional)
SMTP_SERVER=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=

# =============================================================================
# SYSTEM PROMPT CUSTOMIZATION
# =============================================================================

# Custom system prompt (optional - will use default if empty)
SYSTEM_PROMPT=

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# Rate Limiting (requests per minute)
RATE_LIMIT_PER_MINUTE=60

# File Upload Security
ALLOWED_FILE_EXTENSIONS=pdf,docx,txt
MAX_FILENAME_LENGTH=255

# =============================================================================
# DEVELOPMENT/DEBUG SETTINGS
# =============================================================================

# Debug Mode
DEBUG_MODE=false
VERBOSE_LOGGING=false

# Development Server
DEV_MODE=false
AUTO_RELOAD=false
EOF
    print_status "Created comprehensive .env template file"
    print_warning "Please edit .env file with your actual configuration values"
    print_warning "At minimum, set your ANTHROPIC_API_KEY"
else
    print_status ".env file already exists"
fi

# Create start script
print_step "Creating start script..."
cat > start.sh << 'EOF'
#!/bin/bash

# Enhanced BMasterAI RAG System Startup Script

set -e

echo "🚀 Starting Enhanced BMasterAI RAG System..."

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your configuration."
    exit 1
fi

# Load environment variables (filter out empty lines and comments)
export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)

# Check required environment variables
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your-anthropic-api-key-here" ]; then
    echo "❌ ANTHROPIC_API_KEY is not set in .env file"
    echo "   Get your API key from: https://console.anthropic.com/"
    exit 1
fi

# Check if Qdrant is running (if using local instance)
if [ "$QDRANT_URL" = "http://localhost:6333" ]; then
    if ! curl -s http://localhost:6333/health > /dev/null 2>&1; then
        echo "❌ Qdrant is not running on localhost:6333"
        echo "   Start Qdrant with: docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest"
        exit 1
    else
        echo "✅ Qdrant is running on localhost:6333"
    fi
fi

# Create cache directory if it doesn't exist
mkdir -p "$CACHE_DIR"

# Start the application
echo "🌐 Starting Enhanced BMasterAI RAG System on $GRADIO_SERVER_NAME:$GRADIO_SERVER_PORT"
python bmasterai-gradio-rag.py
EOF

chmod +x start.sh
print_status "Created start.sh script"

# Create stop script
print_step "Creating stop script..."
cat > stop.sh << 'EOF'
#!/bin/bash

# Enhanced BMasterAI RAG System Stop Script

echo "🛑 Stopping Enhanced BMasterAI RAG System..."

# Find and kill the gradio process
pkill -f "bmasterai-gradio-rag.py" || true

# Stop Qdrant container if running
if docker ps | grep -q qdrant; then
    echo "Stopping Qdrant container..."
    docker stop qdrant || true
fi

echo "✅ Enhanced BMasterAI RAG System stopped"
EOF

chmod +x stop.sh
print_status "Created stop.sh script"

# Final setup completion
print_step "Completing setup..."

# Set permissions
chmod +x start.sh stop.sh

print_status "Setup completed successfully!"

echo
echo "🎉 Enhanced BMasterAI RAG System setup complete!"
echo
echo "📝 Next steps:"
echo "1. Edit .env file with your configuration values"
echo "2. Get your Anthropic API key from: https://console.anthropic.com/"
echo "3. Run './start.sh' to start the system"
echo "4. Open http://localhost:7860 in your browser"
echo
echo "🚀 Quick start:"
echo "   ./start.sh"
echo
echo "🛑 To stop:"
echo "   ./stop.sh"
echo
echo "🐳 Docker deployment:"
echo "   docker-compose up -d"
echo
echo "📊 Features enabled:"
echo "   ✅ Async document processing"
echo "   ✅ Intelligent caching"
echo "   ✅ Performance monitoring"
echo "   ✅ Connection pooling"
echo "   ✅ Retry logic"
echo "   ✅ Advanced search"
echo "   ✅ Export functionality"
echo
echo "For more information, see README.md"