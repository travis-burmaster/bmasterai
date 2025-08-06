import os
import json
import asyncio

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

from bmasterai.logging import configure_logging, get_logger, LogLevel
from fastmcp import Client

# Load environment variables from .env file
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRFLOW_API_URL = os.getenv("AIRFLOW_API_URL", "http://localhost:8088/api/v1")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "airflow")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "airflow")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3000")

# Set up logging
configure_logging(log_level=LogLevel.INFO)
logger = get_logger().logger

st.set_page_config(page_title="Airflow MCP Assistant", layout="wide")
st.title("🚀 Airflow MCP Assistant with OpenAI")

# Initialize clients
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    st.error("❌ OPENAI_API_KEY environment variable not set.")
    st.stop()

mcp_client = Client(transport=MCP_SERVER_URL)

def get_openai_response(prompt: str, system_prompt: str = None) -> str:
    """Get a response from the OpenAI API."""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=2048,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error communicating with OpenAI API: {e}")
        return None

def interpret_user_query(user_query: str) -> dict:
    """Use OpenAI to interpret user query and determine the appropriate MCP action."""
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
    
    response = get_openai_response(prompt, system_prompt)

    try:
        parsed = json.loads(response)
        logger.info("Interpreted action: %s", parsed.get("action"))
        return parsed
    except json.JSONDecodeError:
        logger.warning("Failed to parse OpenAI response; defaulting to list_dags")
        return {
            "action": "list_dags",
            "parameters": {},
            "explanation": "Could not parse query, defaulting to listing DAGs",
        }

async def execute_mcp_action_async(action_data: dict) -> dict:
    """Execute the determined MCP action asynchronously."""
    action = action_data.get("action")
    parameters = action_data.get("parameters", {})

    logger.info("Executing MCP action: %s", action)
    try:
        async with mcp_client:
            if action == "list_dags":
                result = await mcp_client.call_tool("list_dags", {})
            elif action == "get_dag_runs":
                dag_id = parameters.get("dag_id")
                if dag_id:
                    result = await mcp_client.call_tool("get_dag_runs", {"dag_id": dag_id})
                else:
                    return {"error": "No DAG ID provided"}
            elif action == "trigger_dag":
                dag_id = parameters.get("dag_id")
                if dag_id:
                    result = await mcp_client.call_tool("trigger_dag", {"dag_id": dag_id})
                else:
                    return {"error": "No DAG ID provided"}
            elif action == "get_failed_dags":
                result = await mcp_client.call_tool("get_failed_dags", {})
            else:
                logger.error("Unknown MCP action: %s", action)
                return {"error": f"Unknown action: {action}"}
            
            return result
    except Exception as e:
        logger.error("Error executing MCP action %s: %s", action, str(e))
        return {"error": f"Failed to execute {action}: {str(e)}"}

def execute_mcp_action(action_data: dict) -> dict:
    """Execute the determined MCP action (sync wrapper)."""
    return asyncio.run(execute_mcp_action_async(action_data))

def format_response_with_openai(user_query: str, mcp_response: dict, action_explanation: str) -> str:
    """Use OpenAI to format the MCP response in a user-friendly way."""
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

    return get_openai_response(prompt, system_prompt)

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")
st.sidebar.write(f"**Airflow URL:** {AIRFLOW_API_URL}")
st.sidebar.write(f"**Username:** {AIRFLOW_USERNAME}")
st.sidebar.write(f"**MCP Server:** {MCP_SERVER_URL}")

# Test connection button
if st.sidebar.button("🔍 Test MCP Connection"):
    with st.sidebar:
        with st.spinner("Testing connection..."):
            try:
                async def test_connection():
                    async with mcp_client:
                        return await mcp_client.call_tool("list_dags", {})
                
                test_result = asyncio.run(test_connection())
                if test_result and not test_result.get("error"):
                    st.success("✅ MCP connection successful!")
                else:
                    st.error(f"❌ MCP connection failed: {test_result.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"❌ MCP connection failed: {str(e)}")

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
        
        # Step 4: Format response with OpenAI
        if mcp_response and not mcp_response.get("error"):
            with st.spinner("✨ Formatting response..."):
                formatted_response = format_response_with_openai(
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
2. OpenAI API key
3. Local Airflow instance (optional)

**Environment Variables:**
- `OPENAI_API_KEY`: Your OpenAI API key
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

