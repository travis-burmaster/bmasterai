# webhook/

The inbound Telegram webhook handler. Deployed as an AWS Lambda behind API Gateway.

## Files

### `handler.py`

Receives HTTP POST requests from Telegram's webhook system, translates them into AgentCore Runtime invocations, and sends the agent's response back.

## Request Flow

```
Telegram servers
       │
       ▼ (POST /webhook)
API Gateway (HTTP API)
       │
       ▼
lambda_handler(event, context)
       │
       ├── Parse message from Telegram JSON payload
       ├── Check for commands (/start, /forget, /newsession)
       │
       ├── Get or create session (DynamoDB lookup)
       ├── Send "typing..." indicator to Telegram
       ├── Invoke AgentCore agent
       ├── Send response back to Telegram
       │
       └── Return 200 (always, even on errors)
```

## Session Management

Sessions are tracked in a DynamoDB table (`telegram-agent-sessions`):

| Field | Type | Description |
|-------|------|-------------|
| `chat_id` | String (PK) | Telegram chat ID |
| `session_id` | String | AgentCore session identifier |
| `last_active` | Number | Unix timestamp of last activity |
| `ttl` | Number | DynamoDB TTL for automatic cleanup |

Sessions expire after 30 minutes of inactivity (`SESSION_TTL_SECONDS`). When a user sends a message after expiry, a new session is created. This triggers AgentCore to generate a summary memory record for the expired session.

## Telegram Commands

| Command | Handler |
|---------|---------|
| `/start` | Sends a welcome message with capability overview |
| `/forget` | Deletes all stored memories (GDPR). Calls `MemoryManager.delete_actor_memories()` |
| `/newsession` | Deletes the DynamoDB session record, forcing a fresh session |

## Deployment

The Lambda needs:
- **Runtime:** Python 3.12
- **Timeout:** 120 seconds (agent execution can take time)
- **Memory:** 256 MB
- **IAM permissions:** `bedrock-agentcore:InvokeAgent`, `secretsmanager:GetSecretValue`, `dynamodb:GetItem/PutItem/UpdateItem/DeleteItem`
- **Environment variables:** `AGENTCORE_AGENT_ID`, `MEMORY_ID`, `SESSION_TABLE`, `TELEGRAM_BOT_TOKEN_SECRET`

Deploy behind an API Gateway HTTP API with a single `POST /webhook` route.

## Registering the Webhook

After deployment, register the API Gateway URL with Telegram:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://<API_GW_ID>.execute-api.<REGION>.amazonaws.com/webhook"}'
```

Verify:
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

## Error Handling

The handler always returns HTTP 200 to Telegram. This is critical because Telegram retries non-200 responses aggressively, which can cause message loops and duplicate agent invocations. Errors are logged to CloudWatch for debugging.
