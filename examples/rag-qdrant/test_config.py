#!/usr/bin/env python3
"""
Simple test script to validate .env configuration loading
"""

import os
from typing import Any

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv is available")
except ImportError:
    print("❌ python-dotenv not available")
    exit(1)

def get_env_var(key: str, default: Any = None, var_type: type = str) -> Any:
    """Get environment variable with type conversion and validation"""
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
        print(f"Warning: Invalid value for {key}: {value}. Using default: {default}")
        return default

def test_config_loading():
    """Test configuration loading from .env file"""
    print("🧪 Testing .env configuration loading...")
    
    # Load environment variables
    load_dotenv()
    print("✅ Environment variables loaded")
    
    # Test required configuration
    anthropic_api_key = get_env_var("ANTHROPIC_API_KEY")
    if not anthropic_api_key or anthropic_api_key == "your-anthropic-api-key-here":
        print("❌ ANTHROPIC_API_KEY is not properly configured")
        return False
    else:
        print(f"✅ Anthropic API key configured: {anthropic_api_key[:10]}...")
    
    # Test Qdrant configuration
    qdrant_url = get_env_var("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = get_env_var("QDRANT_API_KEY")
    
    print(f"✅ Qdrant URL: {qdrant_url}")
    if qdrant_api_key and qdrant_api_key.strip():
        print(f"✅ Qdrant API key configured: {qdrant_api_key[:10]}...")
    else:
        print("⚠️  Qdrant API key not configured (OK for local instance)")
    
    # Test model configuration
    model_name = get_env_var("MODEL_NAME", "claude-3-5-sonnet-20241022")
    embedding_model = get_env_var("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    collection_name = get_env_var("COLLECTION_NAME", "bmasterai_documents")
    
    print(f"✅ Model: {model_name}")
    print(f"✅ Embedding Model: {embedding_model}")
    print(f"✅ Collection: {collection_name}")
    
    # Test numeric configurations
    max_tokens = get_env_var("MAX_TOKENS", 4096, int)
    temperature = get_env_var("TEMPERATURE", 0.7, float)
    chunk_size = get_env_var("CHUNK_SIZE", 1000, int)
    chunk_overlap = get_env_var("CHUNK_OVERLAP", 200, int)
    
    print(f"✅ Max Tokens: {max_tokens}")
    print(f"✅ Temperature: {temperature}")
    print(f"✅ Chunk Size: {chunk_size}")
    print(f"✅ Chunk Overlap: {chunk_overlap}")
    
    # Test boolean configurations
    enable_cache = get_env_var("ENABLE_RESPONSE_CACHE", True, bool)
    debug_mode = get_env_var("DEBUG_MODE", False, bool)
    
    print(f"✅ Response Cache: {enable_cache}")
    print(f"✅ Debug Mode: {debug_mode}")
    
    # Test server configuration
    server_name = get_env_var("GRADIO_SERVER_NAME", "0.0.0.0")
    server_port = get_env_var("GRADIO_SERVER_PORT", 7860, int)
    
    print(f"✅ Server: {server_name}:{server_port}")
    
    # Validation checks
    issues = []
    
    if chunk_overlap >= chunk_size:
        issues.append("CHUNK_OVERLAP must be less than CHUNK_SIZE")
    
    if temperature < 0 or temperature > 2:
        issues.append("TEMPERATURE must be between 0 and 2")
    
    if max_tokens <= 0:
        issues.append("MAX_TOKENS must be positive")
    
    if server_port <= 0 or server_port > 65535:
        issues.append("GRADIO_SERVER_PORT must be between 1 and 65535")
    
    if issues:
        print("❌ Configuration validation issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Configuration validation passed")
    
    return True

if __name__ == "__main__":
    try:
        success = test_config_loading()
        if success:
            print("\n🎉 Configuration test completed successfully!")
            print("✅ Your .env file is properly configured")
        else:
            print("\n❌ Configuration test failed")
            print("Please check your .env file")
    except Exception as e:
        print(f"\n❌ Error during configuration test: {e}")
        import traceback
        traceback.print_exc()