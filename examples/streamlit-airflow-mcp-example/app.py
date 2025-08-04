
import os

import streamlit as st
from openai import OpenAI

from bmasterai.logging import configure_logging, get_logger, LogLevel
from fastmcp import MCPClient

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Replace with your MCP server URL if running externally
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3000")

# Set up logging
configure_logging(log_level=LogLevel.INFO)
logger = get_logger().logger

# Initialize MCP client
mcp_client = MCPClient(server_url=MCP_SERVER_URL)

st.set_page_config(page_title="Airflow MCP Chatbot", layout="wide")
st.title("Airflow MCP Chatbot with OpenAI")

# Initialize OpenAI client
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    st.error("OPENAI_API_KEY environment variable not set.")
    st.stop()

def send_to_mcp(query):
    """Sends a query to the MCP server and returns the response."""
    try:
        logger.info("Sending query to MCP: %s", query)
        return mcp_client.query(query)
    except Exception as e:  # pragma: no cover - network errors
        logger.error("Error communicating with MCP server: %s", e)
        st.error(f"Error communicating with MCP server: {e}")
        return None

def get_openai_response(prompt):
    """Gets a response from the OpenAI API."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error communicating with OpenAI API: {e}")
        return None

# Streamlit UI
user_query = st.text_input(
    "Ask a question about your Airflow DAGs:", "What DAGs do we have?"
)

if st.button("Send Query"):
    if user_query:
        st.subheader("Thinking...")
        
        # Step 1: Use OpenAI to formulate a precise query for MCP
        openai_prompt = f"""You are an AI assistant helping to interact with an Apache Airflow MCP server.
Given the user's natural language query, generate a concise, direct query that the MCP server can understand.
Do not include any conversational filler. Just the query itself.

User query: {user_query}
MCP-ready query:"""

        mcp_query = get_openai_response(openai_prompt)

        if mcp_query:
            st.write(f"OpenAI generated MCP query: `{mcp_query}`")
            
            # Step 2: Send the OpenAI-generated query to the MCP server
            mcp_response = send_to_mcp(mcp_query)
            
            if mcp_response:
                st.subheader("MCP Server Response:")
                st.json(mcp_response)
                
                # Step 3: Use OpenAI to interpret the MCP response for the user
                interpretation_prompt = f"""You are an AI assistant interpreting responses from an Apache Airflow MCP server.
Given the original user query, the MCP server's response, and the MCP query that was sent,
explain the MCP response in a user-friendly way, addressing the original user's question.

Original user query: {user_query}
MCP query sent: {mcp_query}
MCP server response: {mcp_response}

User-friendly explanation:"""
                
                user_friendly_explanation = get_openai_response(interpretation_prompt)
                
                if user_friendly_explanation:
                    st.subheader("User-Friendly Explanation:")
                    st.write(user_friendly_explanation)
            else:
                st.warning("No response from MCP server.")
        else:
            st.warning("OpenAI could not generate a valid MCP query.")
    else:
        st.warning("Please enter a query.")

# Instructions for running
st.sidebar.header("How to Run")
st.sidebar.markdown("""
1.  **Set up Airflow MCP:** Follow instructions in the `airflow-mcp` repository to run the MCP server locally. 
    You'll likely need to set up a local Airflow instance first.
2.  **Set Environment Variables:**
    *   `OPENAI_API_KEY`: Your OpenAI API key.
    *   `MCP_SERVER_URL`: The URL where your MCP server is running (e.g., `http://localhost:8000`).
3.  **Run Streamlit:** Navigate to this directory in your terminal and run `streamlit run app.py`.
""")



