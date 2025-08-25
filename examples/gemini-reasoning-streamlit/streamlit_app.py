"""
Enhanced Streamlit App for Gemini 2.5 Pro + BMasterAI + Tavily + Firecrawl

This Streamlit application demonstrates real-time BMasterAI reasoning transparency
by showing how Gemini thinks through complex tasks like finding AI podcast influencers
using Tavily API for search and Firecrawl API for email extraction.
"""

import streamlit as st
import os
import json
import glob
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import google.generativeai as genai

# Import BMasterAI components
try:
    from bmasterai import configure_logging, LogLevel
    BMASTERAI_AVAILABLE = True
except ImportError:
    BMASTERAI_AVAILABLE = False
    st.error("BMasterAI library not found. Please install it with: pip install bmasterai")

# Import our enhanced Gemini reasoning agent
from gemini_reasoning_app import GeminiReasoningAgent

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    st.warning("python-dotenv not installed. Install it with: pip install python-dotenv")

def load_css():
    """Load custom CSS for better styling"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    .thinking-step {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #2ecc71;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        animation: fadeIn 0.5s ease-in;
    }
    
    .tavily-result {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #f39c12;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        animation: slideIn 0.5s ease-in;
    }
    
    .firecrawl-result {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #e74c3c;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        animation: slideIn 0.5s ease-in;
    }
    
    .final-result {
        background-color: #d4edda;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
        animation: slideIn 0.8s ease-in;
    }
    
    .error-message {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #dc3545;
        color: #721c24;
    }
    
    .process-step {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .api-status {
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    
    .api-available {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .api-demo {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .influencer-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #6f42c1;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .real-time-log {
        max-height: 400px;
        overflow-y: auto;
        background-color: #2c3e50;
        color: #ecf0f1;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        margin: 1rem 0;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .progress-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .step-indicator {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .step-pending {
        background-color: #e9ecef;
        color: #6c757d;
    }
    
    .step-active {
        background-color: #007bff;
        color: white;
        animation: pulse 1s infinite;
    }
    
    .step-complete {
        background-color: #28a745;
        color: white;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)

def display_process_steps(current_step: str = "planning"):
    """Display the current process step indicators"""
    steps = [
        ("planning", "🧠 Planning"),
        ("thinking", "💭 Thinking"),
        ("tavily", "🌐 Tavily Search"),
        ("firecrawl", "🔍 Firecrawl Extract"),
        ("analysis", "📊 Analysis"),
        ("complete", "✅ Complete")
    ]
    
    step_html = '<div class="progress-container"><h4>Process Progress:</h4>'
    
    for step_id, step_name in steps:
        if step_id == current_step:
            css_class = "step-active"
        elif steps.index((step_id, step_name)) < steps.index((current_step, next(name for sid, name in steps if sid == current_step))):
            css_class = "step-complete"
        else:
            css_class = "step-pending"
        
        step_html += f'<span class="step-indicator {css_class}">{step_name}</span>'
    
    step_html += '</div>'
    st.markdown(step_html, unsafe_allow_html=True)

def create_real_time_log_container():
    """Create a container for real-time logging updates"""
    if 'log_messages' not in st.session_state:
        st.session_state.log_messages = []
    
    log_container = st.empty()
    return log_container

def update_real_time_log(container, update_data: Dict):
    """Update the real-time log display"""
    if 'log_messages' not in st.session_state:
        st.session_state.log_messages = []
    
    # Add new message
    timestamp = datetime.now().strftime("%H:%M:%S")
    update_type = update_data.get('type', 'info')
    content = update_data.get('content', '')
    
    st.session_state.log_messages.append({
        'timestamp': timestamp,
        'type': update_type,
        'content': content,
        'data': update_data.get('data')
    })
    
    # Keep only last 20 messages
    if len(st.session_state.log_messages) > 20:
        st.session_state.log_messages = st.session_state.log_messages[-20:]
    
    # Update display
    log_html = '<div class="real-time-log">'
    for msg in st.session_state.log_messages:
        log_html += f'<div>[{msg["timestamp"]}] <strong>{msg["type"].upper()}:</strong> {msg["content"]}</div>'
    log_html += '</div>'
    
    container.markdown(log_html, unsafe_allow_html=True)

def display_thinking_steps(updates: List[Dict]):
    """Display thinking steps in real-time"""
    st.markdown("### 🧠 BMasterAI Thinking Process")
    
    for update in updates:
        if update['type'] == 'thinking':
            st.markdown(f"""
            <div class="thinking-step">
                <strong>💭 Thinking:</strong> {update['content']}
                <br><small>⏰ {update.get('timestamp', '')}</small>
            </div>
            """, unsafe_allow_html=True)

def display_tavily_results(updates: List[Dict]):
    """Display Tavily search results"""
    tavily_updates = [u for u in updates if u['type'] in ['tavily_search', 'tavily_result']]
    
    if tavily_updates:
        st.markdown("### 🌐 Tavily Search Results")
        
        for update in tavily_updates:
            if update['type'] == 'tavily_search':
                st.markdown(f"""
                <div class="tavily-result">
                    <strong>🔍 Search:</strong> {update['content']}
                </div>
                """, unsafe_allow_html=True)
            elif update['type'] == 'tavily_result':
                data = update.get('data', [])
                st.markdown(f"""
                <div class="tavily-result">
                    <strong>📊 Results:</strong> {update['content']}
                    <br><small>Found {len(data) if isinstance(data, list) else 0} results</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Show first few results
                if isinstance(data, list) and data:
                    with st.expander(f"View {len(data)} search results", expanded=False):
                        for i, result in enumerate(data[:3]):  # Show first 3
                            st.write(f"**{i+1}.** {result.get('title', 'No title')}")
                            st.write(f"URL: {result.get('url', 'No URL')}")
                            st.write(f"Content: {result.get('content', 'No content')[:200]}...")
                            st.write("---")

def display_firecrawl_results(updates: List[Dict]):
    """Display Firecrawl extraction results"""
    firecrawl_updates = [u for u in updates if u['type'] in ['firecrawl_crawl', 'firecrawl_result']]
    
    if firecrawl_updates:
        st.markdown("### 🔍 Firecrawl Email Extraction")
        
        for update in firecrawl_updates:
            if update['type'] == 'firecrawl_crawl':
                st.markdown(f"""
                <div class="firecrawl-result">
                    <strong>🕷️ Crawling:</strong> {update['content']}
                </div>
                """, unsafe_allow_html=True)
            elif update['type'] == 'firecrawl_result':
                data = update.get('data')
                st.markdown(f"""
                <div class="firecrawl-result">
                    <strong>📧 Extraction:</strong> {update['content']}
                </div>
                """, unsafe_allow_html=True)
                
                # Show extracted data
                if data and isinstance(data, dict):
                    emails = data.get('emails', [])
                    if emails:
                        with st.expander(f"📧 Found {len(emails)} email(s)", expanded=False):
                            for email in emails:
                                st.write(f"• {email}")
                            
                            extracted_info = data.get('extracted_info', {})
                            if extracted_info:
                                st.write("**Additional Info:**")
                                for key, value in extracted_info.items():
                                    st.write(f"• {key}: {value}")

def main():
    """Main Streamlit application with real-time BMasterAI logging"""
    st.set_page_config(
        page_title="Gemini + BMasterAI + Tavily + Firecrawl",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    load_css()
    
    # Header
    st.markdown('<div class="main-header">🧠 Gemini + BMasterAI + Tavily + Firecrawl</div>', unsafe_allow_html=True)
    st.markdown("**AI Podcast Influencer Research with Real-Time Reasoning Transparency**")
    st.markdown("---")
    
    # Check BMasterAI availability
    if not BMASTERAI_AVAILABLE:
        st.error("❌ BMasterAI library is required for this application. Please install it first.")
        st.code("pip install bmasterai")
        st.stop()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔑 API Configuration")
        
        # Gemini API Key
        env_gemini_key = os.getenv("GEMINI_API_KEY")
        if env_gemini_key:
            st.success("✅ Gemini API key loaded from environment")
            gemini_api_key = env_gemini_key
        else:
            st.warning("⚠️ No Gemini API key found in environment")
            gemini_api_key = st.text_input(
                "Enter your Gemini API Key:",
                type="password",
                help="Get your API key from Google AI Studio: https://makersuite.google.com/app/apikey"
            )
        
        # Tavily API Key
        env_tavily_key = os.getenv("TAVILY_API_KEY")
        if env_tavily_key:
            st.markdown('<div class="api-status api-available">✅ Tavily API key loaded</div>', unsafe_allow_html=True)
            tavily_api_key = env_tavily_key
        else:
            st.markdown('<div class="api-status api-demo">ℹ️ No Tavily API key found</div>', unsafe_allow_html=True)
            tavily_api_key = st.text_input(
                "Enter your Tavily API Key (optional):",
                type="password",
                help="Get your API key from Tavily: https://tavily.com/"
            )
        
        # Firecrawl API Key
        env_firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        if env_firecrawl_key:
            st.markdown('<div class="api-status api-available">✅ Firecrawl API key loaded</div>', unsafe_allow_html=True)
            firecrawl_api_key = env_firecrawl_key
        else:
            st.markdown('<div class="api-status api-demo">ℹ️ No Firecrawl API key found</div>', unsafe_allow_html=True)
            firecrawl_api_key = st.text_input(
                "Enter your Firecrawl API Key (optional):",
                type="password",
                help="Get your API key from Firecrawl: https://firecrawl.dev/"
            )
        
        if not gemini_api_key:
            st.error("Please provide a Gemini API key to continue")
            st.stop()
        
        st.markdown("---")
        
        # BMasterAI Configuration
        st.header("🔧 BMasterAI Setup")
        
        if st.button("Initialize BMasterAI Logging"):
            try:
                configure_logging(
                    log_level=LogLevel.DEBUG,
                    enable_console=True,
                    enable_reasoning_logs=True,
                    reasoning_log_file="gemini_tavily_firecrawl_reasoning.jsonl"
                )
                st.success("✅ BMasterAI logging configured!")
            except Exception as e:
                st.error(f"❌ Error configuring BMasterAI: {str(e)}")
        
        st.markdown("---")
        st.header("📋 Process Overview")
        st.markdown("""
        **Real-Time Process Flow:**
        1. 🧠 **BMasterAI Thinking** - See Gemini's reasoning
        2. 🌐 **Tavily Search** - Find podcast websites
        3. 🔍 **Firecrawl Extract** - Get email addresses
        4. 📊 **Analysis** - Structure final results
        5. ✅ **Complete** - Present verified contacts
        """)
    
    # Initialize session state for real-time updates
    if 'updates' not in st.session_state:
        st.session_state.updates = []
    
    if 'agent' not in st.session_state:
        try:
            st.session_state.agent = GeminiReasoningAgent(
                "streamlit-gemini-tavily-firecrawl-agent", 
                gemini_api_key, 
                tavily_api_key if tavily_api_key else None,
                firecrawl_api_key if firecrawl_api_key else None
            )
        except Exception as e:
            st.error(f"Failed to initialize Gemini agent: {str(e)}")
            st.stop()
    
    # Main content
    st.markdown('<div class="section-header">🎙️ AI Podcast Influencer Search with Real-Time Reasoning</div>', unsafe_allow_html=True)
    st.write("Watch Gemini's complete thinking process as it searches for AI podcast influencers using Tavily + Firecrawl APIs.")
    
    # Search parameters
    col1, col2 = st.columns(2)
    
    with col1:
        target_count = st.number_input(
            "Number of influencers to find:",
            min_value=1,
            max_value=20,
            value=5,
            help="How many AI podcast influencers to search for"
        )
    
    with col2:
        focus_area = st.selectbox(
            "Focus area:",
            [
                "general AI",
                "machine learning and AI applications", 
                "AI research and academia",
                "AI in business and enterprise",
                "AI ethics and society",
                "computer vision and NLP",
                "robotics and autonomous systems"
            ],
            help="Specific area of AI to focus the search on"
        )
    
    # API status display
    api_status_col1, api_status_col2, api_status_col3 = st.columns(3)
    
    with api_status_col1:
        st.markdown('<div class="api-status api-available">🧠 Gemini: Ready</div>', unsafe_allow_html=True)
    
    with api_status_col2:
        if tavily_api_key:
            st.markdown('<div class="api-status api-available">🌐 Tavily: Live Search</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="api-status api-demo">🌐 Tavily: Demo Mode</div>', unsafe_allow_html=True)
    
    with api_status_col3:
        if firecrawl_api_key:
            st.markdown('<div class="api-status api-available">🔍 Firecrawl: Live Extract</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="api-status api-demo">🔍 Firecrawl: Demo Mode</div>', unsafe_allow_html=True)
    
    # Search button
    if st.button("🚀 Start AI Podcast Influencer Search", type="primary"):
        # Clear previous updates
        st.session_state.updates = []
        
        # Create containers for real-time updates
        progress_container = st.empty()
        thinking_container = st.empty()
        tavily_container = st.empty()
        firecrawl_container = st.empty()
        results_container = st.empty()
        
        # Set up real-time callback
        def update_callback(update_data):
            st.session_state.updates.append(update_data)
            
            # Update progress indicator
            current_step = "planning"
            if any(u['type'] == 'thinking' for u in st.session_state.updates):
                current_step = "thinking"
            if any(u['type'] in ['tavily_search', 'tavily_result'] for u in st.session_state.updates):
                current_step = "tavily"
            if any(u['type'] in ['firecrawl_crawl', 'firecrawl_result'] for u in st.session_state.updates):
                current_step = "firecrawl"
            if any(u['type'] == 'conclusion' for u in st.session_state.updates):
                current_step = "complete"
            
            with progress_container.container():
                display_process_steps(current_step)
            
            # Update thinking steps
            thinking_updates = [u for u in st.session_state.updates if u['type'] == 'thinking']
            if thinking_updates:
                with thinking_container.container():
                    display_thinking_steps(thinking_updates)
            
            # Update Tavily results
            tavily_updates = [u for u in st.session_state.updates if u['type'] in ['tavily_search', 'tavily_result']]
            if tavily_updates:
                with tavily_container.container():
                    display_tavily_results(tavily_updates)
            
            # Update Firecrawl results
            firecrawl_updates = [u for u in st.session_state.updates if u['type'] in ['firecrawl_crawl', 'firecrawl_result']]
            if firecrawl_updates:
                with firecrawl_container.container():
                    display_firecrawl_results(firecrawl_updates)
            
            # Update final results
            final_updates = [u for u in st.session_state.updates if u['type'] in ['final_results', 'conclusion']]
            if final_updates:
                with results_container.container():
                    st.markdown("### ✅ Final Results")
                    for update in final_updates:
                        if update['type'] == 'final_results':
                            data = update.get('data', [])
                            st.markdown(f"""
                            <div class="final-result">
                                <h4>🎯 {update['content']}</h4>
                                <p>Found {len(data) if isinstance(data, list) else 0} verified influencer profiles</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Display influencer cards
                            if isinstance(data, list):
                                for i, influencer in enumerate(data, 1):
                                    st.markdown(f"""
                                    <div class="influencer-card">
                                        <h4>{i}. {influencer.get('name', 'Unknown')}</h4>
                                        <p><strong>Podcast:</strong> {influencer.get('podcast', 'N/A')}</p>
                                        <p><strong>Email:</strong> {influencer.get('email', 'Not found')}</p>
                                        <p><strong>Website:</strong> {influencer.get('website', 'N/A')}</p>
                                        <p><strong>Focus:</strong> {influencer.get('focus_area', 'General AI')}</p>
                                        <p><strong>Guest Friendly:</strong> {influencer.get('guest_friendly', 'Unknown')}</p>
                                        <p><strong>Contact Confidence:</strong> {influencer.get('contact_confidence', 'N/A')}/10</p>
                                        <p><strong>Notes:</strong> {influencer.get('notes', 'No additional notes')}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                        elif update['type'] == 'conclusion':
                            st.markdown(f"""
                            <div class="final-result">
                                <h4>🎯 Process Complete</h4>
                                <p>{update['content']}</p>
                            </div>
                            """, unsafe_allow_html=True)
            
            # Handle errors
            error_updates = [u for u in st.session_state.updates if u['type'] == 'error']
            if error_updates:
                for error_update in error_updates:
                    st.markdown(f"""
                    <div class="error-message">
                        <strong>❌ Error:</strong> {error_update['content']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Set callback and run search
        st.session_state.agent.set_update_callback(update_callback)
        
        with st.spinner("🧠 Starting AI podcast influencer search with real-time reasoning..."):
            try:
                result = st.session_state.agent.search_ai_podcast_influencers_with_firecrawl(
                    target_count=target_count,
                    focus_area=focus_area
                )
                
                st.success("✅ Search completed with full BMasterAI + Tavily + Firecrawl integration!")
                
            except Exception as e:
                st.error(f"❌ Error during search: {str(e)}")
    
    # Additional tabs for other features
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎭 Sentiment Analysis", 
        "🧩 Problem Solving", 
        "❓ Query Processing", 
        "📊 Logs & Analytics"
    ])
    
    with tab1:
        st.markdown("### 🎭 Sentiment Analysis with Real-Time Thinking")
        
        text_input = st.text_area(
            "Enter text to analyze:",
            placeholder="e.g., I'm excited about the potential of AI podcasts to educate and inspire!",
            height=100
        )
        
        if st.button("Analyze Sentiment", key="sentiment"):
            if text_input.strip():
                sentiment_updates = []
                
                def sentiment_callback(update_data):
                    sentiment_updates.append(update_data)
                    if update_data['type'] == 'thinking':
                        st.markdown(f"""
                        <div class="thinking-step">
                            <strong>💭 Thinking:</strong> {update_data['content']}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.session_state.agent.set_update_callback(sentiment_callback)
                
                with st.spinner("Analyzing sentiment with real-time reasoning..."):
                    try:
                        result = st.session_state.agent.analyze_sentiment_with_context_manager(text_input)
                        st.success("✅ Sentiment analysis completed!")
                        st.write("**Result:**", result)
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
            else:
                st.warning("Please enter some text to analyze.")
    
    with tab2:
        st.markdown("### 🧩 Problem Solving with Chain of Thought")
        
        problem_input = st.text_area(
            "Enter a problem to solve:",
            placeholder="e.g., How can I effectively pitch myself as a guest on AI podcasts?",
            height=100
        )
        
        if st.button("Solve Problem", key="problem"):
            if problem_input.strip():
                problem_updates = []
                
                def problem_callback(update_data):
                    problem_updates.append(update_data)
                    if update_data['type'] == 'thinking':
                        st.markdown(f"""
                        <div class="thinking-step">
                            <strong>💭 Thinking:</strong> {update_data['content']}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.session_state.agent.set_update_callback(problem_callback)
                
                with st.spinner("Solving problem with chain of thought reasoning..."):
                    try:
                        result = st.session_state.agent.analyze_with_chain_of_thought(problem_input)
                        st.success("✅ Problem solved!")
                        st.write("**Solution:**", result)
                    except Exception as e:
                        st.error(f"Error during problem solving: {str(e)}")
            else:
                st.warning("Please enter a problem to solve.")
    
    with tab3:
        st.markdown("### ❓ Query Processing with Real-Time Logging")
        
        query_input = st.text_area(
            "Enter your query:",
            placeholder="e.g., What are the best strategies for getting booked on AI podcasts?",
            height=100
        )
        
        if st.button("Process Query", key="query"):
            if query_input.strip():
                query_updates = []
                
                def query_callback(update_data):
                    query_updates.append(update_data)
                    if update_data['type'] == 'thinking':
                        st.markdown(f"""
                        <div class="thinking-step">
                            <strong>💭 Thinking:</strong> {update_data['content']}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.session_state.agent.set_update_callback(query_callback)
                
                with st.spinner("Processing query with real-time reasoning..."):
                    try:
                        result = st.session_state.agent.process_with_decorator(
                            st.session_state.agent.agent_id, 
                            query_input
                        )
                        st.success("✅ Query processed!")
                        st.write("**Response:**", result)
                    except Exception as e:
                        st.error(f"Error during query processing: {str(e)}")
            else:
                st.warning("Please enter a query to process.")
    
    with tab4:
        st.markdown("### 📊 BMasterAI Logs & Analytics")
        
        # Display recent logs
        if st.button("Refresh Logs"):
            st.rerun()
        
        # Show agent statistics
        if st.button("Show Agent Statistics"):
            try:
                stats = st.session_state.agent.get_agent_stats()
                
                st.markdown("### 📈 Agent Statistics")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Events", stats.get('total_events', 0))
                
                with col2:
                    event_types = stats.get('event_types', {})
                    if event_types:
                        st.write("**Event Types:**")
                        for event_type, count in event_types.items():
                            st.write(f"• {event_type}: {count}")
                
            except Exception as e:
                st.error(f"Error getting statistics: {str(e)}")
        
        # Export functionality
        st.markdown("---")
        st.markdown("### 📥 Export BMasterAI Logs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export as JSON"):
                try:
                    json_logs = st.session_state.agent.export_reasoning_logs("json")
                    st.download_button(
                        label="Download JSON Logs",
                        data=json_logs,
                        file_name=f"bmasterai_tavily_firecrawl_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Error exporting JSON: {str(e)}")
        
        with col2:
            if st.button("Export as Markdown"):
                try:
                    markdown_logs = st.session_state.agent.export_reasoning_logs("markdown")
                    st.download_button(
                        label="Download Markdown Logs",
                        data=markdown_logs,
                        file_name=f"bmasterai_tavily_firecrawl_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
                except Exception as e:
                    st.error(f"Error exporting Markdown: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #7f8c8d; margin-top: 2rem;">
        <p>🧠 Powered by Gemini 2.5 Pro + BMasterAI + Tavily + Firecrawl | Built with Streamlit</p>
        <p><small>Real-time reasoning transparency for complex AI tasks with multi-API integrations.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

