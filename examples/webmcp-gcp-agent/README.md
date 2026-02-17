# WebMCP + GCP Agent Runtime — BMasterAI Example

> An AI agent running on GCP Cloud Run that controls a website by calling its
> [WebMCP](https://webmachinelearning.github.io/webmcp/) tools — instrumented
> end-to-end with BMasterAI monitoring.

---

## What Is WebMCP?

[WebMCP](https://webmachinelearning.github.io/webmcp/) is a W3C draft spec that
lets web pages expose JavaScript functions as **agent-callable tools** directly
in the browser via `navigator.modelContext`:

```js
// Website registers tools — no backend needed
navigator.modelContext.registerTool({
  name: "search_products",
  description: "Search the product catalog",
  inputSchema: { type: "object", properties: { query: { type: "string" } } },
  execute: async (input, client) => {
    return catalog.filter(p => p.name.includes(input.query));
  }
});
```

Think of it as **MCP but browser-native** — tools live in client-side JS,
not on a server.

---

## Architecture

```
┌─────────────────────────────────┐     HTTP POST /run
│  GCP Cloud Run — WebMCP Agent   │ ◄──────────────────── client
│                                 │
│  ┌─────────────┐  ┌──────────┐  │
│  │   Gemini    │  │BMasterAI │  │
│  │  (Vertex AI)│  │monitoring│  │
│  └──────┬──────┘  └──────────┘  │
│         │ tool calls             │
│  ┌──────▼──────────────────┐    │
│  │   WebMCP Bridge          │    │
│  │   (Playwright + CDP)     │    │
│  └──────┬───────────────────┘    │
└─────────┼───────────────────────┘
          │  headless Chromium
          ▼
┌─────────────────────────────────┐
│   Demo Site (Flask / static)    │
│                                 │
│   navigator.modelContext        │
│   ├── search_products           │
│   ├── get_product_details       │
│   ├── add_to_cart               │
│   ├── get_cart                  │
│   └── checkout                  │
└─────────────────────────────────┘
```

### How the Bridge Works

Since WebMCP is a browser-side API, the Python agent can't call it directly.
The **WebMCP Bridge** (`webmcp_bridge.py`) solves this with Playwright:

1. Launches headless Chromium
2. Injects a script *before* the page loads that intercepts `navigator.modelContext.registerTool()` calls
3. Exposes `window.__webmcp_list_tools()` and `window.__webmcp_call_tool(name, args)` globals
4. Python calls these via `page.evaluate()` — Playwright marshals the results across the JS/Python boundary

```python
async with WebMCPBridge("http://localhost:8080") as bridge:
    tools = await bridge.list_tools()
    # [{"name": "search_products", "description": "...", "inputSchema": {...}}, ...]

    result = await bridge.call_tool("search_products", {"query": "laptop"})
    # {"results": [...], "total": 3}
```

---

## Project Structure

```
webmcp-gcp-agent/
├── demo-site/
│   ├── index.html          # Demo store UI
│   ├── webmcp-polyfill.js  # navigator.modelContext polyfill + bridge globals
│   ├── webmcp-tools.js     # Tool registrations (search, cart, checkout)
│   ├── products.js         # Mock product catalog
│   ├── server.py           # Flask dev server
│   └── Dockerfile.demo
├── agent/
│   ├── agent.py            # FastAPI Cloud Run app + Gemini agent loop
│   ├── webmcp_bridge.py    # Playwright WebMCP bridge
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml      # Local dev stack
├── deploy.sh               # GCP deployment script
└── README.md
```

---

## Quickstart (Local)

### Prerequisites

```bash
pip install playwright
playwright install chromium
```

### Run with Docker Compose

```bash
docker-compose up --build
```

This starts:
- **Demo site** at `http://localhost:8080` (WebMCP store)
- **Agent** at `http://localhost:8081`

### Test it

```bash
# List available WebMCP tools
curl http://localhost:8081/tools

# Run an agent task
curl -X POST http://localhost:8081/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Find me a laptop under $1000 and add it to the cart"}'
```

**Example response:**
```json
{
  "task": "Find me a laptop under $1000 and add it to the cart",
  "result": "I found the UltraBook Pro 14 at $899.99 and added 1 to your cart. Your cart total is $899.99.",
  "tool_calls": [
    {"tool": "search_products", "args": {"query": "laptop", "max_price": 1000}, "success": true},
    {"tool": "add_to_cart", "args": {"product_id": "p001", "quantity": 1}, "success": true}
  ],
  "success": true
}
```

### Run without Docker

```bash
# Terminal 1 — start demo site
cd demo-site && pip install flask && python server.py

# Terminal 2 — start agent  
cd agent && pip install -r requirements.txt && python agent.py

# Terminal 3 — test
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"task": "What laptops do you have in stock?"}'
```

---

## Deploy to GCP Cloud Run

### Prerequisites

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com aiplatform.googleapis.com
```

### Deploy

```bash
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID us-central1
```

This deploys both the demo site and the agent as separate Cloud Run services,
then runs a smoke test.

---

## BMasterAI Integration

The agent uses BMasterAI for full observability:

```python
from bmasterai.logging import configure_logging, get_logger, EventType
from bmasterai.monitoring import get_monitor

logger = get_logger("webmcp-agent")
monitor = get_monitor()

# Events logged automatically:
# EventType.TASK_START   — when a task begins
# EventType.TOOL_CALL    — each WebMCP tool call
# EventType.TASK_COMPLETE — when the agent finishes
# EventType.ERROR        — on failures

# Metrics tracked:
monitor.record_metric("webmcp_tools_discovered", len(tools))
monitor.record_metric("webmcp_tool_calls", 1)
monitor.record_metric("gemini_api_calls", 1)
monitor.record_metric("agent_task_completed", 1)
```

View logs:
```bash
# Local
cat agent.log

# GCP Cloud Run
gcloud run logs read webmcp-agent --region us-central1 --limit 50
```

---

## Adding Your Own WebMCP Tools

On your website, register tools via `navigator.modelContext`:

```html
<script src="webmcp-polyfill.js"></script>
<script>
navigator.modelContext.registerTool({
  name: "my_tool",
  description: "What this tool does — be descriptive, the LLM reads this",
  inputSchema: {
    type: "object",
    properties: {
      param: { type: "string", description: "What param does" }
    },
    required: ["param"]
  },
  execute: async (input, client) => {
    // Your tool logic here
    return { result: doSomething(input.param) };
  }
});
</script>
```

The agent will automatically discover and call your tools. No backend changes needed.

---

## Notes

- **WebMCP is a draft spec** (W3C Web Machine Learning Community Group, Feb 2026).
  Browser support is not yet widespread — the polyfill handles this.
- **Playwright runs in the Cloud Run container** — the headless Chromium browser
  adds ~200MB to the image. Ensure your Cloud Run instance has at least 1GB memory.
- **The bridge is stateful per-request** — each `POST /run` opens and closes its
  own browser session. For high-throughput use, consider a browser pool.

---

## License

MIT — see [bmasterai LICENSE](../../LICENSE)
