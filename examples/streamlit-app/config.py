"""Configuration management for the AI Consultant Streamlit app."""

import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config(BaseSettings):
    """Application configuration with validation."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # Perplexity Configuration (optional)
    perplexity_api_key: Optional[str] = None
    
    # Application Configuration
    app_name: str = "AI Business Consultant"
    agent_name: str = "AI Business Consultant"
    
    # Integration Configuration (optional)
    slack_webhook_url: Optional[str] = None
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    
    # Security Configuration
    session_timeout: int = 3600
    max_conversation_length: int = 50
    
    # BMasterAI Configuration
    bmasterai_enabled: bool = True
    bmasterai_log_level: str = "INFO"
    bmasterai_enable_json_logs: bool = False
    bmasterai_enable_file_logs: bool = True
    bmasterai_log_file: str = "logs/bmasterai.log"
    bmasterai_agent_id: str = "streamlit-app"
    bmasterai_enable_monitoring: bool = True
    bmasterai_enable_slack: bool = False
    bmasterai_enable_email: bool = False
    
    @validator('openai_api_key')
    def validate_openai_api_key(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Invalid OpenAI API key')
        return v
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if not 100 <= v <= 10000:
            raise ValueError('Max tokens must be between 100 and 10000')
        return v
    
    class Config:
        env_file = '.env'
        case_sensitive = False

# Global config instance
try:
    config = Config()
except Exception as e:
    # Create a default config for development
    config = Config(
        openai_api_key="sk-placeholder",
        openai_model="gpt-4-turbo-preview",
        max_tokens=4000,
        temperature=0.7
    )
    print(f"Warning: Using default config due to error: {e}")