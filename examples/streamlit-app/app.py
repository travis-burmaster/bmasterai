"""Main Streamlit application for the AI Business Consultant."""

import streamlit as st
import os
from config import config
from components.sidebar import sidebar
from components.chat_interface import chat_interface

# Page configuration
st.set_page_config(
    page_title=config.app_name,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stChat > div {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    
    .stChatMessage {
        background-color: blue;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stExpander {
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        margin: 10px 0;
    }
    
    .insight-card {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    .recommendation-card {
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    .risk-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    .error-card {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function."""
    
    # Check if API keys are configured
    if not config.openai_api_key or config.openai_api_key == "sk-placeholder":
        st.error("⚠️ OpenAI API key not configured. Please set up your .env file.")
        st.markdown("""
        **Setup Instructions:**
        1. Copy `.env.example` to `.env`
        2. Add your OpenAI API key to the `.env` file
        3. Restart the application
        
        **Required in .env file:**
        ```
        OPENAI_API_KEY=your_openai_api_key_here
        ```
        """)
        return
    
    # Render sidebar
    sidebar.render()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Header
        st.title(f"🤖 {config.agent_name}")
        st.markdown("*Your AI-powered business consultant for strategic insights and recommendations*")
        
        # Handle pending messages from sidebar
        if "pending_message" in st.session_state:
            pending_msg = st.session_state.pending_message
            del st.session_state.pending_message
            chat_interface.handle_user_input(pending_msg)
        
        # Show examples if requested
        if st.session_state.get("show_examples", False):
            st.markdown("### 💡 Example Questions")
            st.markdown("Click any example to start a conversation:")
            
            for i, example in enumerate(st.session_state.get("example_questions", [])):
                if st.button(f"📝 {example[:80]}{'...' if len(example) > 80 else ''}", key=f"example_{i}"):
                    chat_interface.handle_user_input(example)
                    st.session_state.show_examples = False
                    st.rerun()
            
            if st.button("❌ Close Examples"):
                st.session_state.show_examples = False
                st.rerun()
            
            st.markdown("---")
        
        # Chat interface
        chat_interface.render()
    
    with col2:
        # Quick stats or additional info
        st.markdown("### 📊 Quick Stats")
        
        # Display conversation stats
        message_count = len(st.session_state.get("messages", []))
        st.metric("Messages", message_count)
        
        # Display current analysis info
        if st.session_state.get("current_analysis"):
            analysis = st.session_state.current_analysis
            st.metric("Last Analysis", analysis.get("type", "None").replace("_", " ").title())
        
        # Usage tips
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Be specific in your questions
        - Ask for market analysis, competitor research, or risk assessment
        - Request strategic recommendations
        - Use the sidebar for quick actions
        """)
        
        # Recent insights
        if st.session_state.get("current_analysis"):
            st.markdown("### 🔍 Recent Insights")
            analysis = st.session_state.current_analysis
            
            if analysis.get("type") == "market_analysis":
                insights = analysis.get("insights", [])
                if insights:
                    st.markdown(f"**{len(insights)} insights found**")
                    for insight in insights[:3]:  # Show first 3
                        st.markdown(f"• {insight['category']}")
            
            elif analysis.get("type") == "recommendations":
                recommendations = analysis.get("recommendations", [])
                if recommendations:
                    st.markdown(f"**{len(recommendations)} recommendations**")
                    for rec in recommendations[:3]:  # Show first 3
                        st.markdown(f"• {rec.get('category', 'Recommendation')}")

if __name__ == "__main__":
    main()