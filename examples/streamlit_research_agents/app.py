import streamlit as st
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
import json
import os
from pathlib import Path

# Import our custom agents and utilities
from agents.research_coordinator import ResearchCoordinator
from agents.search_agent import SearchAgent
from agents.synthesis_agent import SynthesisAgent
from agents.editing_agent import EditingAgent
from utils.perplexity_client import PerplexityClient
from utils.report_generator import ReportGenerator

# Import BMasterAI logging configuration
from config.logging_config import initialize_logging, get_logging_config

class StreamlitResearchApp:
    """Main Streamlit application for multi-agent research collaboration."""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_logging()
        self.initialize_session_state()
        self.setup_agents()
    
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="AI Research Agents",
            page_icon="🔬",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_logging(self):
        """Initialize BMasterAI logging and monitoring."""
        try:
            # Initialize BMasterAI logging configuration
            self.logging_config = initialize_logging()
            self.app_logger = self.logging_config.get_logger("StreamlitApp")
            
            # Log application startup
            self.app_logger.info("Research Agents application starting up")
            self.logging_config.log_metric("app_startup", 1.0, {"version": "1.0.0"})
            
            # Store in session state for access by other components
            if 'logging_config' not in st.session_state:
                st.session_state.logging_config = self.logging_config
                
        except Exception as e:
            print(f"Warning: Failed to initialize BMasterAI logging: {e}")
            # Fallback to basic logging
            import logging
            logging.basicConfig(level=logging.INFO)
            self.app_logger = logging.getLogger("StreamlitApp")
            self.logging_config = None
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'research_active' not in st.session_state:
            st.session_state.research_active = False
        
        if 'research_results' not in st.session_state:
            st.session_state.research_results = {}
        
        if 'agent_status' not in st.session_state:
            st.session_state.agent_status = {
                'coordinator': 'idle',
                'search': 'idle',
                'synthesis': 'idle',
                'editing': 'idle'
            }
        
        if 'progress_log' not in st.session_state:
            st.session_state.progress_log = []
        
        if 'current_stage' not in st.session_state:
            st.session_state.current_stage = 'ready'
    
    def setup_agents(self):
        """Initialize AI agents if API key is available."""
        perplexity_api_key = st.session_state.get('perplexity_api_key', '')
        
        if perplexity_api_key and perplexity_api_key.strip():
            try:
                # Initialize Perplexity client
                st.info("Initializing Perplexity client...")
                perplexity_client = PerplexityClient(api_key=perplexity_api_key)
                
                # Initialize agents step by step with progress feedback
                st.info("Initializing Search Agent...")
                self.search_agent = SearchAgent(perplexity_client)
                
                st.info("Initializing Synthesis Agent...")
                self.synthesis_agent = SynthesisAgent()
                
                st.info("Initializing Editing Agent...")
                self.editing_agent = EditingAgent()
                
                st.info("Initializing Research Coordinator...")
                self.coordinator = ResearchCoordinator(
                    search_agent=self.search_agent,
                    synthesis_agent=self.synthesis_agent,
                    editing_agent=self.editing_agent
                )
                
                st.info("Initializing Report Generator...")
                self.report_generator = ReportGenerator()
                
                st.success("All agents initialized successfully!")
                
            except ImportError as e:
                st.error(f"Import error - missing dependency: {str(e)}")
                st.info("Please ensure all required packages are installed: pip install -r requirements.txt")
                self.coordinator = None
            except ValueError as e:
                if "API key" in str(e):
                    st.error("⚠️ API Key Required")
                    st.info("Please enter your Perplexity API key in the sidebar to enable research functionality.")
                else:
                    st.error(f"Configuration error: {str(e)}")
                self.coordinator = None
            except Exception as e:
                st.error(f"Error initializing agents: {str(e)}")
                st.exception(e)  # Show full traceback for debugging
                self.coordinator = None
        else:
            self.coordinator = None
            if not perplexity_api_key:
                st.info("💡 Enter your Perplexity API key in the sidebar to enable research functionality.")
            if st.session_state.get('show_api_key_warning', True):
                st.warning("Please enter your Perplexity API key in the sidebar to enable research functionality.")
                st.session_state.show_api_key_warning = False
    
    def render_sidebar(self):
        """Render the sidebar with configuration options."""
        st.sidebar.title("🔬 Research Configuration")
        
        # API Key Configuration
        st.sidebar.subheader("API Configuration")
        api_key = st.sidebar.text_input(
            "Perplexity API Key",
            type="password",
            value=st.session_state.get('perplexity_api_key', ''),
            help="Enter your Perplexity API key to enable research functionality"
        )
        
        if not api_key:
            st.sidebar.info("💡 **Get your API key:**\n\n1. Visit [perplexity.ai](https://perplexity.ai)\n2. Sign up/Login\n3. Go to Settings → API\n4. Generate a new API key")
        
        if api_key != st.session_state.get('perplexity_api_key', ''):
            st.session_state.perplexity_api_key = api_key
            self.setup_agents()
            st.rerun()
        
        # Research Parameters
        st.sidebar.subheader("Research Parameters")
        
        research_topic = st.sidebar.text_area(
            "Research Topic",
            value=st.session_state.get('research_topic', ''),
            height=100,
            help="Describe the topic you want to research"
        )
        st.session_state.research_topic = research_topic
        
        research_depth = st.sidebar.selectbox(
            "Research Depth",
            options=['Basic', 'Intermediate', 'Comprehensive'],
            index=1,
            help="Select the depth of research analysis"
        )
        st.session_state.research_depth = research_depth
        
        max_sources = st.sidebar.slider(
            "Maximum Sources",
            min_value=5,
            max_value=50,
            value=st.session_state.get('max_sources', 15),
            help="Maximum number of sources to gather"
        )
        st.session_state.max_sources = max_sources
        
        output_format = st.sidebar.selectbox(
            "Output Format",
            options=['Markdown', 'HTML', 'PDF'],
            index=0,
            help="Select the format for the final report"
        )
        st.session_state.output_format = output_format
        
        # Agent Status
        st.sidebar.subheader("Agent Status")
        self.render_agent_status()
        
        # Control Buttons
        st.sidebar.subheader("Controls")
        
        start_disabled = (
            not api_key or 
            not research_topic.strip() or 
            st.session_state.research_active or
            self.coordinator is None
        )
        
        if st.sidebar.button(
            "🚀 Start Research",
            disabled=start_disabled,
            help="Begin the multi-agent research process"
        ):
            self.start_research()
        
        if st.sidebar.button(
            "⏹️ Stop Research",
            disabled=not st.session_state.research_active,
            help="Stop the current research process"
        ):
            self.stop_research()
        
        if st.sidebar.button(
            "🗑️ Clear Results",
            help="Clear all research results and logs"
        ):
            self.clear_results()
    
    def render_agent_status(self):
        """Render agent status indicators in the sidebar."""
        status_colors = {
            'idle': '⚪',
            'working': '🟡',
            'completed': '🟢',
            'error': '🔴'
        }
        
        for agent_name, status in st.session_state.agent_status.items():
            color = status_colors.get(status, '⚪')
            st.sidebar.text(f"{color} {agent_name.title()}: {status}")
    
    def render_main_content(self):
        """Render the main content area."""
        st.title("🔬 AI Research Agents")
        st.markdown("Multi-agent collaboration for complex research tasks")
        
        # Progress Section
        if st.session_state.research_active or st.session_state.progress_log:
            self.render_progress_section()
        
        # Results Section
        if st.session_state.research_results:
            self.render_results_section()
        
        # Welcome Section (when no research is active)
        if not st.session_state.research_active and not st.session_state.research_results:
            self.render_welcome_section()
    
    def render_welcome_section(self):
        """Render welcome information when no research is active."""
        st.markdown("""
        ## Welcome to AI Research Agents
        
        This application demonstrates multi-agent collaboration for complex research tasks. 
        Our specialized AI agents work together to:
        
        - 🔍 **Search Agent**: Gathers information using the Perplexity API
        - 🧠 **Synthesis Agent**: Analyzes and synthesizes findings
        - ✏️ **Editing Agent**: Refines and formats the final report
        - 🎯 **Coordinator Agent**: Manages the entire workflow
        
        ### Getting Started
        1. Enter your Perplexity API key in the sidebar
        2. Describe your research topic
        3. Configure research parameters
        4. Click "Start Research" to begin
        
        ### Features
        - Real-time progress tracking
        - Agent status monitoring
        - Multiple output formats
        - Comprehensive research reports
        """)
    
    def render_progress_section(self):
        """Render the progress tracking section."""
        st.subheader("📊 Research Progress")
        
        # Current Stage
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("Current Stage", st.session_state.current_stage.title())
        
        with col2:
            if st.session_state.research_active:
                st.info("Research in progress... Please wait.")
            else:
                st.success("Research completed!")
        
        # Progress Log
        if st.session_state.progress_log:
            st.subheader("📝 Activity Log")
            
            # Create a container for the log that auto-scrolls
            log_container = st.container()
            with log_container:
                for entry in reversed(st.session_state.progress_log[-10:]):  # Show last 10 entries
                    timestamp = entry.get('timestamp', '')
                    agent = entry.get('agent', 'System')
                    message = entry.get('message', '')
                    
                    st.text(f"[{timestamp}] {agent}: {message}")
    
    def render_results_section(self):
        """Render the research results section."""
        st.subheader("📋 Research Results")
        
        results = st.session_state.research_results
        
        # Results tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Sources", "Analysis", "Full Report"])
        
        with tab1:
            if 'summary' in results:
                st.markdown("### Executive Summary")
                st.markdown(results['summary'])
        
        with tab2:
            if 'sources' in results:
                st.markdown("### Sources")
                for i, source in enumerate(results['sources'], 1):
                    with st.expander(f"Source {i}: {source.get('title', 'Unknown')}"):
                        st.markdown(f"**URL:** {source.get('url', 'N/A')}")
                        st.markdown(f"**Summary:** {source.get('summary', 'N/A')}")
        
        with tab3:
            if 'analysis' in results:
                st.markdown("### Analysis")
                st.markdown(results['analysis'])
        
        with tab4:
            if 'full_report' in results:
                st.markdown("### Full Report")
                st.markdown(results['full_report'])
                
                # Download button
                if self.report_generator:
                    try:
                        report_data = self.report_generator.generate_report(
                            results,
                            format=st.session_state.output_format.lower()
                        )
                        
                        st.download_button(
                            label=f"📥 Download {st.session_state.output_format} Report",
                            data=report_data,
                            file_name=f"research_report.{st.session_state.output_format.lower()}",
                            mime=self.get_mime_type(st.session_state.output_format)
                        )
                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")
    
    def get_mime_type(self, format_type: str) -> str:
        """Get MIME type for download button."""
        mime_types = {
            'Markdown': 'text/markdown',
            'HTML': 'text/html',
            'PDF': 'application/pdf'
        }
        return mime_types.get(format_type, 'text/plain')
    
    def start_research(self):
        """Start the research process."""
        if not self.coordinator:
            st.error("Coordinator not initialized. Please check your API key.")
            return
        
        st.session_state.research_active = True
        st.session_state.research_results = {}
        st.session_state.progress_log = []
        st.session_state.current_stage = 'initializing'
        
        self.add_log_entry('System', 'Starting research process...')
        
        # Run research in a separate thread to avoid blocking the UI
        self.run_research_async()
    
    def run_research_async(self):
        """Run the research process asynchronously."""
        try:
            # Prepare research parameters
            research_params = {
                'query': st.session_state.research_topic,  # Changed from 'topic' to 'query'
                'depth': st.session_state.research_depth,
                'max_sources': st.session_state.max_sources,
                'output_format': st.session_state.output_format
            }
            
            # Debug logging
            self.add_log_entry('System', f"Starting research with topic: '{st.session_state.research_topic}'")
            self.add_log_entry('System', f"Research params: {research_params}")
            
            # Update status
            self.update_agent_status('coordinator', 'working')
            st.session_state.current_stage = 'coordinating'
            
            # Start the research process
            results = asyncio.run(self.coordinator.conduct_research(
                research_params,
                progress_callback=self.progress_callback
            ))
            
            # Store results
            st.session_state.research_results = results
            st.session_state.research_active = False
            st.session_state.current_stage = 'completed'
            
            self.add_log_entry('System', 'Research completed successfully!')
            self.update_all_agents_status('completed')
            
        except Exception as e:
            st.session_state.research_active = False
            st.session_state.current_stage = 'error'
            self.add_log_entry('System', f'Research failed: {str(e)}')
            self.update_all_agents_status('error')
            st.error(f"Research failed: {str(e)}")
    
    def progress_callback(self, agent: str, stage: str, message: str):
        """Callback function for progress updates."""
        self.add_log_entry(agent, message)
        self.update_agent_status(agent.lower(), 'working')
        st.session_state.current_stage = stage
        
        # Force UI update
        st.rerun()
    
    def stop_research(self):
        """Stop the current research process."""
        st.session_state.research_active = False
        st.session_state.current_stage = 'stopped'
        self.add_log_entry('System', 'Research stopped by user')
        self.update_all_agents_status('idle')
    
    def clear_results(self):
        """Clear all research results and logs."""
        st.session_state.research_results = {}
        st.session_state.progress_log = []
        st.session_state.current_stage = 'ready'
        self.update_all_agents_status('idle')
        st.rerun()
    
    def add_log_entry(self, agent: str, message: str):
        """Add an entry to the progress log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {
            'timestamp': timestamp,
            'agent': agent,
            'message': message
        }
        st.session_state.progress_log.append(entry)
    
    def update_agent_status(self, agent: str, status: str):
        """Update the status of a specific agent."""
        if agent in st.session_state.agent_status:
            st.session_state.agent_status[agent] = status
    
    def update_all_agents_status(self, status: str):
        """Update the status of all agents."""
        for agent in st.session_state.agent_status:
            st.session_state.agent_status[agent] = status
    
    def run(self):
        """Main application entry point."""
        try:
            self.render_sidebar()
            self.render_main_content()
            
            # Auto-refresh when research is active
            if st.session_state.research_active:
                time.sleep(2)
                st.rerun()
                
        except Exception as e:
            st.error(f"Application error: {str(e)}")
            st.exception(e)

def main():
    """Application entry point."""
    app = StreamlitResearchApp()
    app.run()

if __name__ == "__main__":
    main()