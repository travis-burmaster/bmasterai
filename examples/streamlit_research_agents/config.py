import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for API keys and endpoints"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    serper_api_key: Optional[str] = None
    wolfram_alpha_api_key: Optional[str] = None
    
    def __post_init__(self):
        """Load API keys from environment variables"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.google_api_key = os.getenv("GOOGLE_API_KEY", self.google_api_key)
        self.serper_api_key = os.getenv("SERPER_API_KEY", self.serper_api_key)
        self.wolfram_alpha_api_key = os.getenv("WOLFRAM_ALPHA_API_KEY", self.wolfram_alpha_api_key)
    
    def validate(self) -> Dict[str, bool]:
        """Validate which API keys are available"""
        return {
            "openai": bool(self.openai_api_key),
            "anthropic": bool(self.anthropic_api_key),
            "google": bool(self.google_api_key),
            "serper": bool(self.serper_api_key),
            "wolfram_alpha": bool(self.wolfram_alpha_api_key)
        }
    
    def get_available_models(self) -> list:
        """Return list of available models based on API keys"""
        models = []
        if self.openai_api_key:
            models.extend(["gpt-4", "gpt-3.5-turbo"])
        if self.anthropic_api_key:
            models.extend(["claude-2", "claude-instant"])
        if self.google_api_key:
            models.extend(["gemini-pro"])
        return models


@dataclass
class AgentConfig:
    """Configuration for research agent settings"""
    name: str = "Research Assistant"
    description: str = "An AI agent specialized in research and analysis"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    max_iterations: int = 5
    timeout: int = 300  # seconds
    
    # Research specific settings
    search_depth: int = 3
    max_search_results: int = 10
    enable_web_search: bool = True
    enable_academic_search: bool = False
    enable_code_execution: bool = False
    
    # Memory settings
    use_memory: bool = True
    memory_type: str = "buffer"  # buffer, summary, or vector
    max_memory_items: int = 50
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for agent initialization"""
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_iterations": self.max_iterations,
            "timeout": self.timeout,
            "search_depth": self.search_depth,
            "max_search_results": self.max_search_results,
            "enable_web_search": self.enable_web_search,
            "enable_academic_search": self.enable_academic_search,
            "enable_code_execution": self.enable_code_execution,
            "use_memory": self.use_memory,
            "memory_type": self.memory_type,
            "max_memory_items": self.max_memory_items
        }


class Config:
    """Main configuration class for the Streamlit Research Agents app"""
    
    def __init__(self):
        self.api_config = APIConfig()
        self.agent_config = AgentConfig()
        
        # App settings
        self.app_title = "BMasterAI Research Assistant"
        self.app_description = "An intelligent research assistant powered by BMasterAI"
        self.theme = "light"
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        
        # UI settings
        self.show_agent_thoughts = True
        self.show_search_results = True
        self.enable_file_upload = True
        self.max_file_size_mb = 10
        
        # Cache settings
        self.enable_cache = True
        self.cache_ttl = 3600  # 1 hour
        
        # Rate limiting
        self.rate_limit_enabled = True
        self.max_requests_per_minute = 10
        
    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration and return status with error messages"""
        errors = []
        api_status = self.api_config.validate()
        
        # Check if at least one LLM API key is available
        if not any([api_status["openai"], api_status["anthropic"], api_status["google"]]):
            errors.append("No LLM API key found. Please set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY")
        
        # Check if web search is enabled but no search API key
        if self.agent_config.enable_web_search and not api_status["serper"]:
            logger.warning("Web search enabled but SERPER_API_KEY not found. Web search will be disabled.")
            self.agent_config.enable_web_search = False
        
        # Validate model selection
        available_models = self.api_config.get_available_models()
        if self.agent_config.model not in available_models:
            if available_models:
                self.agent_config.model = available_models[0]
                logger.info(f"Selected model not available. Switching to {self.agent_config.model}")
            else:
                errors.append("No models available due to missing API keys")
        
        return len(errors) == 0, errors
    
    def get_agent_params(self) -> Dict[str, Any]:
        """Get parameters for agent initialization"""
        params = self.agent_config.to_dict()
        
        # Add API keys based on selected model
        if "gpt" in self.agent_config.model:
            params["api_key"] = self.api_config.openai_api_key
        elif "claude" in self.agent_config.model:
            params["api_key"] = self.api_config.anthropic_api_key
        elif "gemini" in self.agent_config.model:
            params["api_key"] = self.api_config.google_api_key
        
        # Add search API key if web search is enabled
        if self.agent_config.enable_web_search:
            params["search_api_key"] = self.api_config.serper_api_key
        
        return params
    
    def update_from_ui(self, **kwargs):
        """Update configuration from UI inputs"""
        for key, value in kwargs.items():
            if hasattr(self.agent_config, key):
                setattr(self.agent_config, key, value)
            elif hasattr(self, key):
                setattr(self, key, value)


# Create default configuration instance
default_config = Config()