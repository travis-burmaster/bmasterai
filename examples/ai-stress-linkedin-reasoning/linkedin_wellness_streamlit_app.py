"""
LinkedIn Chain of Thought Wellness Advisor - Streamlit Application

This Streamlit application demonstrates real-time BMasterAI reasoning transparency
by showing how Gemini thinks through LinkedIn profile analysis to provide personalized
stress reduction and happiness suggestions using chain of thought processing.
"""

import streamlit as st
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import google.generativeai as genai

# Import our LinkedIn Wellness Agent
from linkedin_wellness_agent_simple import LinkedInWellnessAgent, BMASTERAI_AVAILABLE

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    st.warning("python-dotenv not installed. Install it with: pip install python-dotenv")

def load_css():
    """Load custom CSS for better styling with wellness theme"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2e7d32;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #2e7d32, #4caf50);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .section-header {
        font-size: 1.5rem;
        color: #1b5e20;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #4caf50;
        padding-bottom: 0.5rem;
    }
    
    .chain-of-thought-step {
        background: linear-gradient(135deg, #e8f5e8, #f1f8e9);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        border-left: 4px solid #4caf50;
        font-family: 'Segoe UI', sans-serif;
        box-shadow: 0 2px 8px rgba(76, 175, 80, 0.1);
        animation: slideInLeft 0.5s ease-out;
    }
    
    .reasoning-step {
        background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
        padding: 1.2rem;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        border-left: 4px solid #2196f3;
        font-family: 'Segoe UI', sans-serif;
        animation: fadeIn 0.6s ease-in;
    }
    
    .stress-factor-card {
        background: linear-gradient(135deg, #fff3e0, #fce4ec);
        padding: 1.2rem;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        border-left: 4px solid #ff9800;
        box-shadow: 0 2px 6px rgba(255, 152, 0, 0.1);
    }
    
    .happiness-opportunity-card {
        background: linear-gradient(135deg, #f3e5f5, #e8f5e8);
        padding: 1.2rem;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        border-left: 4px solid #9c27b0;
        box-shadow: 0 2px 6px rgba(156, 39, 176, 0.1);
    }
    
    .recommendation-card {
        background: linear-gradient(135deg, #e8f5e8, #e3f2fd);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        border-left: 4px solid #4caf50;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.15);
        animation: slideInUp 0.7s ease-out;
    }
    
    .profile-summary-card {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
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
    
    .progress-container {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .step-indicator {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        border-radius: 0.5rem;
        font-size: 0.9rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .step-pending {
        background-color: #e9ecef;
        color: #6c757d;
    }
    
    .step-active {
        background: linear-gradient(135deg, #4caf50, #66bb6a);
        color: white;
        animation: pulse 2s infinite;
        box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
    }
    
    .step-complete {
        background: linear-gradient(135deg, #2e7d32, #388e3c);
        color: white;
        box-shadow: 0 2px 6px rgba(46, 125, 50, 0.2);
    }
    
    .wellness-metric {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem;
    }
    
    .priority-critical {
        border-left: 4px solid #f44336;
        background: linear-gradient(135deg, #ffebee, #fce4ec);
    }
    
    .priority-high {
        border-left: 4px solid #ff9800;
        background: linear-gradient(135deg, #fff3e0, #fce4ec);
    }
    
    .priority-medium {
        border-left: 4px solid #2196f3;
        background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-30px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.05); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    .chain-of-thought-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        background: linear-gradient(135deg, #fafafa, #f5f5f5);
        border-radius: 0.75rem;
        border: 1px solid #e0e0e0;
    }
    
    .reasoning-timestamp {
        font-size: 0.8rem;
        color: #666;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

def display_analysis_progress(current_step: str = "profile_extraction"):
    """Display the current analysis progress with wellness-themed indicators"""
    steps = [
        ("profile_extraction", "📊 Profile Analysis"),
        ("stress_identification", "⚠️ Stress Assessment"),
        ("happiness_assessment", "😊 Happiness Opportunities"),
        ("recommendation_generation", "💡 Wellness Recommendations"),
        ("complete", "✅ Analysis Complete")
    ]
    
    step_html = '<div class="progress-container"><h4>🧠 Chain of Thought Progress:</h4>'
    
    current_index = next((i for i, (step_id, _) in enumerate(steps) if step_id == current_step), 0)
    
    for i, (step_id, step_name) in enumerate(steps):
        if i < current_index:
            css_class = "step-complete"
        elif i == current_index:
            css_class = "step-active"
        else:
            css_class = "step-pending"
        
        step_html += f'<span class="step-indicator {css_class}">{step_name}</span>'
    
    step_html += '</div>'
    st.markdown(step_html, unsafe_allow_html=True)

def display_chain_of_thought_updates(updates: List[Dict]):
    """Display chain of thought reasoning steps in real-time"""
    if not updates:
        st.info("🧠 Chain of thought reasoning will appear here as the analysis progresses...")
        return
    
    st.markdown("### 🧠 Real-Time Chain of Thought Reasoning")
    
    for update in updates:
        step_type = update.get('type', 'thinking')
        reasoning = update.get('reasoning', '')
        conclusion = update.get('conclusion', '')
        timestamp = update.get('timestamp', '')
        confidence = update.get('confidence', 0.8)
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%H:%M:%S")
        except:
            formatted_time = "00:00:00"
        
        # Create reasoning step display
        st.markdown(f"""
        <div class="chain-of-thought-step">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong>🧠 {step_type.replace('_', ' ').title()}</strong>
                <span class="reasoning-timestamp">⏰ {formatted_time} | Confidence: {confidence:.1%}</span>
            </div>
            <div style="margin-bottom: 0.5rem;">
                <strong>Reasoning:</strong> {reasoning}
            </div>
            {f'<div><strong>Conclusion:</strong> {conclusion}</div>' if conclusion else ''}
        </div>
        """, unsafe_allow_html=True)

def display_profile_summary(profile_summary: Dict):
    """Display LinkedIn profile summary"""
    if not profile_summary:
        return
    
    st.markdown("### 👤 Profile Summary")
    
    # Use Streamlit components for better display
    with st.container():
        st.markdown(f"#### {profile_summary.get('name', 'N/A')}")
        
        # Handle current role display better
        current_title = profile_summary.get('current_position', '')
        current_company = profile_summary.get('current_company', '')
        headline = profile_summary.get('headline', '')
        
        if current_title and current_company:
            st.markdown(f"**Current Role:** {current_title} at {current_company}")
        elif current_title:
            st.markdown(f"**Current Role:** {current_title}")
        elif headline:
            st.markdown(f"**Professional Focus:** {headline}")
        
        st.markdown(f"**Location:** {profile_summary.get('location', 'N/A')}")
        
        # Show metrics in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Work Experiences", profile_summary.get('experience_count', 0))
        with col2:
            st.metric("Skills Listed", profile_summary.get('skills_count', 0))
        with col3:
            st.metric("Analysis Factors", profile_summary.get('total_factors', 0))
        
        # Show LinkedIn URL if available
        if profile_summary.get('linkedin_url'):
            st.markdown(f"**Profile:** [View on LinkedIn]({profile_summary.get('linkedin_url')})")
        
        st.markdown("---")

def display_stress_factors(stress_factors: List[Dict]):
    """Display identified stress factors"""
    if not stress_factors:
        st.info("✅ No significant stress factors identified in the profile analysis.")
        return
    
    st.markdown("### ⚠️ Identified Stress Factors")
    
    for factor in stress_factors:
        severity_color = {
            'High': '#f44336',
            'Medium': '#ff9800', 
            'Low': '#4caf50'
        }.get(factor.get('severity', 'Medium'), '#ff9800')
        
        st.markdown(f"""
        <div class="stress-factor-card" style="border-left-color: {severity_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <h4 style="margin: 0; color: {severity_color};">{factor.get('category', 'Stress Factor')}</h4>
                <span style="background: {severity_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem;">
                    {factor.get('severity', 'Medium')} Severity
                </span>
            </div>
            <p><strong>Description:</strong> {factor.get('description', 'N/A')}</p>
            <p><strong>Reasoning:</strong> {factor.get('reasoning', 'N/A')}</p>
            <p><strong>Potential Impact:</strong> {factor.get('impact', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

def display_happiness_opportunities(opportunities: List[Dict]):
    """Display happiness enhancement opportunities"""
    if not opportunities:
        st.info("🔍 No specific happiness opportunities identified. General wellness recommendations will be provided.")
        return
    
    st.markdown("### 😊 Happiness Enhancement Opportunities")
    
    for opportunity in opportunities:
        priority_color = {
            'High': '#4caf50',
            'Medium': '#2196f3',
            'Low': '#9e9e9e'
        }.get(opportunity.get('priority', 'Medium'), '#2196f3')
        
        # Use Streamlit's native components
        with st.container():
            # Header with priority badge
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"#### {opportunity.get('title', 'Opportunity')}")
            with col2:
                priority = opportunity.get('priority', 'Medium')
                st.markdown(f"""
                <div style="text-align: right;">
                    <span style="background: {priority_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem;">
                        {priority} Priority
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            # Basic info
            st.markdown(f"**Category:** {opportunity.get('category', 'N/A')}")
            st.markdown(f"**Description:** {opportunity.get('description', 'N/A')}")
            st.markdown(f"**Reasoning:** {opportunity.get('reasoning', 'N/A')}")
            
            # Specific Actions
            if opportunity.get('specific_actions'):
                with st.expander("📋 Specific Actions"):
                    for action in opportunity.get('specific_actions', []):
                        st.markdown(f"• {action}")
            
            st.markdown("---")

def display_recommendations(recommendations: List[Dict]):
    """Display personalized wellness recommendations"""
    if not recommendations:
        st.info("📝 No specific recommendations generated. Please try the analysis again.")
        return
    
    st.markdown("### 💡 Personalized Wellness Recommendations")
    
    for i, rec in enumerate(recommendations, 1):
        # Use Streamlit's native components instead of raw HTML
        with st.container():
            # Header with priority badges
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"#### {i}. {rec.get('title', 'Recommendation')}")
            with col2:
                priority = rec.get('priority', 'Medium')
                timeframe = rec.get('timeframe', 'N/A')
                st.markdown(f"""
                <div style="text-align: right;">
                    <span style="background: #4caf50; color: white; padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem; margin-right: 0.5rem;">
                        {priority} Priority
                    </span>
                    <span style="background: #2196f3; color: white; padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem;">
                        {timeframe}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            # Basic info
            st.markdown(f"**Description:** {rec.get('description', 'N/A')}")
            st.markdown(f"**Reasoning:** {rec.get('reasoning', 'N/A')}")
            
            # Specific Steps
            if rec.get('specific_steps'):
                with st.expander("📋 Specific Steps"):
                    for step in rec.get('specific_steps', []):
                        step_num = step.get('step', 'N/A')
                        action = step.get('action', 'N/A')
                        timeline = step.get('timeline', 'N/A')
                        reasoning = step.get('reasoning', 'N/A')
                        
                        st.markdown(f"""
                        <div style="margin: 0.5rem 0; padding: 0.5rem; background: rgba(76, 175, 80, 0.1); border-radius: 0.25rem; border-left: 3px solid #4caf50;">
                            <strong>Step {step_num}:</strong> {action}<br>
                            <small><strong>Timeline:</strong> {timeline}</small><br>
                            <small><strong>Reasoning:</strong> {reasoning}</small>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Expected Outcomes
            if rec.get('expected_outcomes'):
                with st.expander("🎯 Expected Outcomes"):
                    for outcome in rec.get('expected_outcomes', []):
                        st.markdown(f"• {outcome}")
            
            # Success Metrics
            if rec.get('success_metrics'):
                with st.expander("📊 Success Metrics"):
                    for metric in rec.get('success_metrics', []):
                        st.markdown(f"• {metric}")
            
            st.markdown("---")

def main():
    """Main Streamlit application focused on chain of thought wellness analysis"""
    st.set_page_config(
        page_title="LinkedIn Chain of Thought Wellness Advisor",
        page_icon="🧠💚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    load_css()
    
    # Header
    st.markdown('<div class="main-header">🧠💚 LinkedIn Chain of Thought Wellness Advisor</div>', unsafe_allow_html=True)
    st.markdown("**Personalized stress reduction and happiness suggestions with transparent AI reasoning**")
    st.markdown("---")
    
    # Check BMasterAI availability
    if not BMASTERAI_AVAILABLE:
        st.warning("⚠️ BMasterAI library not found. Chain of thought transparency will be limited. Install with: `pip install bmasterai`")
    
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
        
        if not gemini_api_key:
            st.error("Please provide a Gemini API key to continue")
            st.stop()
        
        # Tavily API Key
        env_tavily_key = os.getenv("TAVILY_API_KEY")
        if env_tavily_key:
            st.success("✅ Tavily API key loaded from environment")
            tavily_api_key = env_tavily_key
        else:
            st.warning("⚠️ No Tavily API key found in environment")
            tavily_api_key = st.text_input(
                "Enter your Tavily API Key:",
                type="password",
                help="Get your API key from Tavily: https://tavily.com"
            )
        
        if not tavily_api_key:
            st.error("Please provide a Tavily API key to enable LinkedIn profile searching")
            st.stop()
        
        st.markdown("---")
        
        # BMasterAI Configuration
        st.header("🔧 BMasterAI Setup")
        
        if BMASTERAI_AVAILABLE:
            if st.button("Initialize BMasterAI Logging"):
                try:
                    from bmasterai import configure_logging, LogLevel
                    configure_logging(
                        log_level=LogLevel.DEBUG,
                        enable_console=True,
                        enable_reasoning_logs=True,
                        reasoning_log_file="linkedin_wellness_reasoning.jsonl"
                    )
                    st.success("✅ BMasterAI logging configured!")
                except Exception as e:
                    st.error(f"❌ Error configuring BMasterAI: {str(e)}")
        else:
            st.error("❌ BMasterAI not available")
        
        st.markdown("---")
        st.header("📋 Analysis Process")
        st.markdown("""
        **Chain of Thought Flow:**
        1. 📊 **Profile Analysis** - Extract LinkedIn data
        2. ⚠️ **Stress Assessment** - Identify stress factors
        3. 😊 **Happiness Opportunities** - Find enhancement areas
        4. 💡 **Wellness Recommendations** - Generate personalized suggestions
        5. ✅ **Complete Analysis** - Present actionable insights
        """)
    
    # Initialize session state
    if 'wellness_agent' not in st.session_state:
        try:
            st.session_state.wellness_agent = LinkedInWellnessAgent(
                "linkedin-wellness-advisor", 
                gemini_api_key,
                tavily_api_key
            )
        except Exception as e:
            st.error(f"Failed to initialize wellness agent: {str(e)}")
            st.stop()
    
    if 'chain_of_thought_updates' not in st.session_state:
        st.session_state.chain_of_thought_updates = []
    
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    
    # Main content with tabs
    tab1, tab2, tab3 = st.tabs([
        "🔍 Profile Analysis", 
        "💡 Wellness Results", 
        "📊 Reasoning Logs"
    ])
    
    with tab1:
        st.markdown("### 🔍 LinkedIn Profile Analysis")
        st.write("Enter a LinkedIn username to analyze for personalized wellness recommendations.")
        
        # Profile input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            username_input = st.text_input(
                "LinkedIn Username:",
                placeholder="e.g., satyanadella, jeffweiner08, adamselipsky",
                help="Enter the LinkedIn username (the part after linkedin.com/in/)"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            analyze_button = st.button("🚀 Analyze Profile", type="primary")
        
        # Example profiles
        # st.markdown("**Example profiles to try:**")
        # example_cols = st.columns(3)
        
        # with example_cols[0]:
        #     if st.button("👨‍💼 satyanadella", help="Microsoft CEO"):
        #         username_input = "satyanadella"
        #         st.rerun()
        
        # with example_cols[1]:
        #     if st.button("👨‍💻 jeffweiner08", help="Former LinkedIn CEO"):
        #         username_input = "jeffweiner08"
        #         st.rerun()
        
        # with example_cols[2]:
        #     if st.button("👨‍🔬 adamselipsky", help="AWS CEO"):
        #         username_input = "adamselipsky"
        #         st.rerun()
        
        # Privacy notice
        st.info("🔍 **Real LinkedIn Data:** This application uses Tavily search API to find LinkedIn profiles and web scraping to extract public profile information.")
        st.info("🔒 **Privacy Notice:** This tool only analyzes publicly available LinkedIn profile information. No private data is accessed or stored.")
        
        # Analysis trigger
        if analyze_button and username_input.strip():
            # Clear previous results
            st.session_state.chain_of_thought_updates = []
            st.session_state.analysis_result = None
            
            # Set up real-time callback
            def update_callback(update_data):
                st.session_state.chain_of_thought_updates.append(update_data)
            
            st.session_state.wellness_agent.set_update_callback(update_callback)
            
            with st.spinner(f"🧠 Analyzing LinkedIn profile: {username_input}..."):
                try:
                    result = st.session_state.wellness_agent.analyze_linkedin_profile_for_wellness(username_input)
                    st.session_state.analysis_result = result
                    st.success("✅ Analysis completed! Results are displayed below.")
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
        
        elif analyze_button and not username_input.strip():
            st.warning("Please enter a LinkedIn username to analyze.")
        
        # Real-time Chain of Thought Display (directly in this tab)
        if st.session_state.chain_of_thought_updates or st.session_state.analysis_result:
            st.markdown("---")
            st.markdown("### 🧠 Real-Time Chain of Thought Reasoning")
            st.write("Watch the AI's complete thinking process as it analyzes the LinkedIn profile for wellness insights.")
            
            # Progress indicator
            if st.session_state.chain_of_thought_updates:
                # Determine current step based on updates
                current_step = "profile_extraction"
                if any(u['type'] in ['stress_factor_identification', 'career_transition_analysis'] for u in st.session_state.chain_of_thought_updates):
                    current_step = "stress_identification"
                if any(u['type'] in ['happiness_opportunity_identification', 'skill_development_opportunity'] for u in st.session_state.chain_of_thought_updates):
                    current_step = "happiness_assessment"
                if any(u['type'] in ['personalized_recommendation_generation', 'critical_recommendation_generation'] for u in st.session_state.chain_of_thought_updates):
                    current_step = "recommendation_generation"
                if any(u['type'] == 'analysis_complete' for u in st.session_state.chain_of_thought_updates):
                    current_step = "complete"
                
                display_analysis_progress(current_step)
            
            # Chain of thought display
            display_chain_of_thought_updates(st.session_state.chain_of_thought_updates)
            
            # Auto-refresh for real-time updates
            if st.session_state.chain_of_thought_updates and not any(u['type'] == 'analysis_complete' for u in st.session_state.chain_of_thought_updates):
                time.sleep(1)
                st.rerun()
        
        # Display analysis results directly in this tab
        if st.session_state.analysis_result:
            st.markdown("---")
            st.markdown("### 💡 Wellness Analysis Results")
            
            result = st.session_state.analysis_result
            
            # Display profile summary
            if result.get('profile_summary'):
                display_profile_summary(result['profile_summary'])
            
            # Display analysis in columns
            col1, col2 = st.columns(2)
            
            with col1:
                # Stress factors
                display_stress_factors(result.get('stress_factors', []))
            
            with col2:
                # Happiness opportunities
                display_happiness_opportunities(result.get('happiness_opportunities', []))
            
            # Recommendations (full width)
            display_recommendations(result.get('recommendations', []))
            
            # Analysis metadata
            metadata = result.get('analysis_metadata', {})
            if metadata:
                st.markdown("---")
                st.markdown("### 📊 Analysis Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Stress Factors", metadata.get('total_stress_factors', 0))
                
                with col2:
                    st.metric("Opportunities", metadata.get('total_opportunities', 0))
                
                with col3:
                    st.metric("Recommendations", metadata.get('total_recommendations', 0))
                
                with col4:
                    st.metric("High Priority", metadata.get('high_priority_recommendations', 0))
                
                if metadata.get('is_demo'):
                    st.info("ℹ️ This analysis used demo data. For real profile analysis, ensure the LinkedIn username is correct and the profile is public.")
    
    with tab2:
        st.markdown("### 💡 Detailed Wellness Results")
        
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            
            # Enhanced detailed view
            st.markdown("#### 📋 Complete Analysis Report")
            
            # Display profile summary
            if result.get('profile_summary'):
                display_profile_summary(result['profile_summary'])
            
            # Detailed stress analysis
            if result.get('stress_factors'):
                st.markdown("---")
                st.markdown("#### ⚠️ Detailed Stress Factor Analysis")
                for i, factor in enumerate(result['stress_factors'], 1):
                    with st.expander(f"Stress Factor {i}: {factor.get('category', 'Unknown')} - {factor.get('severity', 'Unknown')} Severity"):
                        st.write(f"**Description:** {factor.get('description', 'N/A')}")
                        st.write(f"**Reasoning:** {factor.get('reasoning', 'N/A')}")
                        st.write(f"**Impact:** {factor.get('impact', 'N/A')}")
            
            # Detailed opportunities analysis
            if result.get('happiness_opportunities'):
                st.markdown("---")
                st.markdown("#### 😊 Detailed Opportunity Analysis")
                for i, opp in enumerate(result['happiness_opportunities'], 1):
                    with st.expander(f"Opportunity {i}: {opp.get('title', 'Unknown')} - {opp.get('priority', 'Unknown')} Priority"):
                        st.write(f"**Category:** {opp.get('category', 'N/A')}")
                        st.write(f"**Description:** {opp.get('description', 'N/A')}")
                        st.write(f"**Reasoning:** {opp.get('reasoning', 'N/A')}")
                        if opp.get('specific_actions'):
                            st.write("**Specific Actions:**")
                            for action in opp['specific_actions']:
                                st.write(f"• {action}")
            
            # Detailed recommendations
            if result.get('recommendations'):
                st.markdown("---")
                st.markdown("#### 💡 Detailed Recommendations")
                for i, rec in enumerate(result['recommendations'], 1):
                    with st.expander(f"Recommendation {i}: {rec.get('title', 'Unknown')} - {rec.get('priority', 'Unknown')} Priority"):
                        st.write(f"**Description:** {rec.get('description', 'N/A')}")
                        st.write(f"**Timeframe:** {rec.get('timeframe', 'N/A')}")
                        st.write(f"**Reasoning:** {rec.get('reasoning', 'N/A')}")
                        
                        if rec.get('specific_steps'):
                            st.write("**Detailed Steps:**")
                            for step in rec['specific_steps']:
                                st.write(f"**Step {step.get('step')}:** {step.get('action')}")
                                if step.get('timeline'):
                                    st.write(f"  - *Timeline:* {step.get('timeline')}")
                                if step.get('reasoning'):
                                    st.write(f"  - *Reasoning:* {step.get('reasoning')}")
                        
                        if rec.get('expected_outcomes'):
                            st.write("**Expected Outcomes:**")
                            for outcome in rec['expected_outcomes']:
                                st.write(f"• {outcome}")
                        
                        if rec.get('success_metrics'):
                            st.write("**Success Metrics:**")
                            for metric in rec['success_metrics']:
                                st.write(f"• {metric}")
        
        else:
            st.info("🔍 No analysis results yet. Please analyze a LinkedIn profile in the Profile Analysis tab.")
    
    with tab3:
        st.markdown("### 📊 BMasterAI Reasoning Logs & Analytics")
        
        if BMASTERAI_AVAILABLE:
            # Display agent statistics
            if st.button("📈 Show Agent Statistics"):
                try:
                    stats = st.session_state.wellness_agent.get_agent_stats()
                    
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
            st.markdown("### 📥 Export Reasoning Logs")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Export as JSON"):
                    try:
                        json_logs = st.session_state.wellness_agent.export_reasoning_logs("json")
                        st.download_button(
                            label="⬇️ Download JSON Logs",
                            data=json_logs,
                            file_name=f"linkedin_wellness_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    except Exception as e:
                        st.error(f"Error exporting JSON: {str(e)}")
            
            with col2:
                if st.button("📝 Export as Markdown"):
                    try:
                        markdown_logs = st.session_state.wellness_agent.export_reasoning_logs("markdown")
                        st.download_button(
                            label="⬇️ Download Markdown Logs",
                            data=markdown_logs,
                            file_name=f"linkedin_wellness_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown"
                        )
                    except Exception as e:
                        st.error(f"Error exporting Markdown: {str(e)}")
        
        else:
            st.warning("⚠️ BMasterAI not available. Install BMasterAI to access detailed reasoning logs and analytics.")
            st.code("pip install bmasterai")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #7f8c8d; margin-top: 2rem;">
        <p>🧠💚 Powered by Gemini 2.0 Flash + BMasterAI + LinkedIn APIs | Built with Streamlit</p>
        <p><small>Real-time chain of thought reasoning for personalized wellness recommendations based on LinkedIn profile analysis.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

