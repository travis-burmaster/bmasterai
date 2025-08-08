# bmasterai_telemetry/alerts_api.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from bmasterai_telemetry.alerts.slack import handle_slack_action
from bmasterai_telemetry.alerts.teams import handle_teams_action

app = FastAPI()

@app.post("/alerts/slack/actions")
async def slack_actions(request: Request):
    payload = await request.form()
    return await handle_slack_action(payload.get("payload"))

@app.post("/alerts/teams/actions")
async def teams_actions(request: Request):
    body = await request.json()
    return await handle_teams_action(body)

# bmasterai_telemetry/alerts/slack.py
import os, json
import requests
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

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
        MUTED[agent] = datetime.utcnow() + timedelta(hours=1)
        return JSONResponse({"text": f"🔇 Muted alerts for {agent} for 1 hour"})

    return JSONResponse({"text": "⚠️ Unknown action"})

# bmasterai_telemetry/alerts/teams.py
import os
import requests
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

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
        MUTED[agent] = datetime.utcnow() + timedelta(hours=1)
        return JSONResponse({"text": f"🔇 Muted alerts for {agent} for 1 hour"})

    return JSONResponse({"text": "⚠️ Unknown action"})

# examples/agno/quickstart/send_test_alert.py
import os
from bmasterai_telemetry.alerts.slack import send_slack_alert, build_slack_alert
from bmasterai_telemetry.alerts.teams import send_teams_alert

agent = "agent-test"
text = f"🚨 Budget breach for agent {agent}: $27.63 used > $25.00 limit"
dashboard_url = "http://localhost:3000/d/agent-dashboard"

# Send to Slack
slack_payload = build_slack_alert(text, dashboard_url)
send_slack_alert(slack_payload)

# Send to Teams
send_teams_alert(agent, text, dashboard_url)

print("✅ Test alerts sent to Slack and Teams.")
