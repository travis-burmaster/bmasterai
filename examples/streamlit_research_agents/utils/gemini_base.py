
"""
Custom base classes and utilities for Google Gemini API integration.
Replaces BMasterAI framework components.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import json
import re


class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class AgentError(Exception):
    """Custom exception for agent operations"""
    pass


class BaseAgent:
    """
    Custom BaseAgent class to replace BMasterAI's BaseAgent.
    Provides core agent functionality with status management.
    """
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.status_message = ""
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
        # Status callbacks
        self.status_callbacks: List[Callable] = []
    
    def update_status(self, status: str, message: str = ""):
        """Update agent status and notify callbacks"""
        if isinstance(status, str):
            try:
                self.status = AgentStatus(status)
            except ValueError:
                self.status = AgentStatus.PROCESSING
        else:
            self.status = status
        
        self.status_message = message
        self.last_updated = datetime.now()
        
        # Notify callbacks
        for callback in self.status_callbacks:
            try:
                callback(self.name, self.status.value, message)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.status_message,
            'last_updated': self.last_updated.isoformat()
        }
    
    def add_status_callback(self, callback: Callable):
        """Add status update callback"""
        self.status_callbacks.append(callback)
    
    async def process(self, input_data: str, **kwargs) -> str:
        """
        Process method to be implemented by subclasses.
        This is the main processing interface for agents.
        """
        raise NotImplementedError("Subclasses must implement the process method")


class GeminiClient:
    """
    Google Gemini API client wrapper.
    Replaces BMasterAI's LLMTool functionality.
    """
    
    def __init__(self, api_key: str = None, model_name: str = "gemini-pro"):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
        # Generation configuration
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            top_p=0.9,
            top_k=40,
            max_output_tokens=4000,
        )
        
        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate response using Gemini API.
        Replaces BMasterAI's LLMTool.generate_response method.
        """
        try:
            # Override generation config if provided
            config = self.generation_config
            if kwargs:
                config_dict = {
                    'temperature': kwargs.get('temperature', 0.1),
                    'top_p': kwargs.get('top_p', 0.9),
                    'top_k': kwargs.get('top_k', 40),
                    'max_output_tokens': kwargs.get('max_tokens', 4000),
                }
                config = genai.types.GenerationConfig(**config_dict)
            
            # Generate content
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=config,
                safety_settings=self.safety_settings
            )
            
            if response.candidates and response.candidates[0].content:
                return response.candidates[0].content.parts[0].text
            else:
                self.logger.warning("Empty response from Gemini API")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise AgentError(f"Failed to generate response: {str(e)}")
    
    async def generate_structured_response(self, prompt: str, response_format: str = "json") -> Dict[str, Any]:
        """Generate structured response (JSON) from Gemini"""
        try:
            structured_prompt = f"""
            {prompt}
            
            Please respond in valid {response_format.upper()} format only. 
            Do not include any text before or after the {response_format.upper()}.
            """
            
            response = await self.generate_response(structured_prompt)
            
            if response_format.lower() == "json":
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    else:
                        self.logger.warning("Could not parse JSON response")
                        return {"content": response}
            
            return {"content": response}
            
        except Exception as e:
            self.logger.error(f"Error generating structured response: {str(e)}")
            return {"error": str(e)}


class TextProcessor:
    """
    Custom text processing utilities.
    Replaces BMasterAI's TextProcessor functionality.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common punctuation issues
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([.!?])\s*([a-z])', r'\1 \2', text)
        
        return text.strip()
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """Extract key phrases from text"""
        if not text:
            return []
        
        # Simple key phrase extraction
        sentences = re.split(r'[.!?]+', text)
        phrases = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                phrases.append(sentence)
        
        return phrases[:max_phrases]
    
    def summarize_text(self, text: str, max_length: int = 500) -> str:
        """Create a simple summary of text"""
        if not text or len(text) <= max_length:
            return text
        
        sentences = re.split(r'[.!?]+', text)
        summary_sentences = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and current_length + len(sentence) <= max_length:
                summary_sentences.append(sentence)
                current_length += len(sentence)
            elif current_length > 0:
                break
        
        return '. '.join(summary_sentences) + '.'
    
    def format_citations(self, sources: List[str], format_style: str = "apa") -> str:
        """Format citations in specified style"""
        if not sources:
            return ""
        
        formatted_citations = []
        for i, source in enumerate(sources, 1):
            if format_style.lower() == "apa":
                formatted_citations.append(f"{i}. {source}")
            else:
                formatted_citations.append(f"[{i}] {source}")
        
        return '\n'.join(formatted_citations)


class BaseTool:
    """
    Base tool class for compatibility.
    Replaces BMasterAI's BaseTool.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    async def execute(self, *args, **kwargs) -> Any:
        """Execute tool functionality"""
        raise NotImplementedError("Subclasses must implement execute method")


# Utility functions
def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_api_key() -> bool:
    """Validate that Google API key is available"""
    api_key = os.getenv('GOOGLE_API_KEY')
    return api_key is not None and len(api_key.strip()) > 0


async def test_gemini_connection(api_key: str = None) -> bool:
    """Test connection to Gemini API"""
    try:
        client = GeminiClient(api_key)
        response = await client.generate_response("Hello, this is a test.")
        return len(response) > 0
    except Exception:
        return False
