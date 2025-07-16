#!/usr/bin/env python3
"""
BMasterAI RAG Example with Anthropic API and Qdrant Vector Database
Document upload, vectorization, and semantic search through Gradio UI
"""

import os
import json
import logging
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

import gradio as gr
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import PyPDF2
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BMasterAIRAGConfig:
    """Configuration for BMasterAI RAG system"""
    anthropic_api_key: str
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    model_name: str = "claude-3-5-sonnet-20241022"
    embedding_model: str = "all-MiniLM-L6-v2"
    collection_name: str = "bmasterai_documents"
    max_tokens: int = 4096
    temperature: float = 0.7
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7
    system_prompt: str = """You are a helpful AI assistant that answers questions based on provided documents. 
    Use the context provided to answer questions accurately. If the answer isn't in the provided context, 
    say so clearly. Always cite relevant document sources when available."""

class DocumentProcessor:
    """Handle document processing and text extraction"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {e}")
            return ""
    
    def extract_text(self, file_path: str, filename: str) -> str:
        """Extract text based on file extension"""
        ext = filename.lower().split('.')[-1]
        
        if ext == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext == 'docx':
            return self.extract_text_from_docx(file_path)
        elif ext == 'txt':
            return self.extract_text_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return ""
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        chunks = self.text_splitter.split_text(text)
        
        chunked_docs = []
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Skip empty chunks
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_id': i,
                    'chunk_text': chunk,
                    'chunk_hash': hashlib.md5(chunk.encode()).hexdigest()
                })
                chunked_docs.append(chunk_metadata)
        
        return chunked_docs

class VectorStore:
    """Qdrant vector database interface"""
    
    def __init__(self, config: BMasterAIRAGConfig):
        self.config = config
        self.client = QdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key
        )
        self.embedding_model = SentenceTransformer(config.embedding_model)
        self.collection_name = config.collection_name
        
        # Initialize collection
        self._init_collection()
    
    def _init_collection(self):
        """Initialize Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(
                col.name == self.collection_name 
                for col in collections.collections
            )
            
            if not collection_exists:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to vector store"""
        try:
            points = []
            for doc in documents:
                # Generate embedding
                embedding = self.embedding_model.encode(doc['chunk_text'])
                
                # Create point
                point = PointStruct(
                    id=doc['chunk_hash'],
                    vector=embedding.tolist(),
                    payload={
                        'filename': doc['filename'],
                        'file_hash': doc['file_hash'],
                        'chunk_id': doc['chunk_id'],
                        'chunk_text': doc['chunk_text'],
                        'upload_time': doc['upload_time'],
                        'file_size': doc['file_size']
                    }
                )
                points.append(point)
            
            # Insert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(points)} document chunks to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return False
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k,
                with_payload=True
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'score': result.score,
                    'text': result.payload['chunk_text'],
                    'filename': result.payload['filename'],
                    'chunk_id': result.payload['chunk_id'],
                    'upload_time': result.payload['upload_time']
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'status': info.status,
                'points_count': info.points_count,
                'vectors_count': info.vectors_count,
                'segments_count': info.segments_count
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {'error': str(e)}
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the collection"""
        try:
            # Use scroll to get all points
            result = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,  # Adjust based on your needs
                with_payload=True
            )
            
            documents = {}
            for point in result[0]:
                filename = point.payload['filename']
                if filename not in documents:
                    documents[filename] = {
                        'filename': filename,
                        'file_hash': point.payload['file_hash'],
                        'upload_time': point.payload['upload_time'],
                        'file_size': point.payload['file_size'],
                        'chunk_count': 0
                    }
                documents[filename]['chunk_count'] += 1
            
            return list(documents.values())
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []

class AnthropicChat:
    """Anthropic API interface"""
    
    def __init__(self, config: BMasterAIRAGConfig):
        self.config = config
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for API request"""
        return {
            "Content-Type": "application/json",
            "x-api-key": self.config.anthropic_api_key,
            "anthropic-version": "2023-06-01"
        }
    
    def generate_response(self, query: str, context: str) -> str:
        """Generate response using context and query"""
        try:
            # Prepare context-aware prompt
            prompt = f"""Context from documents:
{context}

User question: {query}

Please answer the question based on the provided context. If the answer isn't in the context, say so clearly."""
            
            # Prepare request payload
            payload = {
                "model": self.config.model_name,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "system": self.config.system_prompt,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            # Make API request
            response = requests.post(
                self.base_url,
                headers=self._prepare_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return f"Error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"

class BMasterAIRAGSystem:
    """Main RAG system combining all components"""
    
    def __init__(self, config: BMasterAIRAGConfig):
        self.config = config
        self.doc_processor = DocumentProcessor(config.chunk_size, config.chunk_overlap)
        self.vector_store = VectorStore(config)
        self.chat = AnthropicChat(config)
        
        # Session tracking
        self.session_stats = {
            'documents_uploaded': 0,
            'queries_processed': 0,
            'start_time': datetime.now().isoformat()
        }
    
    def upload_document(self, file_path: str, filename: str) -> Tuple[bool, str]:
        """Upload and process a document"""
        try:
            # Extract text
            text = self.doc_processor.extract_text(file_path, filename)
            if not text:
                return False, "Could not extract text from document"
            
            # Prepare metadata
            file_hash = hashlib.md5(text.encode()).hexdigest()
            metadata = {
                'filename': filename,
                'file_hash': file_hash,
                'upload_time': datetime.now().isoformat(),
                'file_size': len(text)
            }
            
            # Chunk document
            chunks = self.doc_processor.chunk_text(text, metadata)
            if not chunks:
                return False, "Could not chunk document"
            
            # Add to vector store
            success = self.vector_store.add_documents(chunks)
            
            if success:
                self.session_stats['documents_uploaded'] += 1
                return True, f"Successfully uploaded {filename} with {len(chunks)} chunks"
            else:
                return False, "Failed to add document to vector store"
                
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return False, f"Error uploading document: {str(e)}"
    
    def search_and_answer(self, query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Search documents and generate answer"""
        try:
            # Search for relevant documents
            search_results = self.vector_store.search_documents(
                query, 
                top_k=self.config.top_k
            )
            
            if not search_results:
                return "No relevant documents found for your query.", []
            
            # Prepare context
            context = "\n\n".join([
                f"Document: {result['filename']}\n{result['text']}"
                for result in search_results
                if result['score'] >= self.config.similarity_threshold
            ])
            
            if not context:
                return "No sufficiently relevant documents found for your query.", search_results
            
            # Generate response
            response = self.chat.generate_response(query, context)
            
            self.session_stats['queries_processed'] += 1
            return response, search_results
            
        except Exception as e:
            logger.error(f"Error in search and answer: {e}")
            return f"Error processing query: {str(e)}", []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information"""
        try:
            collection_info = self.vector_store.get_collection_info()
            
            return {
                'session_stats': self.session_stats,
                'collection_info': collection_info,
                'config': {
                    'model_name': self.config.model_name,
                    'embedding_model': self.config.embedding_model,
                    'collection_name': self.config.collection_name,
                    'chunk_size': self.config.chunk_size,
                    'top_k': self.config.top_k
                }
            }
        except Exception as e:
            return {'error': str(e)}

class BMasterAIRAGApp:
    """Gradio application for RAG system"""
    
    def __init__(self):
        # Initialize configuration
        self.config = BMasterAIRAGConfig(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            model_name=os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            collection_name=os.getenv("COLLECTION_NAME", "bmasterai_documents"),
            max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            top_k=int(os.getenv("TOP_K", "5")),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
        )
        
        # Initialize RAG system
        try:
            self.rag_system = BMasterAIRAGSystem(self.config)
            self.system_status = "✅ RAG System Initialized"
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.system_status = f"❌ System Error: {e}"
            self.rag_system = None
    
    def upload_file(self, file) -> str:
        """Handle file upload"""
        if not self.rag_system:
            return "❌ RAG system not initialized"
        
        if file is None:
            return "❌ No file selected"
        
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.name).suffix) as tmp_file:
                tmp_file.write(file.read())
                tmp_path = tmp_file.name
            
            # Upload document
            success, message = self.rag_system.upload_document(tmp_path, file.name)
            
            # Clean up
            os.unlink(tmp_path)
            
            if success:
                return f"✅ {message}"
            else:
                return f"❌ {message}"
                
        except Exception as e:
            logger.error(f"Error in file upload: {e}")
            return f"❌ Error uploading file: {str(e)}"
    
    def search_documents(self, query: str) -> Tuple[str, str]:
        """Search documents and return answer with sources"""
        if not self.rag_system:
            return "❌ RAG system not initialized", ""
        
        if not query.strip():
            return "❌ Please enter a query", ""
        
        try:
            # Search and answer
            answer, sources = self.rag_system.search_and_answer(query)
            
            # Format sources
            sources_text = ""
            if sources:
                sources_text = "**Sources:**\n"
                for i, source in enumerate(sources, 1):
                    sources_text += f"{i}. {source['filename']} (Score: {source['score']:.3f})\n"
                    sources_text += f"   {source['text'][:200]}...\n\n"
            
            return answer, sources_text
            
        except Exception as e:
            logger.error(f"Error in document search: {e}")
            return f"❌ Error processing query: {str(e)}", ""
    
    def get_system_info(self) -> str:
        """Get system information"""
        if not self.rag_system:
            return "❌ RAG system not initialized"
        
        try:
            status = self.rag_system.get_system_status()
            
            info = f"""
**System Status:** {self.system_status}

**Session Statistics:**
- Documents Uploaded: {status['session_stats']['documents_uploaded']}
- Queries Processed: {status['session_stats']['queries_processed']}
- Session Started: {status['session_stats']['start_time']}

**Collection Information:**
- Status: {status['collection_info'].get('status', 'Unknown')}
- Points Count: {status['collection_info'].get('points_count', 'Unknown')}
- Vectors Count: {status['collection_info'].get('vectors_count', 'Unknown')}

**Configuration:**
- Model: {status['config']['model_name']}
- Embedding Model: {status['config']['embedding_model']}
- Collection: {status['config']['collection_name']}
- Chunk Size: {status['config']['chunk_size']}
- Top K: {status['config']['top_k']}
            """
            
            return info.strip()
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return f"❌ Error getting system info: {str(e)}"
    
    def list_documents(self) -> str:
        """List all uploaded documents"""
        if not self.rag_system:
            return "❌ RAG system not initialized"
        
        try:
            documents = self.rag_system.vector_store.list_documents()
            
            if not documents:
                return "📭 No documents uploaded yet"
            
            doc_list = "**Uploaded Documents:**\n\n"
            for doc in documents:
                doc_list += f"📄 **{doc['filename']}**\n"
                doc_list += f"   - Chunks: {doc['chunk_count']}\n"
                doc_list += f"   - Size: {doc['file_size']} characters\n"
                doc_list += f"   - Uploaded: {doc['upload_time']}\n\n"
            
            return doc_list
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return f"❌ Error listing documents: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        
        custom_css = """
        .gradio-container {
            max-width: 1400px;
            margin: auto;
        }
        .header-text {
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #2E86AB;
        }
        .upload-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .search-section {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 20px;
            border-radius: 10px;
        }
        .status-box {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        """
        
        with gr.Blocks(css=custom_css, title="BMasterAI RAG System") as demo:
            
            # Header
            gr.HTML("""
            <div class="header-text">
                🔍 BMasterAI RAG System
            </div>
            <div style="text-align: center; margin-bottom: 30px;">
                <p style="font-size: 1.2em; color: #666;">
                    Upload documents, search with AI, and get intelligent answers
                </p>
                <p style="color: #888;">
                    Powered by Anthropic Claude + Qdrant Vector Database
                </p>
            </div>
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    # Document Upload Section
                    with gr.Group():
                        gr.HTML('<div class="upload-section">')
                        gr.HTML("<h3 style='color: white; margin-top: 0;'>📁 Document Upload</h3>")
                        
                        file_upload = gr.File(
                            label="Upload Document",
                            file_types=[".pdf", ".docx", ".txt"],
                            type="binary"
                        )
                        
                        upload_btn = gr.Button("Upload Document", variant="primary")
                        upload_status = gr.Textbox(
                            label="Upload Status",
                            interactive=False,
                            lines=2
                        )
                        gr.HTML('</div>')
                    
                    # System Information
                    with gr.Group():
                        gr.HTML("<h3>🔧 System Information</h3>")
                        
                        system_info = gr.Markdown(
                            value=self.get_system_info(),
                            label="System Status"
                        )
                        
                        refresh_btn = gr.Button("Refresh Info", variant="secondary")
                        
                        # Document List
                        gr.HTML("<h4>📚 Document Library</h4>")
                        document_list = gr.Markdown(
                            value=self.list_documents(),
                            label="Uploaded Documents"
                        )
                        
                        list_docs_btn = gr.Button("Refresh Documents", variant="secondary")
                
                with gr.Column(scale=2):
                    # Search and Chat Section
                    with gr.Group():
                        gr.HTML('<div class="search-section">')
                        gr.HTML("<h3 style='color: white; margin-top: 0;'>💬 Ask Questions</h3>")
                        
                        query_input = gr.Textbox(
                            label="Your Question",
                            placeholder="Ask a question about your uploaded documents...",
                            lines=2
                        )
                        
                        search_btn = gr.Button("Search & Answer", variant="primary")
                        
                        gr.HTML('</div>')
                    
                    # Results Section
                    with gr.Group():
                        gr.HTML("<h3>🤖 AI Response</h3>")
                        
                        answer_output = gr.Textbox(
                            label="Answer",
                            lines=8,
                            interactive=False
                        )
                        
                        sources_output = gr.Markdown(
                            label="Sources & Context",
                            value="Sources will appear here after searching..."
                        )
                    
                    # Configuration Section
                    with gr.Accordion("⚙️ Advanced Settings", open=False):
                        with gr.Row():
                            top_k_slider = gr.Slider(
                                minimum=1,
                                maximum=10,
                                value=self.config.top_k,
                                step=1,
                                label="Top K Results"
                            )
                            
                            similarity_threshold = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=self.config.similarity_threshold,
                                step=0.1,
                                label="Similarity Threshold"
                            )
                        
                        with gr.Row():
                            temperature_slider = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=self.config.temperature,
                                step=0.1,
                                label="Temperature"
                            )
                            
                            max_tokens_slider = gr.Slider(
                                minimum=100,
                                maximum=8192,
                                value=self.config.max_tokens,
                                step=100,
                                label="Max Tokens"
                            )
            
            # Event handlers
            upload_btn.click(
                self.upload_file,
                inputs=[file_upload],
                outputs=[upload_status]
            )
            
            search_btn.click(
                self.search_documents,
                inputs=[query_input],
                outputs=[answer_output, sources_output]
            )
            
            query_input.submit(
                self.search_documents,
                inputs=[query_input],
                outputs=[answer_output, sources_output]
            )
            
            refresh_btn.click(
                self.get_system_info,
                outputs=[system_info]
            )
            
            list_docs_btn.click(
                self.list_documents,
                outputs=[document_list]
            )
            
            # Auto-refresh document list after upload
            upload_btn.click(
                self.list_documents,
                outputs=[document_list]
            )
            
            # Auto-refresh system info after upload
            upload_btn.click(
                self.get_system_info,
                outputs=[system_info]
            )
        
        return demo

def main():
    """Main function to launch the RAG application"""
    # Environment setup instructions
    required_vars = {
        "ANTHROPIC_API_KEY": "Your Anthropic API key",
        "QDRANT_URL": "Qdrant server URL (default: http://localhost:6333)"
    }
    
    missing_vars = []
    for var, desc in required_vars.items():
        if not os.getenv(var) and var == "ANTHROPIC_API_KEY":
            missing_vars.append(f"{var}: {desc}")
    
    if missing_vars:
        print("\n" + "="*60)
        print("🔑 SETUP REQUIRED:")
        print("Please set the following environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nExample:")
        print("export ANTHROPIC_API_KEY='your-api-key-here'")
        print("export QDRANT_URL='http://localhost:6333'")
        print("\nOr create a .env file with these values")
        print("="*60 + "\n")
        print("ℹ️  Note: Make sure Qdrant is running on the specified URL")
        print("   Docker: docker run -p 6333:6333 qdrant/qdrant")
        print("")
    
    # Create and launch the application
    app = BMasterAIRAGApp()
    demo = app.create_interface()
    
    # Launch configuration
    server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    share = os.getenv("GRADIO_SHARE", "false").lower() == "true"
    
    logger.info(f"Launching BMasterAI RAG app on {server_name}:{server_port}")
    
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        show_error=True,
        debug=False
    )

if __name__ == "__main__":
    main()
