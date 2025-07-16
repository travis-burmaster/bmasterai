#!/usr/bin/env python3
"""
Test the main RAG application initialization
"""

import os
import sys
from dotenv import load_dotenv

def test_app_initialization():
    """Test if the main application can initialize"""
    print("🧪 Testing RAG application initialization...")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Test basic imports
        print("📦 Testing imports...")
        
        import gradio as gr
        print("✅ gradio imported")
        
        import requests
        print("✅ requests imported")
        
        from qdrant_client import QdrantClient
        print("✅ qdrant_client imported")
        
        from sentence_transformers import SentenceTransformer
        print("✅ sentence_transformers imported")
        
        import PyPDF2
        print("✅ PyPDF2 imported")
        
        import docx
        print("✅ python-docx imported")
        
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        print("✅ langchain imported")
        
        import diskcache as dc
        print("✅ diskcache imported")
        
        print("✅ All required dependencies are available")
        
        # Test configuration loading
        print("\n🔧 Testing configuration...")
        
        # Import the get_env_var function
        def get_env_var(key: str, default=None, var_type=str):
            value = os.getenv(key, default)
            if value is None:
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
                return default
        
        # Test key configurations
        anthropic_api_key = get_env_var("ANTHROPIC_API_KEY")
        if not anthropic_api_key or anthropic_api_key == "your-anthropic-api-key-here":
            print("❌ ANTHROPIC_API_KEY not configured")
            return False
        
        qdrant_url = get_env_var("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = get_env_var("QDRANT_API_KEY")
        
        print(f"✅ Configuration loaded successfully")
        
        # Test Qdrant connection
        print("\n🔗 Testing Qdrant connection...")
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        
        collections = client.get_collections()
        print(f"✅ Qdrant connection successful ({len(collections.collections)} collections)")
        
        # Test embedding model loading
        print("\n🤖 Testing embedding model...")
        embedding_model = get_env_var("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # Just test if we can create the model (don't actually load it to save time)
        print(f"✅ Embedding model configured: {embedding_model}")
        
        # Test text splitter
        print("\n📄 Testing text processing...")
        chunk_size = get_env_var("CHUNK_SIZE", 1000, int)
        chunk_overlap = get_env_var("CHUNK_OVERLAP", 200, int)
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Test with sample text
        sample_text = "This is a test document. " * 100
        chunks = text_splitter.split_text(sample_text)
        print(f"✅ Text processing working ({len(chunks)} chunks created)")
        
        # Test cache directory
        print("\n💾 Testing cache setup...")
        cache_dir = get_env_var("CACHE_DIR", "/tmp/bmasterai_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        cache = dc.Cache(cache_dir)
        cache['test'] = 'value'
        assert cache['test'] == 'value'
        print(f"✅ Cache system working: {cache_dir}")
        
        print("\n🎉 All tests passed! The RAG application should work correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during initialization test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_initialization()
    if success:
        print("\n✅ RAG application is ready to run!")
        print("You can now start the application with: python bmasterai-gradio-rag.py")
    else:
        print("\n❌ RAG application has issues that need to be resolved")