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