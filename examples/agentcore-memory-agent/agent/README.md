# agent/

The AgentCore Runtime entrypoint. This is the module that AgentCore loads when your agent is invoked.

## Files

### `main.py`

The core of the agent. Contains:

- **`handler(event, context)`** — The Lambda-style entrypoint that AgentCore Runtime calls. Receives a JSON payload with `actor_id`, `session_id`, and `prompt`. Returns a JSON response with the agent's output.

- **`create_agent(actor_id, session_id, user_message)`** — Factory that builds a Strands `Agent` for each request. It:
  1. Retrieves relevant long-term memories for the user
  2. Builds a personalized system prompt with those memories injected
  3. Configures the Bedrock model (Claude by default)
  4. Registers all tools (bash, browser, telegram)
  5. Returns the assembled agent ready to run

- **`build_system_prompt(memories)`** — Formats retrieved memory records into a natural-language block that gets injected into the system prompt template.

## How It Works

Each incoming request follows this flow:

```
event → retrieve memories → build prompt → create agent → run agent → store turn → return response
```

The agent is stateless between invocations. All state lives in AgentCore Memory (conversation context) and DynamoDB (session tracking). This means each request builds a fresh agent from scratch — memory retrieval is what provides continuity.

## System Prompt Design

The system prompt template tells the agent:
1. What capabilities it has (bash, browser, telegram)
2. What memories are relevant to this conversation
3. How to behave (concise for mobile, reference past conversations naturally)

Memory records are formatted with their strategy type (summary, preference, fact) so the agent can weigh them appropriately.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_ID` | (required) | AgentCore Memory store ID |
| `MODEL_ID` | `anthropic.claude-sonnet-4-20250514-v1:0` | Bedrock model identifier |
| `AWS_REGION` | `us-east-1` | AWS region for all clients |
