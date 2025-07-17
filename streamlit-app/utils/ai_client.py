"""AI client utilities for interfacing with OpenAI and other LLM providers."""

import json
import time
import requests
from typing import Dict, Any, Optional, AsyncGenerator, Generator
from openai import OpenAI
from config import config
import streamlit as st

# Import BMasterAI integration
from utils.bmasterai_integration import bmasterai_manager

class AIClient:
    """Enhanced AI client with streaming support and multiple providers."""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=config.openai_api_key)
        self.perplexity_available = bool(config.perplexity_api_key)
    
    def stream_chat_completion(self, messages: list, model: str = None) -> Generator[str, None, None]:
        """Stream chat completion responses from OpenAI."""
        model = model or config.openai_model
        prompt_length = sum(len(m.get("content", "")) for m in messages)
        
        # Log LLM request with BMasterAI
        bmasterai_manager.log_llm_request(
            model=model,
            prompt_length=prompt_length,
            metadata={
                "message_count": len(messages),
                "streaming": True,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature
            }
        )
        
        # Start task timing
        task_start = bmasterai_manager.log_task_start(
            task_name="stream_chat_completion",
            metadata={"model": model}
        )
        
        try:
            stream = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                stream=True
            )
            
            # Track response
            response_length = 0
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    response_length += len(content)
                    yield content
            
            # Log successful completion
            bmasterai_manager.log_llm_response(
                model=model,
                response_length=response_length,
                metadata={
                    "streaming": True,
                    "success": True
                }
            )
            
            # Log task completion
            bmasterai_manager.log_task_complete(
                task_name="stream_chat_completion",
                start_time=task_start,
                metadata={
                    "model": model,
                    "response_length": response_length
                }
            )
                    
        except Exception as e:
            # Log error
            bmasterai_manager.log_error(
                error_type="llm_streaming_error",
                error_message=str(e),
                metadata={
                    "model": model
                }
            )
            
            yield f"Error: {str(e)}"
    
    def chat_completion(self, messages: list, model: str = None) -> Dict[str, Any]:
        """Get non-streaming chat completion from OpenAI."""
        model = model or config.openai_model
        prompt_length = sum(len(m.get("content", "")) for m in messages)
        
        # Log LLM request with BMasterAI
        bmasterai_manager.log_llm_request(
            model=model,
            prompt_length=prompt_length,
            metadata={
                "message_count": len(messages),
                "streaming": False,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature
            }
        )
        
        # Start task timing
        task_start = bmasterai_manager.log_task_start(
            task_name="chat_completion",
            metadata={"model": model}
        )
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            # Extract usage statistics
            usage = response.usage.dict() if response.usage else {}
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
            # Log successful completion
            bmasterai_manager.log_llm_response(
                model=model,
                response_length=len(response.choices[0].message.content),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                metadata={
                    "streaming": False,
                    "success": True,
                    "total_tokens": usage.get("total_tokens", 0)
                }
            )
            
            # Log task completion
            bmasterai_manager.log_task_complete(
                task_name="chat_completion",
                start_time=task_start,
                metadata={
                    "model": model,
                    "total_tokens": usage.get("total_tokens", 0)
                }
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "usage": usage,
                "model": response.model
            }
            
        except Exception as e:
            # Log error
            bmasterai_manager.log_error(
                error_type="llm_completion_error",
                error_message=str(e),
                metadata={
                    "model": model
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def perplexity_search(self, query: str, system_prompt: str = None) -> Dict[str, Any]:
        """Enhanced Perplexity search with error handling."""
        if not self.perplexity_available:
            return {
                "success": False,
                "error": "Perplexity API key not configured",
                "content": None
            }
        
        try:
            system_prompt = system_prompt or "Be precise and concise. Focus on business insights and market data."
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json={
                    "model": "sonar",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ]
                },
                headers={
                    "Authorization": f"Bearer {config.perplexity_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and result["choices"]:
                return {
                    "success": True,
                    "content": result["choices"][0]["message"]["content"],
                    "citations": result.get("citations", []),
                    "usage": result.get("usage", {}),
                    "model": result.get("model", "sonar")
                }
            else:
                return {
                    "success": False,
                    "error": "No response content found",
                    "content": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Perplexity search failed: {str(e)}",
                "content": None
            }
    
    def get_consultation_response(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get a comprehensive consultation response."""
        context = context or {}
        
        # Build comprehensive system prompt
        system_prompt = """You are an expert AI business consultant with deep knowledge in:
        - Market analysis and business strategy
        - Technology trends and digital transformation
        - Risk assessment and mitigation
        - Strategic planning and implementation
        - Competitive analysis and positioning
        
        Provide detailed, actionable advice with specific recommendations.
        Structure your response with clear sections and bullet points where appropriate.
        Always consider both opportunities and risks in your analysis.
        """
        
        # Add context if available
        if context:
            context_str = json.dumps(context, indent=2)
            system_prompt += f"\n\nAdditional context:\n{context_str}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        return self.chat_completion(messages)

# Global AI client instance
ai_client = AIClient()