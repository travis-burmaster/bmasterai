#!/usr/bin/env python3
"""
Test Qdrant connection with the configured settings
"""

import os
from dotenv import load_dotenv

def test_qdrant_connection():
    """Test connection to Qdrant"""
    print("🧪 Testing Qdrant connection...")
    
    # Load environment variables
    load_dotenv()
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    print(f"📍 Qdrant URL: {qdrant_url}")
    
    try:
        from qdrant_client import QdrantClient
        print("✅ qdrant-client is available")
    except ImportError:
        print("❌ qdrant-client not available")
        print("Install with: pip install qdrant-client")
        return False
    
    try:
        # Create client
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        
        # Test connection by getting collections
        collections = client.get_collections()
        print(f"✅ Successfully connected to Qdrant")
        print(f"📊 Found {len(collections.collections)} collections")
        
        for collection in collections.collections:
            print(f"   - {collection.name}")
        
        # Test health
        try:
            health = client.get_cluster_info()
            print("✅ Cluster is healthy")
        except Exception as e:
            print(f"⚠️  Could not get cluster info: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        print("Please check your QDRANT_URL and QDRANT_API_KEY in .env file")
        return False

if __name__ == "__main__":
    try:
        success = test_qdrant_connection()
        if success:
            print("\n🎉 Qdrant connection test passed!")
        else:
            print("\n❌ Qdrant connection test failed")
    except Exception as e:
        print(f"\n❌ Error during Qdrant test: {e}")
        import traceback
        traceback.print_exc()