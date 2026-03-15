# claude-web-computer-agent

A bare-metal Claude tool-use agent combining **web search** and **computer use** — no LangGraph, no framework, just the Anthropic SDK — fully instrumented with **BMasterAI** logging and telemetry.

This is the foundational pattern that every Claude agent is built on. Study this before moving to the LangGraph examples.

---

## What It Demonstrates

- The raw Anthropic `tool_use` / `tool_result` message cycle (the core loop behind every Claude agent)
- How to register two complementary tool types — network I/O (web search) and system I/O (computer use)
- How to send screenshot images back to Claude as multimodal `tool_result` content
- BMasterAI telemetry on every step of a bare SDK agent — not just framework agents

---

## Architecture

```
user prompt
    ↓
claude_call (tools: web_search, computer_use, calculator)
    ↓
stop_reason == "tool_use"?
   ├── yes → dispatch tool(s) → append tool_result(s) → loop back
   └── no  → final text response → END
```

**Tools available:**

| Tool | Description | Implementation |
|---|---|---|
| `web_search` | Tavily search — current information from the web | `tavily-python` |
| `computer_use` | Screenshot, click, type, key, scroll | `xdotool` + `scrot` |

---

## BMasterAI Instrumentation

| Event | BMasterAI call |
|---|---|
| Agent starts | `monitor.track_agent_start(AGENT_ID)` + `log_event(AGENT_START)` |
| Each Claude API call | `monitor.track_llm_call(...)` + `log_event(LLM_CALL)` ×2 (before + after) |
| Tool dispatched | `log_event(TOOL_USE)` |
| Tool result returned | `log_event(TASK_COMPLETE)` or `log_event(TASK_ERROR)` |
| Loop decision | `log_event(DECISION_POINT, "continue" or "end_turn")` |
| Any exception | `monitor.track_error(...)` + `log_event(TASK_ERROR)` |
| Agent finishes | `monitor.track_agent_stop(AGENT_ID)` + `log_event(AGENT_STOP)` |
| Task timings | `monitor.track_task_duration(...)` per LLM call and per tool call |

Telemetry output:

```
logs/agent.log                  — human-readable event log
logs/agent.jsonl                — structured JSON (pipe to any analytics tool)
logs/reasoning/agent_reasoning.jsonl  — decision points and reasoning chains
```

---

## Setup

```bash
pip install -r requirements.txt

# Linux only: install computer use dependencies
sudo apt-get install scrot xdotool
```

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Required:
- `ANTHROPIC_API_KEY` — [console.anthropic.com](https://console.anthropic.com)

Optional (enables `web_search`):
- `TAVILY_API_KEY` — [tavily.com](https://tavily.com) (generous free tier)

---

## Usage

```bash
# Pass query as argument
python main.py "Search for the latest Anthropic model pricing and calculate
                the cost of 1 million tokens at Sonnet rates."

# Or run interactively
python main.py
```

### Example queries

```bash
# Web search
python main.py "What are the key differences between Claude Opus 4.6 and Sonnet 4.6?"

# Computer use — screenshot + describe
python main.py "Take a screenshot of my current screen and describe what applications are open."

# Combined workflow — the core use case for this example
python main.py "Search for today's top AI news, open a browser to the first result,
                take a screenshot, and summarize what you see."
```

---

## Example Output

```
════════════════════════════════════════════════════════════
🤖  claude-web-computer-agent
────────────────────────────────────────────────────────────
📝  Query: Search for Claude Opus 4.6 pricing and calculate cost for 1M tokens
════════════════════════════════════════════════════════════

🔄  Turn 1/20
   🧠  claude-opus-4-6 | 892+87 tokens | 1243ms | stop=tool_use
   🔧  Tool: web_search({"query": "Claude Opus 4.6 pricing per token 2026"})
   ✅  web_search → {"query": "...", "results": [...], "result_count": 5} (412ms)

🔄  Turn 2/20
   🧠  claude-opus-4-6 | 2341+63 tokens | 987ms | stop=tool_use
   🔧  Tool: computer_use({"action": "screenshot"})
   ✅  computer_use → {"action": "screenshot", "success": true} (312ms)

🔄  Turn 3/20
   🧠  claude-opus-4-6 | 2589+312 tokens | 1821ms | stop=end_turn

✅  Done in 3 turn(s)

════════════════════════════════════════════════════════════
📊  BMASTERAI TELEMETRY
────────────────────────────────────────────────────────────
  Agent status : STOPPED
  Total errors : 0

  Task timings:
    llm_call_turn_1                     avg=1243ms  calls=1
    llm_call_turn_2                     avg=987ms   calls=1
    llm_call_turn_3                     avg=1821ms  calls=1
    tool_web_search                     avg=412ms   calls=1
    tool_computer_use                   avg=312ms   calls=1

  Telemetry logs:
    logs/agent.log       — human-readable
    logs/agent.jsonl     — structured JSON
    logs/reasoning/      — decision points & reasoning
════════════════════════════════════════════════════════════

════════════════════════════════════════════════════════════
🗒️  FINAL RESPONSE
────────────────────────────────────────────────────────────
Based on current pricing, 1 million input tokens with Claude Opus 4.6 would cost $15.00...
════════════════════════════════════════════════════════════
```

---

## Files

| File | Purpose |
|---|---|
| `tools.py` | Tool JSON schemas + dispatch functions for all three tools |
| `agent.py` | `WebComputerAgent` class — the tool-use loop with full BMasterAI instrumentation |
| `main.py` | CLI entry point with env checks and interactive fallback |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

---

## Analyse the Telemetry

```bash
# Show all LLM calls with token counts
cat logs/agent.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    if e.get('event_type') == 'llm_call':
        meta = e.get('metadata', {})
        if 'input_tokens' in meta:
            print(f\"{e['timestamp'][:19]}  tokens={meta.get('input_tokens',0)}+{meta.get('output_tokens',0)}  latency={meta.get('latency_ms',0):.0f}ms\")
"

# Show all tool calls
cat logs/agent.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    if e.get('event_type') == 'tool_use':
        meta = e.get('metadata', {})
        print(f\"{e['timestamp'][:19]}  tool={meta.get('tool_name')}  input={str(meta.get('input',''))[:80]}\")
"

# Show errors only
cat logs/agent.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    if e.get('event_type') == 'task_error':
        print(json.dumps(e, indent=2))
"
```

---

## Stack

- [Anthropic Python SDK](https://github.com/anthropic-ai/anthropic-sdk-python)
- [BMasterAI](https://github.com/travis-burmaster/bmasterai)
- [Tavily Python](https://github.com/tavily-ai/tavily-python)
- [xdotool](https://github.com/jordansissel/xdotool) + [scrot](https://github.com/dreamer/scrot) (Linux computer use)
