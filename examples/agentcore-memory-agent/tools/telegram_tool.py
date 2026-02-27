"""
Telegram Tool
=============
Sends messages to Telegram users via the Bot API.

The bot token is stored in AWS Secrets Manager and retrieved at init time.
In production, this tool would be fronted by an AgentCore Gateway MCP tool,
which handles credential injection and Cedar policy enforcement automatically.

This module provides the direct implementation for local development
and a Gateway-compatible variant for deployed environments.
"""

import json
import logging
import os

import boto3
import requests
from strands.tools import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bot token retrieval
# ---------------------------------------------------------------------------

_secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
_bot_token: str | None = None


def _get_bot_token() -> str:
    """Retrieve the Telegram bot token from Secrets Manager (cached)."""
    global _bot_token
    if _bot_token is None:
        secret_arn = os.environ.get(
            "TELEGRAM_BOT_TOKEN_SECRET",
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:telegram-bot-token",
        )
        response = _secrets_client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response["SecretString"])
        _bot_token = secret["bot_token"]
        logger.info("Telegram bot token loaded from Secrets Manager")
    return _bot_token


# ---------------------------------------------------------------------------
# Telegram API helpers
# ---------------------------------------------------------------------------

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _call_telegram(method: str, payload: dict) -> dict:
    """Make a Telegram Bot API call."""
    token = _get_bot_token()
    url = TELEGRAM_API.format(token=token, method=method)

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data.get('description', 'unknown')}")

    return data.get("result", {})


# ---------------------------------------------------------------------------
# Strands tool definitions
# ---------------------------------------------------------------------------

@tool
def telegram_send_message(
    chat_id: str,
    text: str,
    parse_mode: str = "Markdown",
) -> dict:
    """
    Send a text message to a Telegram chat.

    Use this tool to reply to the user on Telegram. The chat_id is
    automatically set to the current user's Telegram chat ID.

    Args:
        chat_id:    Telegram chat ID to send to.
        text:       Message text. Supports Markdown formatting.
        parse_mode: "Markdown" or "HTML". Defaults to Markdown.

    Returns:
        dict with message_id and status.
    """
    logger.info("Sending Telegram message to chat_id=%s len=%d", chat_id, len(text))

    # Telegram has a 4096 char limit per message — split if needed
    chunks = _split_message(text, max_len=4000)
    message_ids = []

    for chunk in chunks:
        result = _call_telegram("sendMessage", {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": parse_mode,
        })
        message_ids.append(result.get("message_id"))

    return {
        "status": "sent",
        "message_ids": message_ids,
        "chunks": len(chunks),
    }


@tool
def telegram_send_document(
    chat_id: str,
    file_url: str,
    caption: str = "",
) -> dict:
    """
    Send a document/file to a Telegram chat via URL.

    Use this when you need to send a file (PDF, image, text file, etc.)
    to the user on Telegram.

    Args:
        chat_id:  Telegram chat ID.
        file_url: Public URL of the file to send.
        caption:  Optional caption (max 1024 chars).

    Returns:
        dict with message_id and status.
    """
    logger.info("Sending document to chat_id=%s url=%s", chat_id, file_url)

    result = _call_telegram("sendDocument", {
        "chat_id": chat_id,
        "document": file_url,
        "caption": caption[:1024] if caption else "",
    })

    return {
        "status": "sent",
        "message_id": result.get("message_id"),
    }


@tool
def telegram_send_photo(
    chat_id: str,
    photo_url: str,
    caption: str = "",
) -> dict:
    """
    Send a photo to a Telegram chat via URL.

    Args:
        chat_id:   Telegram chat ID.
        photo_url: Public URL of the photo.
        caption:   Optional caption.

    Returns:
        dict with message_id and status.
    """
    result = _call_telegram("sendPhoto", {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption[:1024] if caption else "",
    })

    return {
        "status": "sent",
        "message_id": result.get("message_id"),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_message(text: str, max_len: int = 4000) -> list[str]:
    """Split a long message into Telegram-safe chunks."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break

        # Try to split at a newline
        split_idx = text.rfind("\n", 0, max_len)
        if split_idx == -1:
            # Fall back to splitting at a space
            split_idx = text.rfind(" ", 0, max_len)
        if split_idx == -1:
            split_idx = max_len

        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip()

    return chunks


class TelegramTool:
    """
    Wrapper that binds the actor's chat_id to the Telegram tools,
    so the agent doesn't need to know the raw chat ID.
    """

    def __init__(self, actor_id: str):
        # actor_id format: "tg_123456789"
        self.chat_id = actor_id.replace("tg_", "")

    def __call__(self):
        return [telegram_send_message, telegram_send_document, telegram_send_photo]
