import os
import json
import asyncio

import streamlit as st
import anthropic
from dotenv import load_dotenv

from bmasterai.logging import configure_logging, get_logger, LogLevel
from fastmcp import Client

from app_logic import (
    INTERPRET_SYSTEM_PROMPT,
    memory_enabled,
    render_recall_context,
    build_extract_prompt,
)

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3000/mcp")
DEMO_USER_ID = os.getenv("DEMO_USER_ID", "u_demo")

configure_logging(log_level=LogLevel.INFO)
logger = get_logger().logger

st.set_page_config(page_title="Databricks MCP Assistant", layout="wide")
st.title("🧱 Databricks MCP Assistant with Claude")

if not ANTHROPIC_API_KEY:
    st.error("❌ ANTHROPIC_API_KEY environment variable not set.")
    st.stop()


@st.cache_resource
def get_anthropic_client(api_key: str) -> anthropic.Anthropic:
    """Build the Anthropic client once and reuse it across Streamlit reruns."""
    return anthropic.Anthropic(api_key=api_key)


@st.cache_resource
def get_mcp_client(url: str) -> Client:
    """Build the fastmcp client once and reuse it across reruns."""
    return Client(url)


@st.cache_resource
def get_memory(user_id: str):
    """Build the lakehouse-memory client once; return None if memory is off or init fails."""
    if not memory_enabled(os.environ):
        return None
    try:
        from lakehouse_memory import Memory, Scope
        return Memory.from_databricks(
            catalog=os.getenv("MEMORY_CATALOG", "workspace"),
            schema_name=os.getenv("MEMORY_SCHEMA", "mcp_assistant_memory"),
            workspace_url=os.environ["DATABRICKS_HOST"],
            access_token=os.environ["DATABRICKS_TOKEN"],
            http_path=os.environ["DATABRICKS_HTTP_PATH"],
            vector_search_endpoint=os.environ["DATABRICKS_VECTOR_SEARCH_ENDPOINT"],
            scope=Scope(user_id=user_id),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("memory init failed; disabling memory: %s", e)
        return None


anthropic_client = get_anthropic_client(ANTHROPIC_API_KEY)
mcp_client = get_mcp_client(MCP_SERVER_URL)
mem = get_memory(DEMO_USER_ID)
MEMORY_ON = mem is not None


def _unwrap(result):
    """Normalize a fastmcp CallToolResult to a plain Python value."""
    for attr in ("data", "structured_content"):
        if hasattr(result, attr) and getattr(result, attr) is not None:
            return getattr(result, attr)
    return result


def ask_claude(prompt: str, system_prompt: str = None) -> str:
    # Anthropic puts the system prompt in a top-level parameter, not a message role.
    kwargs = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    resp = anthropic_client.messages.create(**kwargs)
    # response.content is a list of blocks; concatenate the text blocks.
    return "".join(b.text for b in resp.content if b.type == "text")


def recall_context(user_query: str) -> str:
    if not (MEMORY_ON and mem):
        return ""
    try:
        return render_recall_context(mem.semantic.retrieve(user_query, k=5))
    except Exception as e:  # noqa: BLE001
        logger.warning("recall failed: %s", e)
        return ""


def remember(user_query: str, answer: str) -> None:
    if not (MEMORY_ON and mem):
        return
    try:
        fact = ask_claude(build_extract_prompt(user_query, answer)).strip()
        if fact and fact.lower() != "none" and len(fact) > 3:
            mem.semantic.upsert(fact=fact, source="mcp-assistant")
            mem.semantic.trigger_sync()
    except Exception as e:  # noqa: BLE001
        logger.warning("remember failed: %s", e)


def interpret(user_query: str) -> dict:
    ctx = recall_context(user_query)
    prompt = f"{ctx}\nUser query: {user_query}\n\nJSON response:"
    raw = ask_claude(prompt, INTERPRET_SYSTEM_PROMPT)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("could not parse interpret response: %s", raw)
        return {
            "action": None,
            "parameters": {},
            "explanation": "I couldn't interpret that question. Try rephrasing it.",
            "parse_error": True,
        }


async def call_tool_async(action: str, parameters: dict):
    async with mcp_client:
        return _unwrap(await mcp_client.call_tool(action, parameters or {}))


def call_tool(action: str, parameters: dict):
    try:
        return asyncio.run(call_tool_async(action, parameters))
    except Exception as e:  # noqa: BLE001
        logger.error("tool call failed: %s", e)
        return {"error": str(e)}


def format_answer(user_query: str, response, explanation: str) -> str:
    system = ("Explain Databricks data clearly and concisely, answering the user's question. "
              "Use plain language; organize logically.")
    prompt = (f'User asked: "{user_query}"\nAction: {explanation}\n'
              f"Response: {json.dumps(response, indent=2, default=str)}\n\nExplain:")
    return ask_claude(prompt, system)


# Sidebar
st.sidebar.header("⚙️ Configuration")
st.sidebar.write(f"**Workspace:** {os.getenv('DATABRICKS_HOST', '(unset)')}")
st.sidebar.write(f"**MCP Server:** {MCP_SERVER_URL}")
st.sidebar.write(f"**Memory:** {'on' if MEMORY_ON else 'off'}")

if MEMORY_ON and mem:
    st.sidebar.header("🧠 What I remember about you")
    try:
        facts = mem.semantic.retrieve("user preferences", k=20)
        for f in facts:
            st.sidebar.write(f"• {f.get('text', '')}")
        if st.sidebar.button("🗑️ Forget me"):
            for f in facts:
                if f.get("fact_id"):
                    mem.semantic.forget(f["fact_id"])
            mem.semantic.trigger_sync()
            st.sidebar.success("Forgotten.")
    except Exception as e:  # noqa: BLE001
        st.sidebar.warning(f"memory unavailable: {e}")
else:
    st.sidebar.info("Memory disabled (set ENABLE_MEMORY=true and DATABRICKS_VECTOR_SEARCH_ENDPOINT).")

if st.sidebar.button("🔍 Test MCP Connection"):
    with st.sidebar:
        with st.spinner("Testing..."):
            res = call_tool("list_catalogs", {})
            if res and not (isinstance(res, dict) and res.get("error")):
                st.success("✅ MCP connection successful!")
            else:
                st.error(f"❌ {res.get('error') if isinstance(res, dict) else res}")

# Main
st.subheader("💬 Ask about your Databricks workspace")
examples = [
    "What jobs do we have?",
    "Show me the failed jobs",
    "What catalogs can I see?",
    "List tables in workspace.lakehouse_memory_test",
    "How many rows are in workspace.lakehouse_memory_test.semantic?",
]
for i, ex in enumerate(examples):
    if st.button(f"📝 {ex}", key=f"ex_{i}"):
        st.session_state.user_input = ex

user_query = st.text_input("Enter your question:", value=st.session_state.get("user_input", ""))

if st.button("🚀 Send Query", type="primary"):
    if not user_query:
        st.warning("⚠️ Please enter a question.")
    else:
        with st.spinner("🤔 Understanding..."):
            action_data = interpret(user_query)
        if action_data.get("parse_error") or not action_data.get("action"):
            st.warning(f"⚠️ {action_data.get('explanation', 'Could not interpret your question.')}")
            st.stop()
        st.info(f"**Action:** {action_data.get('explanation', '')}")
        with st.spinner("📡 Querying Databricks..."):
            response = call_tool(action_data.get("action"), action_data.get("parameters", {}))
        with st.expander("🔍 Raw MCP Response", expanded=False):
            st.json(response)
        if response and not (isinstance(response, dict) and response.get("error")):
            with st.spinner("✨ Formatting..."):
                answer = format_answer(user_query, response, action_data.get("explanation", ""))
            st.subheader("📋 Response")
            st.write(answer)
            remember(user_query, answer)
        else:
            st.error(f"❌ {response.get('error') if isinstance(response, dict) else response}")

if st.sidebar.button("🧹 Clear Session"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()
