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

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

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