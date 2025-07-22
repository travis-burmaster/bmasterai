
"""API route for streaming LLM analysis"""
import os
import json
import asyncio
from typing import Dict, Any
import streamlit as st

async def handle_streaming_analysis(request_data: Dict[str, Any]):
    """Handle streaming analysis request"""
    try:
        from utils.llm_client import get_llm_client
        
        llm_client = get_llm_client()
        
        # Get default model from configuration
        from config import get_config_manager
        config_manager = get_config_manager()
        model_config = config_manager.get_model_config()
        default_model = os.getenv('API_ANALYZE_MODEL', model_config.default_model)
        
        # Extract request parameters
        prompt = request_data.get("prompt", "")
        model = request_data.get("model", default_model)
        max_tokens = request_data.get("max_tokens", 1500)
        
        # Stream the response
        full_response = ""
        async for chunk in llm_client.stream_llm_call(model, prompt, max_tokens):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        # Send completion signal
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_response = {"error": str(e)}
        yield f"data: {json.dumps(error_response)}\n\n"

def create_streaming_endpoint():
    """Create streaming endpoint for Streamlit"""
    # This would be used if we were creating a FastAPI backend
    # For now, we'll handle streaming directly in the Streamlit app
    pass
