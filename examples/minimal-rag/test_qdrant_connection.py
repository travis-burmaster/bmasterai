#!/usr/bin/env python3
"""
Test script for Qdrant Cloud connection
Simple script to verify Qdrant Cloud setup and connectivity
"""

import os
import sys
from typing import Dict, Any

def test_qdrant_connection() -> Dict[str, Any]:
    """Test connection to Qdrant Cloud"""
    
    # Check environment variables
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url:
        return {
            "success": False,
            "error": "QDRANT_URL environment variable not set",
            "help": "Set with: export QDRANT_URL='https://your-cluster.qdrant.io'"
        }
    
    if not qdrant_api_key:
        return {
            "success": False,
            "error": "QDRANT_API_KEY environment variable not set",
            "help": "Set with: export QDRANT_API_KEY='your-api-key'"
        }
    
    try:
        # Import Qdrant client
        from qdrant_client import QdrantClient
        
        # Create client
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        
        # Test connection by getting collections
        collections = client.get_collections()
        
        return {
            "success": True,
            "url": qdrant_url,
            "collections_count": len(collections.collections),
            "collections": [col.name for col in collections.collections],
            "message": "✅ Successfully connected to Qdrant Cloud!"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Missing dependency: {str(e)}",
            "help": "Install with: pip install qdrant-client"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Connection failed: {str(e)}",
            "help": "Check your URL and API key, ensure cluster is running"
        }

def test_openai_connection() -> Dict[str, Any]:
    """Test OpenAI API connection"""
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        return {
            "success": False,
            "error": "OPENAI_API_KEY environment variable not set",
            "help": "Set with: export OPENAI_API_KEY='your-api-key'"
        }
    
    try:
        import openai
        
        # Set API key
        openai.api_key = openai_api_key
        
        # Test with a simple completion
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        
        return {
            "success": True,
            "model": "gpt-3.5-turbo",
            "tokens_used": response.usage.total_tokens,
            "message": "✅ Successfully connected to OpenAI API!"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Missing dependency: {str(e)}",
            "help": "Install with: pip install openai"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"API call failed: {str(e)}",
            "help": "Check your API key and account status"
        }

def test_embedding_model() -> Dict[str, Any]:
    """Test sentence transformer model"""
    
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        # Load model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test encoding
        test_text = "This is a test sentence for embedding."
        embedding = model.encode(test_text)
        
        return {
            "success": True,
            "model": "all-MiniLM-L6-v2",
            "embedding_size": len(embedding),
            "embedding_type": str(type(embedding)),
            "message": "✅ Embedding model loaded successfully!"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Missing dependency: {str(e)}",
            "help": "Install with: pip install sentence-transformers"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Model loading failed: {str(e)}",
            "help": "Check internet connection for model download"
        }

def main():
    """Run all connection tests"""
    
    print("🧪 BMasterAI Qdrant Cloud RAG - Connection Tests")
    print("=" * 50)
    
    # Test Qdrant connection
    print("\n1. Testing Qdrant Cloud connection...")
    qdrant_result = test_qdrant_connection()
    
    if qdrant_result["success"]:
        print(f"   {qdrant_result['message']}")
        print(f"   URL: {qdrant_result['url']}")
        print(f"   Collections: {qdrant_result['collections_count']}")
        if qdrant_result['collections']:
            print(f"   Collection names: {', '.join(qdrant_result['collections'])}")
    else:
        print(f"   ❌ {qdrant_result['error']}")
        print(f"   💡 {qdrant_result['help']}")
    
    # Test OpenAI connection
    print("\n2. Testing OpenAI API connection...")
    openai_result = test_openai_connection()
    
    if openai_result["success"]:
        print(f"   {openai_result['message']}")
        print(f"   Model: {openai_result['model']}")
        print(f"   Test tokens used: {openai_result['tokens_used']}")
    else:
        print(f"   ❌ {openai_result['error']}")
        print(f"   💡 {openai_result['help']}")
    
    # Test embedding model
    print("\n3. Testing embedding model...")
    embedding_result = test_embedding_model()
    
    if embedding_result["success"]:
        print(f"   {embedding_result['message']}")
        print(f"   Model: {embedding_result['model']}")
        print(f"   Embedding size: {embedding_result['embedding_size']}")
    else:
        print(f"   ❌ {embedding_result['error']}")
        print(f"   💡 {embedding_result['help']}")
    
    # Summary
    print("\n" + "=" * 50)
    all_success = all([
        qdrant_result["success"],
        openai_result["success"],
        embedding_result["success"]
    ])
    
    if all_success:
        print("🎉 All tests passed! You're ready to run the RAG example.")
        print("\nNext steps:")
        print("   python bmasterai_rag_qdrant_cloud.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues above before running the RAG example.")
        
        # Show setup instructions
        print("\n📋 Quick Setup Guide:")
        print("1. Get Qdrant Cloud API key: https://cloud.qdrant.io/")
        print("2. Get OpenAI API key: https://platform.openai.com/")
        print("3. Set environment variables:")
        print("   export QDRANT_URL='https://your-cluster.qdrant.io'")
        print("   export QDRANT_API_KEY='your-qdrant-api-key'")
        print("   export OPENAI_API_KEY='your-openai-api-key'")
        print("4. Install dependencies:")
        print("   pip install -r requirements_qdrant.txt")
    
    return all_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)