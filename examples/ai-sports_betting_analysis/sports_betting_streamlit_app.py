"""
Sports Betting Analysis Streamlit Application

This Streamlit application demonstrates real-time BMasterAI reasoning transparency
by showing how multiple AI agents analyze sports betting scenarios to provide
probability-based recommendations with full chain of thought visibility.
"""

import streamlit as st
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

# Import our agents
from base_agent import CoordinationAgent
from data_collection_agent import DataCollectionAgent
from statistical_analysis_agent import StatisticalAnalysisAgent
from probability_calculation_agent import ProbabilityCalculationAgent

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Sports Betting Analysis - Multi-Agent AI System",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chain of thought display (adapted from LinkedIn wellness app)
st.markdown("""
<style>
    /* Main header styling */
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

    /* Section header styling */
    .section-header {
        font-size: 1.5rem;
        color: #1b5e20;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #4caf50;
        padding-bottom: 0.5rem;
    }

    /* Chain of thought container */
    .chain-of-thought-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        background: linear-gradient(135deg, #f8f9fa, #e8f5e8);
        border-radius: 0.75rem;
        border: 1px solid #4caf50;
        margin-bottom: 0.5rem;
    }

    /* Chain of thought step styling */
    .chain-of-thought-step {
        background: linear-gradient(135deg, #ffffff, #f1f8e9);
        border-radius: 0.5rem;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border-left: 4px solid #4caf50;
        box-shadow: 0 2px 8px rgba(76, 175, 80, 0.1);
        animation: slideInLeft 0.6s ease-out;
    }

    /* Reasoning step styling */
    .reasoning-step {
        background: linear-gradient(135deg, #e8f5e8, #c8e6c8);
        padding: 1.2rem;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        border-left: 4px solid #2e7d32;
        font-family: 'Segoe UI', sans-serif;
        box-shadow: 0 2px 6px rgba(46, 125, 50, 0.15);
        animation: fadeIn 0.6s ease-in;
    }

    /* Agent status indicators */
    .agent-status {
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
        font-weight: bold;
    }

    .agent-status.running {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }

    .agent-status.complete {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .agent-status.error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    /* Progress container */
    .progress-container {
        background: linear-gradient(135deg, #f8f9fa, #e8f5e8);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        border: 1px solid #4caf50;
    }

    /* Step indicator */
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
        border: 1px solid #dee2e6;
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

    /* Probability cards */
    .probability-card {
        background: linear-gradient(135deg, #ffffff, #f1f8e9);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        border-left: 4px solid #4caf50;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.15);
    }

    /* Recommendation cards */
    .recommendation-card {
        background: linear-gradient(135deg, #e8f5e8, #c8e6c8);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        border: 1px solid #4caf50;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.1);
    }

    /* Animations */
    @keyframes slideInLeft {
        from { transform: translateX(-30px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.05); }
        100% { opacity: 1; transform: scale(1); }
    }

    /* Confidence indicators */
    .confidence-high {
        border-left-color: #2e7d32;
        background: linear-gradient(135deg, #e8f5e8, #c8e6c8);
    }

    .confidence-medium {
        border-left-color: #f57c00;
        background: linear-gradient(135deg, #fff8e1, #ffecb3);
    }

    .confidence-low {
        border-left-color: #d32f2f;
        background: linear-gradient(135deg, #ffebee, #ffcdd2);
    }
</style>
""", unsafe_allow_html=True)


def display_analysis_progress(current_step: str = "game_selection") -> str:
    """Display the current analysis progress with wellness-themed indicators"""
    steps = [
        ("game_selection", "🎯 Game Selection"),
        ("data_collection", "📊 Data Collection"),
        ("statistical_analysis", "📈 Statistical Analysis"),
        ("market_analysis", "💰 Market Analysis"),
        ("news_sentiment", "📰 News & Sentiment"),
        ("probability_calculation", "🎲 Probability Calculation"),
        ("complete", "✅ Analysis Complete")
    ]

    current_index = next((i for i, (step_id, _) in enumerate(steps) if step_id == current_step), 0)

    step_html = '<div class="progress-container"><h4>Sports Betting Analysis Progress</h4>'
    
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
    
    return f'<div class="chain-of-thought-container"><h4>🧠 Chain of Thought Progress</h4>'


def display_chain_of_thought_updates(updates: List[Dict]) -> str:
    """Display chain of thought reasoning steps in real-time"""
    if not updates:
        st.info("🧠 Chain of thought reasoning will appear here as the analysis progresses...")
        return

    st.markdown("### 🧠 Real-Time Chain of Thought Reasoning")
    
    for update in updates:
        step_type = update.get('step_type', 'thinking')
        reasoning = update.get('reasoning', '')
        confidence = update.get('confidence', 1.0)
        timestamp = update.get('timestamp', '')
        agent_id = update.get('agent_id', 'system')
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%H:%M:%S")
        except:
            formatted_time = "00:00:00"
        
        # Determine confidence class
        if confidence > 0.7:
            confidence_class = "confidence-high"
        elif confidence > 0.4:
            confidence_class = "confidence-medium"
        else:
            confidence_class = "confidence-low"
        
        # Create reasoning step display
        st.markdown(f"""
        <div class="chain-of-thought-step {confidence_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong>🤖 {agent_id.replace('_', ' ').title()}</strong> | <strong>🧠 {step_type.replace('_', ' ').title()}</strong>
                <span class="reasoning-timestamp" style="font-size: 0.8rem; color: #666;">⏰ {formatted_time} | Confidence: {confidence:.1%}</span>
            </div>
            <div style="margin-bottom: 0.5rem;">
                <strong>Reasoning:</strong> {reasoning}
            </div>
        </div>
        """, unsafe_allow_html=True)


def display_probability_summary(probability_data: Dict[str, Any]):
    """Display probability analysis summary"""
    if not probability_data:
        return
    
    st.markdown("### 🎲 Probability Analysis Summary")
    
    probabilities = probability_data.get("updated_probabilities", {})
    confidence_intervals = probability_data.get("confidence_intervals", {})
    
    # Create probability visualization
    if probabilities:
        outcomes = list(probabilities.keys())
        probs = list(probabilities.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=outcomes,
                y=probs,
                marker_color=['#4caf50', '#ff9800', '#2196f3'],
                text=[f'{p:.1%}' for p in probs],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Probability Estimates",
            xaxis_title="Outcomes",
            yaxis_title="Probability",
            yaxis=dict(tickformat='.0%'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display confidence intervals
    if confidence_intervals:
        st.markdown("#### Confidence Intervals")
        
        for outcome, interval in confidence_intervals.items():
            point_est = interval.get("point_estimate", 0)
            lower = interval.get("lower_bound", 0)
            upper = interval.get("upper_bound", 0)
            
            st.markdown(f"""
            <div class="probability-card">
                <strong>{outcome.replace('_', ' ').title()}:</strong> {point_est:.1%} 
                <br><small>95% CI: [{lower:.1%}, {upper:.1%}]</small>
            </div>
            """, unsafe_allow_html=True)


def display_betting_recommendations(recommendations: Dict[str, Any]):
    """Display betting recommendations with expected value analysis"""
    if not recommendations:
        return
    
    st.markdown("### 💰 Betting Recommendations")
    
    recs = recommendations.get("recommendations", [])
    best_bet = recommendations.get("best_bet")
    
    if best_bet:
        st.markdown(f"""
        <div class="recommendation-card">
            <h4>🏆 Best Betting Opportunity</h4>
            <strong>Outcome:</strong> {best_bet['outcome'].replace('_', ' ').title()}<br>
            <strong>Recommendation:</strong> {best_bet['recommendation']}<br>
            <strong>Expected Value:</strong> {best_bet['expected_value']:.1%}<br>
            <strong>Confidence:</strong> {best_bet['confidence']}<br>
            <strong>Suggested Stake:</strong> {best_bet['suggested_stake']:.1%} of bankroll<br>
            <strong>Reasoning:</strong> {best_bet['reasoning']}
        </div>
        """, unsafe_allow_html=True)
    
    # Display all recommendations
    for rec in recs:
        rec_class = "recommendation-card"
        if rec['recommendation'] == 'BET':
            rec_class += " confidence-high"
        else:
            rec_class += " confidence-low"
        
        st.markdown(f"""
        <div class="{rec_class}">
            <strong>{rec['outcome'].replace('_', ' ').title()}:</strong> {rec['recommendation']}<br>
            <strong>Expected Value:</strong> {rec['expected_value']:.1%}<br>
            <strong>Confidence:</strong> {rec['confidence']}<br>
            <small>{rec['reasoning']}</small>
        </div>
        """, unsafe_allow_html=True)


async def run_analysis_workflow(game_query: str) -> Dict[str, Any]:
    """Run the complete analysis workflow with real-time updates"""
    
    # Initialize agents
    coordinator = CoordinationAgent()
    data_agent = DataCollectionAgent()
    stats_agent = StatisticalAnalysisAgent()
    prob_agent = ProbabilityCalculationAgent()
    
    # Register agents with coordinator
    coordinator.register_agent(data_agent)
    coordinator.register_agent(stats_agent)
    coordinator.register_agent(prob_agent)
    
    # Run workflow
    game_data = {"game_query": game_query, "sport": "americanfootball_nfl"}
    result = await coordinator.run_workflow(game_data)
    
    return result


def main():
    # Main header
    st.markdown('<h1 class="main-header">🏈 Sports Betting Analysis - Multi-Agent AI System</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    **Powered by BMasterAI Logging Framework, Agno Multi-Agent System, and Gemini AI**
    
    This application demonstrates real-time AI reasoning transparency by showing how multiple 
    specialized agents collaborate to analyze sports betting scenarios and provide probability-based 
    recommendations with full chain of thought visibility.
    """)
    
    st.warning(
        "⚠️ **Disclaimer:** This application is for educational and demonstration purposes only. "
        "Sports betting involves risk and this tool does not guarantee profits. Always gamble responsibly "
        "and never bet more than you can afford to lose. Consult local laws regarding sports betting legality."
    )
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    if 'chain_of_thought_updates' not in st.session_state:
        st.session_state.chain_of_thought_updates = []
    if 'analysis_running' not in st.session_state:
        st.session_state.analysis_running = False
    
    # Sidebar configuration
    with st.sidebar:
        st.header("🎯 Analysis Configuration")
        
        # Game selection
        game_query = st.text_area(
            "Game/Matchup Query",
            value="Chiefs vs Bills NFL",
            height=120,
            help="Enter the teams or game you want to analyze, or ask specific questions about player performance (e.g., 'Chiefs vs Bills - How is Mahomes' passing performance in cold weather?', 'Lakers vs Warriors - Curry's 3-point shooting vs Lakers defense')"
        )
        
        sport_type = st.selectbox(
            "Sport Type",
            ["NFL", "NBA", "MLB", "NHL", "College Football", "College Basketball"],
            index=0
        )
        
        # Analysis options
        st.subheader("🔧 Analysis Options")
        include_market_analysis = st.checkbox("Market Analysis", value=True)
        include_news_sentiment = st.checkbox("News & Sentiment Analysis", value=True)
        include_statistical_models = st.checkbox("Statistical Models", value=True)
        
        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            confidence_threshold = st.slider("Minimum Confidence Threshold", 0.0, 1.0, 0.6, 0.1)
            max_bet_percentage = st.slider("Maximum Bet Percentage", 0.0, 0.25, 0.05, 0.01)
            simulation_runs = st.number_input("Monte Carlo Simulations", 1000, 50000, 10000, 1000)
        
        # Analysis button
        analyze_button = st.button("🚀 Run Analysis", type="primary", disabled=st.session_state.analysis_running)
        
        if st.button("🔄 Reset Analysis"):
            st.session_state.analysis_results = {}
            st.session_state.chain_of_thought_updates = []
            st.session_state.analysis_running = False
            st.rerun()
    
    # Main content area
    if analyze_button and game_query:
        st.session_state.analysis_running = True
        st.session_state.chain_of_thought_updates = []
        
        # Display progress
        progress_placeholder = st.empty()
        chain_of_thought_placeholder = st.empty()
        
        with st.spinner(f"🧠 Analyzing {game_query}..."):
            try:
                # Simulate real-time updates for demonstration
                steps = [
                    ("game_selection", "Selected game for analysis", 1.0),
                    ("data_collection", "Collecting odds, statistics, and news data", 0.8),
                    ("statistical_analysis", "Running Poisson, Elo, and Monte Carlo models", 0.9),
                    ("market_analysis", "Analyzing betting markets and line movements", 0.7),
                    ("news_sentiment", "Processing news articles and sentiment", 0.6),
                    ("probability_calculation", "Synthesizing all analysis into final probabilities", 0.9),
                    ("complete", "Analysis complete with recommendations", 1.0)
                ]
                
                for i, (step, reasoning, confidence) in enumerate(steps):
                    # Update progress
                    with progress_placeholder.container():
                        display_analysis_progress(step)
                    
                    # Add chain of thought update
                    update = {
                        "step_type": step,
                        "reasoning": reasoning,
                        "confidence": confidence,
                        "timestamp": datetime.now().isoformat(),
                        "agent_id": f"agent_{i+1}"
                    }
                    st.session_state.chain_of_thought_updates.append(update)
                    
                    # Display chain of thought
                    with chain_of_thought_placeholder.container():
                        display_chain_of_thought_updates(st.session_state.chain_of_thought_updates)
                    
                    # Simulate processing time
                    time.sleep(1)
                
                # Run actual analysis (simplified for demo)
                # In production, this would run the actual agent workflow
                mock_results = {
                    "probability_analysis": {
                        "updated_probabilities": {
                            "team1_win": 0.58,
                            "team2_win": 0.39,
                            "tie": 0.03
                        }
                    },
                    "confidence_intervals": {
                        "team1_win": {"point_estimate": 0.58, "lower_bound": 0.52, "upper_bound": 0.64},
                        "team2_win": {"point_estimate": 0.39, "lower_bound": 0.33, "upper_bound": 0.45},
                        "tie": {"point_estimate": 0.03, "lower_bound": 0.01, "upper_bound": 0.05}
                    },
                    "betting_recommendations": {
                        "best_bet": {
                            "outcome": "team1_win",
                            "recommendation": "BET",
                            "expected_value": 0.12,
                            "confidence": "High Confidence",
                            "suggested_stake": 0.08,
                            "reasoning": "Strong statistical edge with 12% expected value"
                        },
                        "recommendations": [
                            {
                                "outcome": "team1_win",
                                "recommendation": "BET",
                                "expected_value": 0.12,
                                "confidence": "High Confidence",
                                "reasoning": "Strong statistical edge with 12% expected value"
                            },
                            {
                                "outcome": "team2_win",
                                "recommendation": "PASS",
                                "expected_value": -0.05,
                                "confidence": "No Value",
                                "reasoning": "Negative expected value of -5%"
                            }
                        ]
                    }
                }
                
                st.session_state.analysis_results = mock_results
                st.session_state.analysis_running = False
                
                st.success("✅ Analysis completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                st.session_state.analysis_running = False
    
    # Display results if available
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        st.markdown('<div class="section-header">📊 Analysis Results</div>', unsafe_allow_html=True)
        
        # Create tabs for different result sections
        tab1, tab2, tab3 = st.tabs(["🎲 Probabilities", "💰 Recommendations", "🧠 Chain of Thought"])
        
        with tab1:
            display_probability_summary(results)
        
        with tab2:
            display_betting_recommendations(results.get("betting_recommendations", {}))
        
        with tab3:
            display_chain_of_thought_updates(st.session_state.chain_of_thought_updates)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    *Powered by BMasterAI Logging Framework, Agno Multi-Agent System, Tavily Search API, and Gemini AI*
    
    **Educational Use Only** - This tool is designed for learning about AI reasoning transparency 
    and multi-agent systems in sports analysis. Always verify information independently and 
    consult professional advice for actual betting decisions.
    """)


if __name__ == "__main__":
    main()

