import streamlit as st
import os
import json
from anthropic import Anthropic
from mcp_client import MCPClient

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AIRFLOW_API_URL = os.getenv("AIRFLOW_API_URL", "http://localhost:8088/api/v1")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "airflow")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "airflow")

st.set_page_config(page_title="Airflow MCP Assistant", layout="wide")
st.title("🚀 Airflow MCP Assistant with Anthropic Claude")

# Initialize clients
if ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    st.error("❌ ANTHROPIC_API_KEY environment variable not set.")
    st.stop()

mcp_client = MCPClient(
    airflow_api_url=AIRFLOW_API_URL,
    airflow_username=AIRFLOW_USERNAME,
    airflow_password=AIRFLOW_PASSWORD
)

def get_anthropic_response(prompt: str, system_prompt: str = None) -> str:
    """Get a response from the Anthropic API."""
    try:
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 2048,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
            
        message = anthropic_client.messages.create(**kwargs)
        return message.content[0].text
    except Exception as e:
        st.error(f"Error communicating with Anthropic API: {e}")
        return None

def interpret_user_query(user_query: str) -> dict:
    """Use Anthropic to interpret user query and determine the appropriate MCP action."""
    system_prompt = """You are an AI assistant that helps interpret user queries about Apache Airflow and determines the appropriate action to take with an MCP server.

Available MCP actions:
- list_dags: Get all DAGs
- get_dag_runs <dag_id>: Get runs for a specific DAG
- trigger_dag <dag_id>: Trigger a DAG
- get_failed_dags: Get failed DAGs

Respond with a JSON object containing:
- "action": the MCP action to take
- "parameters": any parameters needed (like dag_id)
- "explanation": brief explanation of what you're doing

Examples:
User: "What DAGs do we have?"
Response: {"action": "list_dags", "parameters": {}, "explanation": "Listing all available DAGs"}

User: "Show me runs for the data_pipeline DAG"
Response: {"action": "get_dag_runs", "parameters": {"dag_id": "data_pipeline"}, "explanation": "Getting runs for the data_pipeline DAG"}"""

    prompt = f"User query: {user_query}\n\nJSON response:"
    
    response = get_anthropic_response(prompt, system_prompt)
    
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "action": "list_dags", 
            "parameters": {}, 
            "explanation": "Could not parse query, defaulting to listing DAGs"
        }

def execute_mcp_action(action_data: dict) -> dict:
    """Execute the determined MCP action."""
    action = action_data.get("action")
    parameters = action_data.get("parameters", {})
    
    if action == "list_dags":
        return mcp_client.get_dags()
    elif action == "get_dag_runs":
        dag_id = parameters.get("dag_id")
        if dag_id:
            return mcp_client.get_dag_runs(dag_id)
        else:
            return {"error": "No DAG ID provided"}
    elif action == "trigger_dag":
        dag_id = parameters.get("dag_id")
        if dag_id:
            return mcp_client.trigger_dag(dag_id)
        else:
            return {"error": "No DAG ID provided"}
    elif action == "get_failed_dags":
        return mcp_client.get_failed_dags()
    else:
        return {"error": f"Unknown action: {action}"}

def format_response_with_anthropic(user_query: str, mcp_response: dict, action_explanation: str) -> str:
    """Use Anthropic to format the MCP response in a user-friendly way."""
    system_prompt = """You are an AI assistant that helps explain Apache Airflow data to users in a clear, friendly way. 
Take the raw MCP server response and format it into a helpful, easy-to-understand explanation that directly answers the user's question.

Focus on:
- Answering the user's specific question
- Highlighting important information
- Using clear, non-technical language when possible
- Organizing information logically"""

    prompt = f"""User asked: "{user_query}"
Action taken: {action_explanation}
MCP server response: {json.dumps(mcp_response, indent=2)}

Please provide a clear, helpful explanation of this data:"""

    return get_anthropic_response(prompt, system_prompt)

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")
st.sidebar.write(f"**Airflow URL:** {AIRFLOW_API_URL}")
st.sidebar.write(f"**Username:** {AIRFLOW_USERNAME}")

# Test connection button
if st.sidebar.button("🔍 Test MCP Connection"):
    with st.sidebar:
        with st.spinner("Testing connection..."):
            test_result = mcp_client.get_dags()
            if test_result and not test_result.get("error"):
                st.success("✅ MCP connection successful!")
            else:
                st.error(f"❌ MCP connection failed: {test_result.get('error', 'Unknown error')}")

# Main interface
st.subheader("💬 Ask about your Airflow DAGs")

# Example queries
st.write("**Example queries:**")
example_queries = [
    "What DAGs do we have in our Airflow cluster?",
    "Show me the failed DAGs",
    "What is the status of the data_pipeline DAG?",
    "Trigger the daily_report DAG"
]

for i, example in enumerate(example_queries):
    if st.button(f"📝 {example}", key=f"example_{i}"):
        st.session_state.user_input = example

# User input
user_query = st.text_input(
    "Enter your question:",
    value=st.session_state.get("user_input", ""),
    placeholder="e.g., What DAGs failed today?"
)

if st.button("🚀 Send Query", type="primary"):
    if user_query:
        # Step 1: Interpret the user query
        with st.spinner("🤔 Understanding your question..."):
            action_data = interpret_user_query(user_query)
        
        st.info(f"**Action:** {action_data['explanation']}")
        
        # Step 2: Execute MCP action
        with st.spinner("📡 Querying Airflow..."):
            mcp_response = execute_mcp_action(action_data)
        
        # Step 3: Display raw response (collapsible)
        with st.expander("🔍 Raw MCP Response", expanded=False):
            st.json(mcp_response)
        
        # Step 4: Format response with Anthropic
        if mcp_response and not mcp_response.get("error"):
            with st.spinner("✨ Formatting response..."):
                formatted_response = format_response_with_anthropic(
                    user_query, 
                    mcp_response, 
                    action_data['explanation']
                )
            
            st.subheader("📋 Response")
            st.write(formatted_response)
        else:
            st.error(f"❌ Error: {mcp_response.get('error', 'Unknown error occurred')}")
    else:
        st.warning("⚠️ Please enter a question.")

# Instructions
st.sidebar.header("📖 Setup Instructions")
st.sidebar.markdown("""
**Prerequisites:**
1. Docker installed and running
2. Anthropic API key
3. Local Airflow instance (optional)

**Environment Variables:**
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `AIRFLOW_API_URL`: Airflow API URL (default: http://localhost:8088/api/v1)
- `AIRFLOW_USERNAME`: Airflow username (default: airflow)
- `AIRFLOW_PASSWORD`: Airflow password (default: airflow)

**To run:**
```bash
streamlit run enhanced_app.py
```
""")

# Clear session state button
if st.sidebar.button("🗑️ Clear Session"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

