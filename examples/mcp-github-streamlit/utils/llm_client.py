
"""LLM client with streaming support and BMasterAI integration"""
import os
import json
import time
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
import anthropic
from utils.bmasterai_logging import get_logger, EventType, LogLevel
from utils.bmasterai_monitoring import get_monitor
from config import get_config_manager

class LLMClient:
    """LLM client with BMasterAI logging and monitoring"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.anthropic_config = self.config_manager.get_anthropic_config()
        self.logger = get_logger()
        self.monitor = get_monitor()
        
        if not self.anthropic_config.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.Anthropic(api_key=self.anthropic_config.api_key)
    
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
            # Use asyncio to run the synchronous Anthropic client in a thread pool
            def _call_anthropic():
                return self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
            
            # Run the synchronous call in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(None, _call_anthropic)
            
            # Extract content and token usage
            content = response.content[0].text if response.content else ""
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
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
        
        # Enhance prompt to request JSON format
        json_prompt = f"{prompt}\n\nPlease respond with a valid JSON object only. Do not include any other text or formatting."
        
        # Log LLM call start
        self.logger.log_llm_call(
            agent_id="llm_client",
            model=model,
            prompt_length=len(json_prompt),
            max_tokens=max_tokens,
            metadata={"response_format": "json"}
        )
        
        try:
            # Use asyncio to run the synchronous Anthropic client in a thread pool
            def _call_anthropic():
                return self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.3,  # Lower temperature for structured output
                    messages=[{"role": "user", "content": json_prompt}]
                )
            
            # Run the synchronous call in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(None, _call_anthropic)
            
            # Extract content and token usage
            content = response.content[0].text if response.content else "{}"
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
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
            full_response = ""
            
            # Use asyncio to run the synchronous streaming in a thread
            def _stream_anthropic():
                return self.client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
            
            # Run the stream creation in a thread pool
            stream = await asyncio.get_event_loop().run_in_executor(None, _stream_anthropic)
            
            # Process the stream
            with stream as stream_context:
                async for text in self._async_stream_wrapper(stream_context):
                    if text:
                        full_response += text
                        yield text
            
            # Log completion
            duration_ms = (time.time() - start_time) * 1000
            estimated_tokens = len(full_response.split()) * 1.3  # Rough estimate
            self.monitor.track_llm_call("llm_client", model, int(estimated_tokens), duration_ms)
            
            self.logger.log_event(
                agent_id="llm_client",
                event_type=EventType.TASK_COMPLETE,
                message=f"Streaming LLM call completed: {model}",
                duration_ms=duration_ms,
                metadata={"response_length": len(full_response)}
            )
                        
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
    
    async def _async_stream_wrapper(self, stream):
        """Wrapper to make Anthropic's synchronous stream work with async generators"""
        def _iterate_stream():
            for text in stream.text_stream:
                yield text
        
        # Process stream chunks in executor to avoid blocking
        for text in await asyncio.get_event_loop().run_in_executor(None, lambda: list(_iterate_stream())):
            yield text

def get_llm_client() -> LLMClient:
    """Get LLM client instance"""
    return LLMClient()
