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
