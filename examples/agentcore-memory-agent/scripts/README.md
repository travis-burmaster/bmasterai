# scripts/

Setup and deployment automation. Run these in order when deploying for the first time.

## Files

### `setup_memory.py`

Creates the AgentCore Memory store with all three strategies (summary, user preference, semantic). Idempotent — if the store already exists, it prints the existing Memory ID.

```bash
python scripts/setup_memory.py
# Output: Memory ID: mem-xxxxxxxxxxxx
```

Run this first. You'll need the Memory ID for the `.env` file and deployment.

---

### `setup_telegram_webhook.sh`

Sets up the Telegram integration infrastructure:

1. Stores the bot token in AWS Secrets Manager
2. Creates a DynamoDB table for session tracking (with TTL enabled)
3. Packages the webhook Lambda
4. Prints deployment commands and webhook registration instructions

```bash
./scripts/setup_telegram_webhook.sh <BOT_TOKEN> [AWS_REGION]
```

Requires: AWS CLI configured, a bot token from [@BotFather](https://t.me/BotFather).

---

### `deploy.sh`

End-to-end deployment orchestrator:

1. Creates the memory store (calls `setup_memory.py`)
2. Optionally pauses for local testing
3. Deploys the agent to AgentCore Runtime (`agentcore deploy`)
4. Runs a verification invocation

```bash
./scripts/deploy.sh
```

Requires: `bedrock-agentcore-starter-toolkit` installed, AWS credentials configured.

## Deployment Order

```
1. python scripts/setup_memory.py           ← get Memory ID
2. cp .env.example .env                     ← fill in values
3. ./scripts/deploy.sh                      ← deploy agent
4. ./scripts/setup_telegram_webhook.sh      ← Telegram infra
5. Deploy webhook Lambda + API Gateway       ← (manual or IaC)
6. Register webhook URL with Telegram        ← (curl command printed by step 4)
```
