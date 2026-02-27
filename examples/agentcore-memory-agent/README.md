# AgentCore Memory Agent + BMasterAI Telemetry

A Telegram bot with persistent memory, built on [AWS Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html) and instrumented with [BMasterAI](https://github.com/travis-burmaster/bmasterai) structured telemetry. The agent remembers past conversations, learns user preferences over time, and can execute bash commands, search the web, and send rich Telegram messages — all governed by Cedar security policies and fully observable via BMasterAI logging.

## BMasterAI Telemetry

Every agent lifecycle event is captured as a structured log entry:

| Component | Events Logged |
|---|---|
| `agent/main.py` | `AGENT_START`, `TASK_START`, `TASK_COMPLETE`, `TASK_ERROR`, `LLM_CALL`, `TOOL_USE`, `DECISION_POINT`, `PERFORMANCE_METRIC` |
| `memory/manager.py` | `TOOL_USE` (store), `TASK_COMPLETE`, `TASK_ERROR`, `DECISION_POINT` (retrieve), `PERFORMANCE_METRIC`, `AGENT_COMMUNICATION` (session close / GDPR delete) |
| `webhook/handler.py` | `AGENT_START`, `TASK_START`, `TASK_COMPLETE`, `TASK_ERROR`, `LLM_CALL`, `AGENT_COMMUNICATION`, `DECISION_POINT` |

Logs are written to three sinks simultaneously:
- **Console** — human-readable during development
- `logs/bmasterai.log` — flat file for CloudWatch ingestion
- `logs/bmasterai.jsonl` — structured JSONL for analytics / dashboards

---

## What It Does

Send a message to the Telegram bot and it will respond using Claude (or any Bedrock model). Behind the scenes, the agent retrieves relevant memories from past conversations, personalizes its response, and stores the new interaction for future reference.

**Capabilities:**

- **Persistent Memory** — Remembers facts, preferences, and conversation summaries across sessions using AgentCore's three memory strategies (summary, user preference, semantic).
- **Bash Execution** — Runs shell commands in a sandboxed Code Interpreter for computations, file processing, and automation.
- **Web Search** — Searches the web and extracts page content using AgentCore's managed Browser tool.
- **Telegram Integration** — Sends text messages, documents, and photos back to the user. Supports commands like `/start`, `/forget` (GDPR deletion), and `/newsession`.
- **Policy Governance** — All tool access is gated by Cedar policies enforced at the AgentCore Gateway boundary, preventing the LLM from bypassing security controls.

---

## Architecture

```
Telegram ──► API Gateway ──► webhook/handler.py (Lambda)
                                    │
                                    ▼
                          AgentCore Runtime
                          ┌─────────────────┐
                          │  agent/main.py   │
                          │                  │
                          │  Memory Manager  │──► AgentCore Memory
                          │                  │    (short-term + long-term)
                          │  Tools:          │
                          │  ├─ Bash         │──► Code Interpreter
                          │  ├─ Browser      │──► AgentCore Browser
                          │  └─ Telegram     │──► Telegram Bot API
                          └─────────────────┘
                                    │
                              Cedar Policies
                          (enforced at Gateway)
```

---

## Prerequisites

- Python 3.12+
- AWS CLI configured with appropriate permissions
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- AWS account with Bedrock AgentCore access

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create the memory store

```bash
python scripts/setup_memory.py
# Output: Memory ID: mem-xxxxxxxxxxxx
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your MEMORY_ID, AWS region, etc.
```

### 4. Test locally

```bash
# Terminal 1
agentcore dev

# Terminal 2
agentcore invoke --dev '{"actor_id": "tg_test", "session_id": "test_1", "prompt": "Hello! Remember that my name is Travis."}'

# Verify memory works
agentcore invoke --dev '{"actor_id": "tg_test", "session_id": "test_1", "prompt": "What is my name?"}'
```

### 5. Deploy

```bash
agentcore deploy
```

### 6. Set up Telegram webhook

```bash
./scripts/setup_telegram_webhook.sh <YOUR_BOT_TOKEN>
```

Then deploy the webhook Lambda behind API Gateway and register the URL with Telegram (the script prints the exact commands).

### 7. Try it out

Send `/start` to your bot on Telegram.

---

## Project Structure

| Path | Purpose |
|------|---------|
| `agentcore.yaml` | AgentCore project configuration — model, memory strategies, tool registration, policy engine, observability settings |
| `agent/main.py` | Runtime entrypoint. Builds a memory-hydrated system prompt, creates the Strands agent with all tools, and stores conversation turns |
| `memory/manager.py` | `MemoryManager` class wrapping AgentCore's data-plane APIs for storing turns and retrieving long-term memories |
| `tools/bash_tool.py` | Sandboxed bash execution via AgentCore Code Interpreter. Includes client-side command blocklist as defense-in-depth |
| `tools/browser_tool.py` | Web search and URL fetching via AgentCore Browser. Launches ephemeral Chromium sessions, extracts text |
| `tools/telegram_tool.py` | Telegram Bot API wrapper for sending messages, documents, and photos. Token loaded from Secrets Manager |
| `webhook/handler.py` | Lambda function receiving Telegram webhooks. Manages sessions in DynamoDB, invokes the agent, sends replies |
| `policies/agent_policies.cedar` | Cedar policies governing tool access — scoped bash execution, browser URL restrictions, user-bound messaging |
| `scripts/setup_memory.py` | One-time script to create the AgentCore Memory store with all three strategies |
| `scripts/setup_telegram_webhook.sh` | Stores bot token in Secrets Manager, creates DynamoDB session table, prints webhook registration commands |
| `scripts/deploy.sh` | End-to-end deployment orchestrator (memory → deploy → verify) |

---

## Memory System

The agent uses three complementary memory strategies that work together:

**Short-term memory** captures each conversation turn as an event. This gives the agent context within a single session (e.g., understanding that "What about tomorrow?" refers to a previously mentioned city).

**Long-term memory** is extracted automatically by AgentCore in the background:

| Strategy | What It Captures | Example |
|----------|-----------------|---------|
| **Session Summary** | Compressed overview of each session | "User asked about Seattle restaurants and booked a table at Canlis" |
| **User Preference** | Learned preferences and patterns | "Prefers concise responses. Interested in Python and DevOps." |
| **Semantic Facts** | Extractable knowledge and facts | "User's name is Travis. Works at Acme Corp." |

Before each response, the agent queries all three strategies with the user's message and injects the most relevant memories into the system prompt. This keeps the agent personalized without bloating the context window.

---

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Introduction message with capabilities overview |
| `/newsession` | Force-start a fresh conversation session |
| `/forget` | Delete all stored memories for your account (GDPR) |

Sessions auto-expire after 30 minutes of inactivity.

---

## Security Model

Security is enforced at multiple layers:

1. **Cedar Policies (primary)** — Evaluated at the AgentCore Gateway boundary, outside the agent's code. The LLM cannot bypass these. Policies control which tools the agent can call and with what parameters.

2. **Tool-level safety (defense-in-depth)** — The bash tool blocks dangerous command prefixes. The browser tool blocks private IP navigation. Telegram messaging is scoped to the requesting user.

3. **Secrets management** — The bot token lives in AWS Secrets Manager, never in code or environment variables.

4. **Session isolation** — Each AgentCore Browser session runs in an isolated container. Code Interpreter runs in a sandbox.

---

## Configuration

All configuration lives in `agentcore.yaml` and `.env`:

**Model:** Change `model.model_id` in `agentcore.yaml` to use any Bedrock-available model (Claude, Nova, Llama, Mistral).

**Memory retention:** Adjust `memory.event_expiry_days` to control how long raw events are kept. Long-term memories persist independently.

**Browser timeout:** Adjust `tools.browser.session_timeout_minutes` (default 15, max 480).

**Session TTL:** Change `SESSION_TTL_SECONDS` in `webhook/handler.py` (default 1800 = 30 minutes).

---

## Extending the Agent

### Adding a new tool

1. Create `tools/your_tool.py` with `@tool`-decorated functions
2. Add a wrapper class with `__call__` returning the functions
3. Register in `agent/main.py` → `create_agent()`
4. Add a Cedar `permit` policy in `policies/agent_policies.cedar`
5. Update `agentcore.yaml` if the tool needs Gateway config

### Adding a Telegram command

Add a handler in `webhook/handler.py` → `lambda_handler()` under the commands section, following the `/start` and `/forget` patterns.

---

## Cost Considerations

- **AgentCore Runtime** — Consumption-based, no minimums.
- **AgentCore Memory** — Charged per event stored and per retrieval.
- **AgentCore Browser** — Each session spins up a container. For pure search (no full browsing needed), consider replacing with a search API (Brave, SerpAPI) behind Gateway.
- **DynamoDB** — PAY_PER_REQUEST mode, negligible for session tracking.
- **Secrets Manager** — $0.40/secret/month + $0.05 per 10K API calls.

---

## Troubleshooting

**Agent doesn't respond on Telegram**
Check CloudWatch logs for the webhook Lambda. Verify the webhook is registered: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

**Memory isn't working**
Long-term memory extraction is asynchronous. Wait a few seconds after storing a turn, then check with `retrieve_memory_records`. Run `python scripts/setup_memory.py` to verify the memory store exists.

**Tool calls are blocked**
Cedar is deny-by-default. If you added a new tool without a `permit` policy, it will be silently blocked. Check the policy engine logs in CloudWatch.

**Browser sessions timing out**
Increase `session_timeout_minutes` in `agentcore.yaml`. The maximum is 480 minutes (8 hours).

---

## References

- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)
- [AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [AgentCore Browser](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/browser-tool.html)
- [AgentCore Policy (Cedar)](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html)
- [Strands Agents SDK](https://github.com/strands-agents/strands-agents)
- [Cedar Policy Language](https://www.cedarpolicy.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Sample Code](https://github.com/awslabs/amazon-bedrock-agentcore-samples/)
