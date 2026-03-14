# Deep Research Agent

A multi-step web research agent built with **LangGraph** and instrumented with **BMasterAI** logging and telemetry. Inspired by [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents).

## What It Does

1. **Planner** — breaks your research question into 3–5 focused sub-questions, logs the reasoning chain
2. **Web Searcher** — runs Tavily searches for each sub-question in sequence
3. **Analyzer** — synthesizes search results into one clear finding per question, logs each LLM call
4. **Reflector** — evaluates completeness (quality score 1–10); if gaps exist, loops back for more searches (max 2 loops)
5. **Synthesizer** — combines all findings into a structured report with Executive Summary, Key Findings, Analysis, and Limitations

BMasterAI instruments every step: LLM calls, tool use, agent lifecycle events, decision points, and reasoning chains. Telemetry is written to `logs/research.jsonl` for downstream analysis.

## Architecture

```
planner → web_searcher → analyzer → reflector
                                         ↓
                             needs_more_research?
                              /               \\
                            yes (≤2x)         no
                             ↓                ↓
                        web_searcher      synthesizer → END
                       (follow-ups)
```

## BMasterAI Integration

| BMasterAI feature | Where used |
|---|---|
| `configure_logging` | Once at startup |
| `monitor.track_agent_start/stop` | Every node entry/exit |
| `monitor.track_llm_call` | Every Claude API call |
| `monitor.track_task_duration` | Per-node timing |
| `bm.log_event(EventType.LLM_CALL)` | Before each LLM call |
| `bm.log_event(EventType.TOOL_USE)` | Each Tavily search |
| `bm.log_event(EventType.DECISION_POINT)` | Planner decomposition + reflector routing |
| `bm.log_event(EventType.LLM_REASONING)` | Analyzer synthesis step |
| `bm.log_reasoning_chain` | Planner sub-question breakdown |
| `monitor.get_agent_dashboard()` | Final telemetry printout |
| `logs/research.jsonl` | Structured JSON telemetry for analytics |

## Setup

```bash
pip install -r requirements.txt
# or with uv:
uv add -r requirements.txt
```

Copy `.env.example` to `.env` and add your keys:

```bash
cp .env.example .env
```

Required keys:
- `ANTHROPIC_API_KEY` — [console.anthropic.com](https://console.anthropic.com)
- `TAVILY_API_KEY` — [tavily.com](https://tavily.com) (generous free tier)

## Usage

```bash
# Pass topic as argument
python main.py "What is the current state of multi-agent AI systems in 2026?"

# Or run interactively
python main.py
```

## Example Output

```
📋  Plan:         4 sub-questions
   1. What are the leading multi-agent AI frameworks in 2026?
   2. How are enterprises adopting multi-agent systems?
   3. What benchmarks evaluate multi-agent performance?
   4. What are the key limitations of current multi-agent systems?

🔎  Web search:    4 query batches completed
🧪  Analysis:      4 findings synthesized
🪞  Reflection 1:  approved for synthesis
📝  Synthesizing final report...

═════════════════════════════════════
📊  DEEP RESEARCH REPORT
═════════════════════════════════════

## Executive Summary
...

📈  BMASTERAI TELEMETRY
═════════════════════════════════════
System Health:  HEALTHY

Agent: planner
  LLM calls:    1
  Total tokens: 342
  Avg latency:  1.23s
...

✅  Completed in 38.2s
```

## Logs

| File | Contents |
|---|---|
| `logs/research.log` | Human-readable event log |
| `logs/research.jsonl` | Structured JSON — pipe to any analytics tool |

```bash
# Filter LLM calls from telemetry
cat logs/research.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    if e.get('event_type') == 'llm_call':
        print(e)
"
```

## Files

| File | Purpose |
|---|---|
| `state.py` | `ResearchState` TypedDict — shared pipeline state |
| `agents.py` | Five agent nodes with full BMasterAI instrumentation |
| `graph.py` | LangGraph `StateGraph` with conditional reflection loop |
| `main.py` | CLI entry point with streaming progress + telemetry summary |
