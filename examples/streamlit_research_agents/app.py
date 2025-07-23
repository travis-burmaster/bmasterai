import streamlit as st
import os
import sys
from pathlib import Path
import logging
from typing import Optional, Dict, Any

# Add parent directory to path for bmasterai imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from bmasterai import BMasterAI
    from bmasterai.agents import ResearchAgent
    from bmasterai.tools import WebSearchTool, DocumentAnalyzer
except ImportError as e:
    st.error(f"Failed to import BMasterAI modules: {e}")
    st.stop()

# Import configuration
try:
    from config import Config
except ImportError:
    st.error("Configuration module not found. Please ensure config.py exists.")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'research_agent' not in st.session_state:
        st.session_state.research_agent = None
    if 'bmasterai_client' not in st.session_state:
        st.session_state.bmasterai_client = None


def validate_api_keys() -> Dict[str, str]:
    """Validate and return required API keys."""
    api_keys = {}
    
    # Check for BMasterAI API key
    bmasterai_key = os.getenv('BMASTERAI_API_KEY') or Config.BMASTERAI_API_KEY
    if not bmasterai_key:
        st.error("BMasterAI API key not found. Please set BMASTERAI_API_KEY environment variable.")
        st.stop()
    api_keys['bmasterai'] = bmasterai_key
    
    # Check for optional API keys
    openai_key = os.getenv('OPENAI_API_KEY') or getattr(Config, 'OPENAI_API_KEY', None)
    if openai_key:
        api_keys['openai'] = openai_key
    
    return api_keys


def initialize_bmasterai_client(api_keys: Dict[str, str]) -> Optional[BMasterAI]:
    """Initialize BMasterAI client with proper error handling."""
    try:
        client = BMasterAI(
            api_key=api_keys['bmasterai'],
            base_url=getattr(Config, 'BMASTERAI_BASE_URL', 'https://api.bmasterai.com'),
            timeout=getattr(Config, 'REQUEST_TIMEOUT', 30)
        )
        return client
    except Exception as e:
        logger.error(f"Failed to initialize BMasterAI client: {e}")
        st.error(f"Failed to initialize BMasterAI client: {e}")
        return None


def initialize_research_agent(client: BMasterAI) -> Optional[ResearchAgent]:
    """Initialize research agent with tools and configuration."""
    try:
        # Initialize tools
        web_search = WebSearchTool(
            api_key=os.getenv('SEARCH_API_KEY') or getattr(Config, 'SEARCH_API_KEY', None)
        )
        doc_analyzer = DocumentAnalyzer()
        
        # Create research agent
        agent = ResearchAgent(
            client=client,
            name="Research Assistant",
            description="AI-powered research assistant for comprehensive information gathering",
            tools=[web_search, doc_analyzer],
            model=getattr(Config, 'DEFAULT_MODEL', 'gpt-4'),
            temperature=getattr(Config, 'DEFAULT_TEMPERATURE', 0.7),
            max_tokens=getattr(Config, 'MAX_TOKENS', 2000)
        )
        
        return agent
    except Exception as e:
        logger.error(f"Failed to initialize research agent: {e}")
        st.error(f"Failed to initialize research agent: {e}")
        return None


def handle_user_input(user_input: str, agent: ResearchAgent):
    """Process user input and generate research response."""
    try:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Researching..."):
                response = agent.research(
                    query=user_input,
                    max_sources=getattr(Config, 'MAX_RESEARCH_SOURCES', 5),
                    include_citations=True
                )
                
                if response:
                    st.write(response.content)
                    
                    # Display sources if available
                    if hasattr(response, 'sources') and response.sources:
                        with st.expander("Sources"):
                            for idx, source in enumerate(response.sources, 1):
                                st.write(f"{idx}. [{source.title}]({source.url})")
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response.content
                    })
                else:
                    st.error("Failed to generate research response.")
                    
    except Exception as e:
        logger.error(f"Error processing user input: {e}")
        st.error(f"An error occurred while processing your request: {e}")


def display_chat_history():
    """Display chat history from session state."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="BMasterAI Research Assistant",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 BMasterAI Research Assistant")
    st.markdown("Powered by BMasterAI - Your intelligent research companion")
    
    # Initialize session state
    initialize_session_state()
    
    # Validate API keys
    api_keys = validate_api_keys()
    
    # Initialize BMasterAI client if not already done
    if st.session_state.bmasterai_client is None:
        st.session_state.bmasterai_client = initialize_bmasterai_client(api_keys)
        if st.session_state.bmasterai_client is None:
            st.stop()
    
    # Initialize research agent if not already done
    if st.session_state.research_agent is None:
        st.session_state.research_agent = initialize_research_agent(
            st.session_state.bmasterai_client
        )
        if st.session_state.research_agent is None:
            st.stop()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Model selection
        model = st.selectbox(
            "Model",
            options=getattr(Config, 'AVAILABLE_MODELS', ['gpt-4', 'gpt-3.5-turbo']),
            index=0
        )
        
        # Temperature slider
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=getattr(Config, 'DEFAULT_TEMPERATURE', 0.7),
            step=0.1
        )
        
        # Update agent configuration
        if st.button("Update Configuration"):
            st.session_state.research_agent.model = model
            st.session_state.research_agent.temperature = temperature
            st.success("Configuration updated!")
        
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Display chat history
    display_chat_history()
    
    # Chat input
    if prompt := st.chat_input("Ask me anything for research..."):
        handle_user_input(prompt, st.session_state.research_agent)


if __name__ == "__main__":
    main()