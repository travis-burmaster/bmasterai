import os
import requests
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone

ACKED = set()
MUTED = {}

TEAMS_WEBHOOK = os.getenv("BMASTERAI_ALERTS_TEAMS_WEBHOOK")

def send_teams_alert(agent, text, dashboard_url):
    if not TEAMS_WEBHOOK:
        return
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {"type": "TextBlock", "text": text, "wrap": True}
                    ],
                    "actions": [
                        {"type": "Action.Submit", "title": "Acknowledge", "data": {"action": "ack", "agent": agent}},
                        {"type": "Action.Submit", "title": "Mute 1h", "data": {"action": "mute_1h", "agent": agent}},
                        {"type": "Action.OpenUrl", "title": "Open Dashboard", "url": dashboard_url}
                    ]
                }
            }
        ]
    }
    requests.post(TEAMS_WEBHOOK, json=payload)

def handle_teams_action(body):
    action = body.get("data", {}).get("action")
    agent = body.get("data", {}).get("agent")

    if action == "ack":
        ACKED.add(agent)
        return JSONResponse({"text": f"✅ Acknowledged alerts for {agent}"})
    elif action == "mute_1h":
        MUTED[agent] = datetime.now(timezone.utc) + timedelta(hours=1)
        return JSONResponse({"text": f"🔇 Muted alerts for {agent} for 1 hour"})

    return JSONResponse({"text": "⚠️ Unknown action"})
