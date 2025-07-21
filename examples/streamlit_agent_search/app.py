import streamlit as st
import requests
import json
from typing import Dict, List, Optional

# Configure page settings
st.set_page_config(
    page_title="AI Agent Search",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'selected_agent' not in st.session_state:
    st.session_state.selected_agent = None

def search_agents(query: str) -> List[Dict]:
    """
    Search for AI agents based on the provided query
    """
    try:
        # Mock API endpoint - replace with actual API in production
        response = requests.get(
            f"https://api.example.com/agents/search",
            params={"q": query},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error searching agents: {str(e)}")
        return []

def integrate_agent(agent_id: str) -> bool:
    """
    Integrate selected agent with the current application
    """
    try:
        # Mock API endpoint - replace with actual API in production
        response = requests.post(
            f"https://api.example.com/agents/{agent_id}/integrate",
            timeout=10
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error integrating agent: {str(e)}")
        return False

# Main application layout
st.title("AI Agent Search & Integration")
st.write("Search and integrate with AI agents from various sources")

# Search interface
with st.container():
    search_query = st.text_input("Search for AI agents", placeholder="Enter keywords...")
    if st.button("Search"):
        with st.spinner("Searching..."):
            results = search_agents(search_query)
            st.session_state.search_results = results

# Display search results
if st.session_state.search_results:
    st.subheader("Search Results")
    for idx, agent in enumerate(st.session_state.search_results):
        with st.expander(f"{agent.get('name', 'Unknown Agent')} - {agent.get('type', 'Unknown Type')}"):
            st.write(f"Description: {agent.get('description', 'No description available')}")
            st.write(f"Capabilities: {', '.join(agent.get('capabilities', []))}")
            st.write(f"Provider: {agent.get('provider', 'Unknown')}")
            
            if st.button("Integrate", key=f"integrate_{idx}"):
                with st.spinner("Integrating agent..."):
                    if integrate_agent(agent.get('id')):
                        st.success("Agent successfully integrated!")
                        st.session_state.selected_agent = agent
                    else:
                        st.error("Failed to integrate agent")

# Display integrated agent details
if st.session_state.selected_agent:
    st.sidebar.subheader("Integrated Agent")
    st.sidebar.json(st.session_state.selected_agent)
    if st.sidebar.button("Remove Integration"):
        st.session_state.selected_agent = None
        st.success("Agent integration removed")

# Footer
st.markdown("---")
st.markdown("*Powered by AI Agent Search Engine*")

# Error handling for session state
try:
    st.session_state
except Exception as e:
    st.error("Session state error occurred. Please refresh the page.")
    st.exception(e)