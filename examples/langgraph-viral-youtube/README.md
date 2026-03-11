# BMasterAI × LangGraph — Viral YouTube Short Generator

> Four AI agents collaborate in a LangGraph pipeline to produce a complete,
> production-ready YouTube Short package — instrumented end-to-end with
> BMasterAI telemetry.

---

## What It Does

You give it a topic. Four specialist agents do the rest:

```
trend_researcher → hook_writer → script_writer → title_and_tags
                                                        ↓
                                                  quality_gate
                                                   /         \
                                            approved       rejected
                                               ↓            ↓
                                             END      retry from hook
```

| Agent | Job |
|---|---|
| **Trend Researcher** | Searches the web (Tavily) for the most viral angle on your topic right now |
| **Hook Writer** | Writes the single best ≤12-word opening line to stop the scroll |
| **Script Writer** | Writes the full 45–60s script: Hook → Conflict → Build → Payoff → CTA |
| **Title & Tags** | Generates a viral title, 10 SEO tags, and thumbnail concept |
| **Quality Gate** | Validates the package; triggers a retry loop (max 2) if it falls short |

**Output:** title, hook, full script, tags, thumbnail concept — ready to record.

---

## BMasterAI Integration

Every agent call is instrumented with structured telemetry:

```python
bm.log_event(EventType.TASK_START, agent_id="hook-writer", metadata={...})
bm.log_event(EventType.LLM_CALL,   agent_id="hook-writer", metadata={...})
bm.log_event(EventType.TASK_COMPLETE, ...)
bm.log_event(EventType.TASK_ERROR, ...)   # on failure
```

Logs written to:
- `logs/agents.log` — human-readable
- `logs/agents.jsonl` — structured JSONL (import into any observability tool)

---

## Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/travis-burmaster/bmasterai
cd bmasterai/examples/langgraph-viral-youtube

# 2. Install deps
pip install -r requirements.txt

# 3. Set API keys
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY and TAVILY_API_KEY

# 4. Run
python main.py "AI agents taking over software engineering"

# Or interactive mode
python main.py
```

---

## Example Output

```
═══════════════════════════════════════════════════════════
🎬  VIRAL YOUTUBE SHORT — PRODUCTION PACKAGE
═══════════════════════════════════════════════════════════

📌  TITLE
The AI Agent Nobody Warned You About

🎣  HOOK  (first 3–5 seconds)
Your job isn't safe — and your boss already knows.

📝  SCRIPT
[HOOK]
Your job isn't safe — and your boss already knows.

[CONFLICT]
AI agents don't just answer questions anymore.
They write code. They deploy it. They fix bugs at 3am.
No salary. No lunch break. No complaints.

[BUILD]
Three things agents can already do better than you:
Debug production code in under 30 seconds.
Write and ship a full feature without a ticket.
Review a PR with zero ego.

[PAYOFF]
This isn't coming. It's already here.
The engineers winning right now aren't fighting agents.
They're building them.

[CTA]
Follow for the playbook. Your future self will thank you.

🏷️   TAGS
AI agents, software engineering, future of work, ...

🖼️   THUMBNAIL CONCEPT
BOLD RED TEXT: "Your job is next" | background: robot at laptop, shocked dev in corner

✅ Quality gate: PASSED (iteration 1)
```

---

## Architecture

```
main.py          ← CLI entry point, invokes graph
graph.py         ← LangGraph StateGraph definition + routing
agents.py        ← All four agent functions + quality gate
state.py         ← Shared VideoState TypedDict
logs/            ← BMasterAI telemetry output
output.json      ← Final result saved after each run
```

---

## API Keys

| Key | Get it at |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) (free tier available) |

---

## How It Differs from Other Examples

| This Example | bmasterai-agentcore |
|---|---|
| LangGraph (framework-agnostic) | Amazon Bedrock AgentCore |
| Multi-agent pipeline | Single research agent |
| Creative content generation | Technical research |
| Conditional retry loop | Linear execution |
| Tavily web search | No external search |

---

## Part of the BMasterAI Examples Collection

- [`bmasterai-agentcore`](../bmasterai-agentcore) — AWS Bedrock AgentCore + Strands
- [`agentcore-memory-agent-bmasterai`](../agentcore-memory-agent-bmasterai) — Telegram bot with persistent memory
- [`a2a-realestate-multiagent`](../a2a-realestate-multiagent) — A2A multi-agent coordination
- [`webmcp-gcp-agent`](../webmcp-gcp-agent) — GCP Cloud Run + WebMCP browser tools
- **`langgraph-viral-youtube`** ← you are here
