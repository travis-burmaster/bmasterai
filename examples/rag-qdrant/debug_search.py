#!/usr/bin/env python3
"""
Debug script to test the search functionality and identify the attribute error
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

def debug_search():
    """Debug the search functionality"""
    load_dotenv()
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("COLLECTION_NAME", "bmasterai_documents")
    
    print(f"🔍 Testing search functionality...")
    print(f"📍 Qdrant URL: {qdrant_url}")
    print(f"📚 Collection: {collection_name}")
    
    try:
        # Initialize client
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        
        # Initialize embedding model
        print("🤖 Loading embedding model...")
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Test query
        query = "What are the main topics?"
        print(f"❓ Query: {query}")
        
        # Generate embedding
        print("🔢 Generating embedding...")
        query_embedding = embedding_model.encode(query).tolist()
        print(f"✅ Embedding generated: {len(query_embedding)} dimensions")
        
        # Test search with query_points
        print("🔍 Testing query_points method...")
        try:
            search_result = client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                limit=5,
                with_payload=True
            )
            
            print(f"✅ Search successful!")
            print(f"📊 Type of search_result: {type(search_result)}")
            print(f"📊 Search result attributes: {dir(search_result)}")
            
            if hasattr(search_result, 'points'):
                points = search_result.points
                print(f"📊 Number of points: {len(points)}")
                
                for i, point in enumerate(points[:2]):  # Show first 2 results
                    print(f"\n📄 Result {i+1}:")
                    print(f"   Type: {type(point)}")
                    print(f"   Attributes: {dir(point)}")
                    
                    if hasattr(point, 'score'):
                        print(f"   Score: {point.score}")
                    if hasattr(point, 'payload'):
                        print(f"   Payload keys: {list(point.payload.keys())}")
                        if 'chunk_text' in point.payload:
                            text = point.payload['chunk_text']
                            print(f"   Text preview: {text[:100]}...")
            else:
                print("❌ No 'points' attribute in search result")
                
        except Exception as e:
            print(f"❌ Error with query_points: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
        
        # Test old search method for comparison
        print("\n🔍 Testing old search method...")
        try:
            old_results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=5,
                with_payload=True
            )
            
            print(f"✅ Old search successful!")
            print(f"📊 Type of old results: {type(old_results)}")
            print(f"📊 Number of old results: {len(old_results)}")
            
            if old_results:
                first_result = old_results[0]
                print(f"📊 First result type: {type(first_result)}")
                print(f"📊 First result attributes: {dir(first_result)}")
                
        except Exception as e:
            print(f"❌ Error with old search: {e}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_search()