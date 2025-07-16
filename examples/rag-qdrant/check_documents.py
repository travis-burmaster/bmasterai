#!/usr/bin/env python3
"""
Quick script to check what documents are in the Qdrant collection
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

def check_documents():
    """Check what documents are stored in Qdrant"""
    load_dotenv()
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("COLLECTION_NAME", "bmasterai_documents")
    
    print(f"🔍 Checking Qdrant collection: {collection_name}")
    print(f"📍 Qdrant URL: {qdrant_url}")
    
    try:
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        
        # Get collection info
        try:
            info = client.get_collection(collection_name)
            print(f"✅ Collection exists")
            print(f"📊 Points count: {info.points_count}")
            print(f"📊 Vectors count: {info.vectors_count}")
            
            if info.points_count == 0:
                print("❌ No documents found in collection!")
                print("   Please upload documents using the web interface.")
                return False
            
            # Get some sample points
            result = client.scroll(
                collection_name=collection_name,
                limit=5,
                with_payload=True
            )
            
            print(f"\n📄 Sample documents:")
            documents = {}
            for point in result[0]:
                filename = point.payload.get('filename', 'Unknown')
                if filename not in documents:
                    documents[filename] = {
                        'chunks': 0,
                        'upload_time': point.payload.get('upload_time', 'Unknown')
                    }
                documents[filename]['chunks'] += 1
            
            for filename, info in documents.items():
                print(f"   - {filename}: {info['chunks']} chunks (uploaded: {info['upload_time']})")
            
            return True
            
        except Exception as e:
            print(f"❌ Collection '{collection_name}' not found or error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return False

if __name__ == "__main__":
    check_documents()