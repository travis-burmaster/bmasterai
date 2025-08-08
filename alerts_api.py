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
