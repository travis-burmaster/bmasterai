# tools/

Agent tool implementations. Each tool is defined using the Strands `@tool` decorator and wrapped in a class for registration with the agent.

## Files

### `bash_tool.py` — Shell Command Execution

Wraps AgentCore's Code Interpreter for sandboxed bash execution.

**Tool:** `bash_execute(command, timeout_seconds)`

- Runs shell commands in an isolated sandbox managed by AgentCore
- Supports a configurable timeout (1–120 seconds, default 30)
- Includes a client-side blocklist of dangerous command prefixes (fork bombs, destructive operations) as defense-in-depth on top of Cedar policies
- Returns `{stdout, stderr, exit_code}`

**When the agent uses it:** Quick computations, file processing, API calls with curl, running Python/Node scripts, text manipulation with grep/sed/awk.

---

### `browser_tool.py` — Web Search and Page Fetching

Uses AgentCore's managed Browser tool to launch ephemeral Chromium sessions.

**Tool 1:** `browser_search(query, max_results)`

- Navigates to DuckDuckGo with the query
- Extracts search results from the rendered page
- Returns `{results: [{title, url, snippet}], raw_text}`

**Tool 2:** `browser_fetch_url(url)`

- Navigates to a specific URL and extracts visible text
- Returns `{title, text, url}`

Each call creates a new browser session (default 3-minute timeout), runs the operation, and tears down the session. Sessions are fully isolated containers.

**When the agent uses it:** Current events, documentation lookups, fact-checking, reading articles or API docs.

**Cost note:** Each browser session has a startup cost. For high-frequency search, consider replacing with a search API (Brave, SerpAPI, Tavily) exposed through AgentCore Gateway.

---

### `telegram_tool.py` — Telegram Messaging

Sends messages to Telegram users via the Bot API.

**Tool 1:** `telegram_send_message(chat_id, text, parse_mode)`

- Sends text messages with Markdown or HTML formatting
- Automatically splits messages longer than 4000 characters into multiple chunks
- Returns `{status, message_ids, chunks}`

**Tool 2:** `telegram_send_document(chat_id, file_url, caption)`

- Sends a document/file via public URL
- Returns `{status, message_id}`

**Tool 3:** `telegram_send_photo(chat_id, photo_url, caption)`

- Sends a photo via public URL
- Returns `{status, message_id}`

The bot token is loaded from AWS Secrets Manager and cached in memory. The `TelegramTool` wrapper class binds the actor's chat ID so the agent doesn't need to know raw Telegram IDs.

**When the agent uses it:** Replying to the user (the primary output channel), sending files or images the user requested.

## Adding a New Tool

1. Create `tools/your_tool.py`
2. Define functions with the `@tool` decorator from `strands.tools`
3. Write a clear docstring — the LLM reads it to decide when to use the tool
4. Create a wrapper class with `__call__` that returns the tool function(s)
5. Import and register in `agent/main.py` → `create_agent()`
6. Add a Cedar `permit` policy in `policies/agent_policies.cedar`

## Design Principles

- **Fail gracefully:** Return error dicts instead of raising exceptions
- **Limit output size:** Truncate large outputs to avoid context window bloat
- **Self-documenting:** The `@tool` docstring is the API contract for the LLM
- **Stateless:** No state between calls; all persistence is in memory/DynamoDB
- **Scoped access:** Telegram tools are bound to the requesting user's chat ID
