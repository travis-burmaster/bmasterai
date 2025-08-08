import os, json
import requests
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone

ACKED = set()
MUTED = {}

SLACK_WEBHOOK = os.getenv("BMASTERAI_ALERTS_SLACK_WEBHOOK")

def send_slack_alert(payload):
    if not SLACK_WEBHOOK:
        return
    requests.post(SLACK_WEBHOOK, json=payload)

def build_slack_alert(text, dashboard_url):
    return {
        "text": text,
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "Acknowledge"}, "value": "ack", "action_id": "ack"},
                    {"type": "button", "text": {"type": "plain_text", "text": "Mute 1h"}, "value": "mute_1h", "action_id": "mute_1h"},
                    {"type": "button", "text": {"type": "plain_text", "text": "Open Dashboard"}, "url": dashboard_url, "action_id": "dashboard"}
                ]
            }
        ]
    }

def handle_slack_action(payload_json):
    payload = json.loads(payload_json)
    action = payload['actions'][0]['action_id']
    agent = payload['message']['text'].split()[3]  # crude parse: "🚨 Budget breach for agent X"

    if action == 'ack':
        ACKED.add(agent)
        return JSONResponse({"text": f"✅ Acknowledged alerts for {agent}"})
    elif action == 'mute_1h':
        MUTED[agent] = datetime.now(timezone.utc) + timedelta(hours=1)
        return JSONResponse({"text": f"🔇 Muted alerts for {agent} for 1 hour"})

    return JSONResponse({"text": "⚠️ Unknown action"})
