
"""LLM client with streaming support and BMasterAI integration"""
import os
import json
import time
import asyncio
import aiohttp
from typing import Dict, Any, Optional, AsyncGenerator
from utils.bmasterai_logging import get_logger, EventType, LogLevel
from utils.bmasterai_monitoring import get_monitor

class LLMClient:
    """LLM client with BMasterAI logging and monitoring"""
    
    def __init__(self):
        self.api_key = os.getenv('ABACUSAI_API_KEY')
        self.base_url = "https://apps.abacus.ai/v1/chat/completions"
        self.logger = get_logger()
        self.monitor = get_monitor()
        
        if not self.api_key:
            raise ValueError("ABACUSAI_API_KEY environment variable is required")
    
    async def call_llm(self, model: str, prompt: str, max_tokens: int = 1500, 
                      temperature: float = 0.7) -> Dict[str, Any]:
        """Make a simple LLM call without streaming"""
        start_time = time.time()
        
        # Log LLM call start
        self.logger.log_llm_call(
            agent_id="llm_client",
            model=model,
            prompt_length=len(prompt),
            max_tokens=max_tokens,
            metadata={"temperature": temperature}
        )
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                async with session.post(self.base_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        tokens_used = result.get("usage", {}).get("total_tokens", 0)
                        
                        duration_ms = (time.time() - start_time) * 1000
                        
                        # Track metrics
                        self.monitor.track_llm_call("llm_client", model, tokens_used, duration_ms)
                        
                        # Log successful completion
                        self.logger.log_event(
                            agent_id="llm_client",
                            event_type=EventType.TASK_COMPLETE,
                            message=f"LLM call completed: {model}",
                            duration_ms=duration_ms,
                            metadata={
                                "tokens_used": tokens_used,
                                "response_length": len(content)
                            }
                        )
                        
                        return {"response": content, "tokens_used": tokens_used}
                    else:
                        error_text = await response.text()
                        raise Exception(f"LLM API error {response.status}: {error_text}")
                        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.log_event(
                agent_id="llm_client",
                event_type=EventType.TASK_ERROR,
                message=f"LLM call failed: {str(e)}",
                level=LogLevel.ERROR,
                duration_ms=duration_ms,
                metadata={"model": model, "error": str(e)}
            )
            
            # Track error
            self.monitor.track_error("llm_client", "llm_call_error")
            
            raise
    
    async def call_llm_structured(self, model: str, prompt: str, max_tokens: int = 1500) -> Dict[str, Any]:
        """Make an LLM call expecting structured JSON response"""
        start_time = time.time()
        
        # Log LLM call start
        self.logger.log_llm_call(
            agent_id="llm_client",
            model=model,
            prompt_length=len(prompt),
            max_tokens=max_tokens,
            metadata={"response_format": "json"}
        )
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.3,  # Lower temperature for structured output
                    "response_format": {"type": "json_object"},
                    "stream": False
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                async with session.post(self.base_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                        tokens_used = result.get("usage", {}).get("total_tokens", 0)
                        
                        # Parse JSON response
                        try:
                            structured_response = json.loads(content)
                        except json.JSONDecodeError as e:
                            self.logger.log_event(
                                agent_id="llm_client",
                                event_type=EventType.TASK_ERROR,
                                message=f"Failed to parse JSON response: {str(e)}",
                                level=LogLevel.WARNING,
                                metadata={"raw_response": content[:500]}
                            )
                            # Return a fallback structure
                            structured_response = {"error": "Failed to parse JSON", "raw_response": content}
                        
                        duration_ms = (time.time() - start_time) * 1000
                        
                        # Track metrics
                        self.monitor.track_llm_call("llm_client", model, tokens_used, duration_ms)
                        
                        # Log successful completion
                        self.logger.log_event(
                            agent_id="llm_client",
                            event_type=EventType.TASK_COMPLETE,
                            message=f"Structured LLM call completed: {model}",
                            duration_ms=duration_ms,
                            metadata={
                                "tokens_used": tokens_used,
                                "response_keys": list(structured_response.keys()) if isinstance(structured_response, dict) else []
                            }
                        )
                        
                        return structured_response
                    else:
                        error_text = await response.text()
                        raise Exception(f"LLM API error {response.status}: {error_text}")
                        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.log_event(
                agent_id="llm_client",
                event_type=EventType.TASK_ERROR,
                message=f"Structured LLM call failed: {str(e)}",
                level=LogLevel.ERROR,
                duration_ms=duration_ms,
                metadata={"model": model, "error": str(e)}
            )
            
            # Track error
            self.monitor.track_error("llm_client", "structured_llm_call_error")
            
            raise
    
    async def stream_llm_call(self, model: str, prompt: str, max_tokens: int = 1500) -> AsyncGenerator[str, None]:
        """Make a streaming LLM call"""
        start_time = time.time()
        
        # Log LLM call start
        self.logger.log_llm_call(
            agent_id="llm_client",
            model=model,
            prompt_length=len(prompt),
            max_tokens=max_tokens,
            metadata={"streaming": True}
        )
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": True
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                async with session.post(self.base_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        full_response = ""
                        
                        async for line in response.content:
                            line_text = line.decode('utf-8').strip()
                            
                            if line_text.startswith('data: '):
                                data_part = line_text[6:]
                                
                                if data_part == '[DONE]':
                                    break
                                
                                try:
                                    chunk_data = json.loads(data_part)
                                    content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    
                                    if content:
                                        full_response += content
                                        yield content
                                        
                                except json.JSONDecodeError:
                                    continue
                        
                        # Log completion
                        duration_ms = (time.time() - start_time) * 1000
                        self.monitor.track_llm_call("llm_client", model, len(full_response.split()), duration_ms)
                        
                        self.logger.log_event(
                            agent_id="llm_client",
                            event_type=EventType.TASK_COMPLETE,
                            message=f"Streaming LLM call completed: {model}",
                            duration_ms=duration_ms,
                            metadata={"response_length": len(full_response)}
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"LLM API error {response.status}: {error_text}")
                        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.log_event(
                agent_id="llm_client",
                event_type=EventType.TASK_ERROR,
                message=f"Streaming LLM call failed: {str(e)}",
                level=LogLevel.ERROR,
                duration_ms=duration_ms,
                metadata={"model": model, "error": str(e)}
            )
            
            # Track error
            self.monitor.track_error("llm_client", "streaming_llm_call_error")
            
            raise

def get_llm_client() -> LLMClient:
    """Get LLM client instance"""
    return LLMClient()
