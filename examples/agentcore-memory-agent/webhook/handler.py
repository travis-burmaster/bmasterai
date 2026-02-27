"""
Telegram Webhook Handler
========================
An AWS Lambda function that receives Telegram webhook updates,
translates them into AgentCore Runtime invocations, and sends
the agent's response back to the user.

BMasterAI telemetry is instrumented on every webhook event,
session transition, agent invocation, and delivery path.

Deployment:
  - Fronted by API Gateway (HTTP API)
  - Telegram webhook URL → https://<api-gw-id>.execute-api.<region>.amazonaws.com/webhook
  - Set via: POST https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WEBHOOK_URL>
"""

import hashlib
import json
import logging
import os
import time

import boto3

from bmasterai.logging import configure_logging, LogLevel, EventType

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# BMasterAI — structured telemetry
# ---------------------------------------------------------------------------
bm = configure_logging(
    log_level=LogLevel.INFO,
    enable_console=True,
    enable_file=True,
    enable_json=True,
)

_AGENT_ID = "agentcore-memory-agent-webhook"

# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
agentcore = boto3.client("bedrock-agentcore", region_name=os.environ.get("AWS_REGION", "us-east-1"))
secrets = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION", "us-east-1"))
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))

# Environment
AGENT_ID = os.environ["AGENTCORE_AGENT_ID"]
SESSION_TABLE = os.environ.get("SESSION_TABLE", "telegram-agent-sessions")
BOT_TOKEN_SECRET = os.environ.get(
    "TELEGRAM_BOT_TOKEN_SECRET",
    "arn:aws:secretsmanager:us-east-1:000000000000:secret:telegram-bot-token",
)

# Session TTL: 30 minutes of inactivity → new session
SESSION_TTL_SECONDS = 1800

# DynamoDB table for session tracking
sessions_table = dynamodb.Table(SESSION_TABLE)


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def _get_or_create_session(chat_id: str) -> str:
    """
    Retrieve an active session for this chat, or create a new one.
    Sessions expire after 30 minutes of inactivity.
    """
    now = int(time.time())
    t0 = time.monotonic()

    bm.log_event(
        agent_id=_AGENT_ID,
        event_type=EventType.DECISION_POINT,
        message="Looking up session for chat",
        metadata={"chat_id": chat_id},
    )

    try:
        resp = sessions_table.get_item(Key={"chat_id": str(chat_id)})
        item = resp.get("Item")

        if item and (now - int(item.get("last_active", 0))) < SESSION_TTL_SECONDS:
            sessions_table.update_item(
                Key={"chat_id": str(chat_id)},
                UpdateExpression="SET last_active = :now",
                ExpressionAttributeValues={":now": now},
            )
            session_id = item["session_id"]
            bm.log_event(
                agent_id=_AGENT_ID,
                event_type=EventType.AGENT_COMMUNICATION,
                message="Resumed existing session",
                metadata={"chat_id": chat_id, "session_id": session_id},
                duration_ms=(time.monotonic() - t0) * 1000,
            )
            return session_id

    except Exception as exc:
        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.TASK_ERROR,
            message=f"Session lookup failed, creating new: {exc}",
            metadata={"chat_id": chat_id, "error": str(exc)},
        )
        logger.warning("Session lookup failed, creating new session")

    # Create a new session
    session_id = f"sess_{chat_id}_{now}"
    sessions_table.put_item(
        Item={
            "chat_id": str(chat_id),
            "session_id": session_id,
            "last_active": now,
            "ttl": now + SESSION_TTL_SECONDS * 2,
        }
    )

    bm.log_event(
        agent_id=_AGENT_ID,
        event_type=EventType.AGENT_COMMUNICATION,
        message="Created new session",
        metadata={"chat_id": chat_id, "session_id": session_id},
        duration_ms=(time.monotonic() - t0) * 1000,
    )

    logger.info("Created new session=%s for chat=%s", session_id, chat_id)
    return session_id


# ---------------------------------------------------------------------------
# AgentCore invocation
# ---------------------------------------------------------------------------

def _invoke_agent(actor_id: str, session_id: str, prompt: str) -> str:
    """Invoke the AgentCore Runtime agent and return its text response."""
    t0 = time.monotonic()

    bm.log_event(
        agent_id=_AGENT_ID,
        event_type=EventType.LLM_CALL,
        message="Invoking AgentCore Runtime agent",
        metadata={
            "actor_id": actor_id,
            "session_id": session_id,
            "agent_id": AGENT_ID,
            "prompt_len": len(prompt),
        },
    )

    response = agentcore.invoke_agent(
        agentId=AGENT_ID,
        payload=json.dumps({
            "actor_id": actor_id,
            "session_id": session_id,
            "prompt": prompt,
        }),
    )
    result = json.loads(response["body"].read())
    duration_ms = (time.monotonic() - t0) * 1000

    if result.get("status") == "success":
        response_text = result.get("response", "Sorry, I couldn't generate a response.")
        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.TASK_COMPLETE,
            message="AgentCore invocation succeeded",
            metadata={
                "actor_id": actor_id,
                "session_id": session_id,
                "response_len": len(response_text),
            },
            duration_ms=duration_ms,
        )
        return response_text
    else:
        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.TASK_ERROR,
            message="AgentCore returned error status",
            metadata={
                "actor_id": actor_id,
                "session_id": session_id,
                "agent_message": result.get("message"),
            },
            duration_ms=duration_ms,
        )
        logger.error("Agent returned error: %s", result.get("message"))
        return "I encountered an error processing your request. Please try again."


# ---------------------------------------------------------------------------
# Telegram response helper
# ---------------------------------------------------------------------------

def _send_telegram_reply(chat_id: str, text: str) -> None:
    """Send a reply directly via the Telegram Bot API (for the webhook response)."""
    import requests

    t0 = time.monotonic()

    bm.log_event(
        agent_id=_AGENT_ID,
        event_type=EventType.AGENT_COMMUNICATION,
        message="Sending Telegram reply",
        metadata={"chat_id": chat_id, "text_len": len(text)},
    )

    token_response = secrets.get_secret_value(SecretId=BOT_TOKEN_SECRET)
    token = json.loads(token_response["SecretString"])["bot_token"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)]

    for i, chunk in enumerate(chunks):
        requests.post(url, json={
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
        }, timeout=10)

    bm.log_event(
        agent_id=_AGENT_ID,
        event_type=EventType.TASK_COMPLETE,
        message=f"Telegram reply sent ({len(chunks)} chunk(s))",
        metadata={"chat_id": chat_id, "chunks": len(chunks)},
        duration_ms=(time.monotonic() - t0) * 1000,
    )


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    """
    Receives Telegram webhook updates via API Gateway.

    Supports:
      - Text messages
      - /start command
      - /forget command (GDPR memory deletion)
      - /newsession command (force new session)
    """
    t0 = time.monotonic()

    bm.log_event(
        agent_id=_AGENT_ID,
        event_type=EventType.AGENT_START,
        message="Webhook Lambda invoked",
        metadata={"request_id": getattr(context, "aws_request_id", "local")},
    )

    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.TASK_ERROR,
            message="Invalid JSON in webhook body",
            metadata={},
        )
        return {"statusCode": 400, "body": "Invalid JSON"}

    # Extract message
    message = body.get("message", {})
    if not message:
        return {"statusCode": 200, "body": "OK"}

    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "").strip()
    username = message.get("from", {}).get("username", "unknown")

    if not chat_id or not text:
        return {"statusCode": 200, "body": "OK"}

    actor_id = f"tg_{chat_id}"

    bm.log_event(
        agent_id=_AGENT_ID,
        event_type=EventType.TASK_START,
        message="Processing Telegram message",
        metadata={
            "actor_id": actor_id,
            "username": username,
            "text_preview": text[:80],
            "is_command": text.startswith("/"),
        },
    )

    logger.info("Received message from @%s (chat=%s): %s", username, chat_id, text[:100])

    # -----------------------------------------------------------------------
    # Handle commands
    # -----------------------------------------------------------------------
    if text == "/start":
        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.AGENT_COMMUNICATION,
            message="Handling /start command",
            metadata={"actor_id": actor_id},
        )
        _send_telegram_reply(
            chat_id,
            "Hi! I'm your AI assistant with persistent memory. "
            "I'll remember our conversations and learn your preferences over time.\n\n"
            "Just send me a message to get started. I can:\n"
            "- Search the web for information\n"
            "- Run code and commands\n"
            "- Remember things you tell me\n\n"
            "Commands:\n"
            "/newsession — Start a fresh conversation\n"
            "/forget — Delete all my memories of you",
        )
        return {"statusCode": 200, "body": "OK"}

    if text == "/forget":
        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.AGENT_COMMUNICATION,
            message="Handling /forget command — GDPR memory deletion",
            metadata={"actor_id": actor_id},
        )
        from memory.manager import MemoryManager
        mgr = MemoryManager(
            agentcore_data=boto3.client("bedrock-agentcore"),
            memory_id=os.environ["MEMORY_ID"],
        )
        mgr.delete_actor_memories(actor_id)
        _send_telegram_reply(chat_id, "Done — all your memories have been deleted.")
        return {"statusCode": 200, "body": "OK"}

    if text == "/newsession":
        bm.log_event(
            agent_id=_AGENT_ID,
            event_type=EventType.AGENT_COMMUNICATION,
            message="Handling /newsession command",
            metadata={"actor_id": actor_id},
        )
        sessions_table.delete_item(Key={"chat_id": chat_id})
        _send_telegram_reply(chat_id, "New session started. What can I help you with?")
        return {"statusCode": 200, "body": "OK"}

    # -----------------------------------------------------------------------
    # Normal message → invoke agent
    # -----------------------------------------------------------------------
    session_id = _get_or_create_session(chat_id)

    # Send "typing" indicator (best-effort)
    try:
        import requests
        token_response = secrets.get_secret_value(SecretId=BOT_TOKEN_SECRET)
        token = json.loads(token_response["SecretString"])["bot_token"]
        requests.post(
            f"https://api.telegram.org/bot{token}/sendChatAction",
            json={"chat_id": chat_id, "action": "typing"},
            timeout=5,
        )
    except Exception:
        pass

    response_text = _invoke_agent(actor_id, session_id, text)
    _send_telegram_reply(chat_id, response_text)

    bm.log_event(
        agent_id=_AGENT_ID,
        event_type=EventType.TASK_COMPLETE,
        message="Webhook request handled successfully",
        metadata={"actor_id": actor_id, "session_id": session_id},
        duration_ms=(time.monotonic() - t0) * 1000,
    )

    return {"statusCode": 200, "body": "OK"}
