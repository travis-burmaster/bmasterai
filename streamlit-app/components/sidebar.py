"""Sidebar component for the AI consultant application."""

import streamlit as st
from config import config
from components.chat_interface import chat_interface

class Sidebar:
    """Sidebar component for navigation and controls."""
    
    def __init__(self):
        self.config = config
    
    def render(self):
        """Render the sidebar."""
        with st.sidebar:
            st.title("🤖 AI Business Consultant")
            st.markdown("---")
            
            # Configuration section
            st.subheader("⚙️ Configuration")
            self._render_config_section()
            
            st.markdown("---")
            
            # Quick Actions
            st.subheader("🚀 Quick Actions")
            self._render_quick_actions()
            
            st.markdown("---")
            
            # Help section
            st.subheader("❓ Help")
            self._render_help_section()
            
            st.markdown("---")
            
            # About section
            st.subheader("ℹ️ About")
            self._render_about_section()
    
    def _render_config_section(self):
        """Render configuration options."""
        # Model selection
        model_options = [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
        
        current_model = st.selectbox(
            "AI Model",
            options=model_options,
            index=0 if config.openai_model in model_options else 0,
            help="Select the AI model for consultations"
        )
        
        # Update session state model
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = current_model
        else:
            st.session_state.selected_model = current_model
        
        # Temperature slider
        temperature = st.slider(
            "Response Creativity",
            min_value=0.0,
            max_value=1.0,
            value=config.temperature,
            step=0.1,
            help="Higher values make responses more creative, lower values more focused"
        )
        
        # Max tokens
        max_tokens = st.number_input(
            "Max Response Length",
            min_value=100,
            max_value=4000,
            value=config.max_tokens,
            step=100,
            help="Maximum number of tokens in the response"
        )
        
        # Store in session state
        st.session_state.temperature = temperature
        st.session_state.max_tokens = max_tokens
        
        # API Status
        st.markdown("**API Status:**")
        api_status = self._check_api_status()
        if api_status["openai"]:
            st.success("✅ OpenAI API Connected")
        else:
            st.error("❌ OpenAI API Not Connected")
        
        if api_status["perplexity"]:
            st.success("✅ Perplexity API Connected")
        else:
            st.warning("⚠️ Perplexity API Not Connected")
    
    def _render_quick_actions(self):
        """Render quick action buttons."""
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                chat_interface.clear_chat()
        
        with col2:
            if st.button("📊 Examples", use_container_width=True):
                self._show_examples()
        
        # Analysis tools
        st.markdown("**Analysis Tools:**")
        
        if st.button("📈 Market Analysis", use_container_width=True):
            self._trigger_market_analysis()
        
        if st.button("🏢 Competitor Analysis", use_container_width=True):
            self._trigger_competitor_analysis()
        
        if st.button("⚠️ Risk Assessment", use_container_width=True):
            self._trigger_risk_assessment()
        
        if st.button("💡 Get Recommendations", use_container_width=True):
            self._trigger_recommendations()
    
    def _render_help_section(self):
        """Render help information."""
        with st.expander("🔍 How to Use"):
            st.markdown("""
            **Getting Started:**
            1. Type your business question in the chat
            2. Ask for specific analysis (market, competitor, risk)
            3. Get detailed insights and recommendations
            
            **Example Questions:**
            - "I want to launch a SaaS startup in healthcare"
            - "Analyze the market for AI-powered tools"
            - "What are the risks of entering the fintech space?"
            - "Give me recommendations for scaling my business"
            
            **Features:**
            - Real-time AI consultation
            - Market analysis and insights
            - Competitor analysis
            - Risk assessment
            - Strategic recommendations
            """)
        
        with st.expander("🛠️ Troubleshooting"):
            st.markdown("""
            **Common Issues:**
            - **API Not Connected**: Check your .env file and API keys
            - **Slow Responses**: Try reducing max tokens or using a faster model
            - **Errors**: Clear chat and try again, or check the logs
            
            **Tips:**
            - Be specific in your questions for better results
            - Use the quick action buttons for structured analysis
            - Review the configuration settings if needed
            """)
    
    def _render_about_section(self):
        """Render about information."""
        st.markdown(f"""
        **Version:** 1.0.0  
        **Model:** {config.openai_model}  
        **Max Tokens:** {config.max_tokens}  
        **Temperature:** {config.temperature}
        """)
        
        st.markdown("Built with ❤️ using Streamlit and OpenAI")
    
    def _check_api_status(self) -> dict:
        """Check the status of API connections."""
        return {
            "openai": bool(config.openai_api_key and config.openai_api_key != "sk-placeholder"),
            "perplexity": bool(config.perplexity_api_key)
        }
    
    def _show_examples(self):
        """Show example questions in the main chat."""
        examples = [
            "I want to launch a SaaS startup for small businesses in the accounting space. What should I consider?",
            "Analyze the market opportunities for AI-powered customer service tools.",
            "What are the key risks of entering the fintech space as a startup?",
            "Give me strategic recommendations for scaling my e-commerce business.",
            "Conduct a competitor analysis for the project management software industry."
        ]
        
        st.session_state.show_examples = True
        st.session_state.example_questions = examples
        st.rerun()
    
    def _trigger_market_analysis(self):
        """Trigger market analysis prompt."""
        prompt = "Please conduct a comprehensive market analysis for my business idea. I need insights on market size, opportunities, trends, and competitive landscape."
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Add as if user typed it
        st.session_state.pending_message = prompt
        st.rerun()
    
    def _trigger_competitor_analysis(self):
        """Trigger competitor analysis prompt."""
        prompt = "I need a detailed competitor analysis for my industry. Please analyze the competitive landscape, key players, and market positioning opportunities."
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        st.session_state.pending_message = prompt
        st.rerun()
    
    def _trigger_risk_assessment(self):
        """Trigger risk assessment prompt."""
        prompt = "Please conduct a comprehensive risk assessment for my business. I need to understand potential threats, challenges, and mitigation strategies."
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        st.session_state.pending_message = prompt
        st.rerun()
    
    def _trigger_recommendations(self):
        """Trigger recommendations prompt."""
        prompt = "Based on my business context, please provide strategic recommendations with specific action items, timelines, and success metrics."
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        st.session_state.pending_message = prompt
        st.rerun()

# Global sidebar instance
sidebar = Sidebar()