## Agno + BMasterAI Telemetry Example

This example shows how the [Agno](https://github.com/agno-ai/agno) agent framework can
call Google's Gemini models while recording rich BMasterAI telemetry and optionally
emitting alerts through the `bmasterai_telemetry` extension.

### Why it's exciting

- **Native Agno agent** – uses the high level `Agent` interface to interact with Gemini.
- **Full observability** – BMasterAI logging and monitoring capture agent lifecycle
  events, token usage and latency metrics out of the box.
- **Alerting hooks** – simple token budgets can trigger Slack or Teams alerts via
  `bmasterai_telemetry`.
- **Minimal setup** – a single script demonstrates how to combine the two libraries.

### Requirements

- Python 3.10+
- Environment variable `GOOGLE_API_KEY` containing a valid Gemini API key.
- (Optional) `BMASTERAI_ALERTS_SLACK_WEBHOOK` and/or `BMASTERAI_ALERTS_TEAMS_WEBHOOK`
  for alert delivery.
- Install dependencies:

```bash
pip install agno google-generativeai bmasterai
```

### Run

```bash
export GOOGLE_API_KEY=your-key
python gemini_agno_example.py
```
Set `TOKEN_BUDGET` to enable alerting when the token usage exceeds the limit. The script
prints the Gemini response and records structured telemetry in logs and metrics files,
sending optional alerts when budgets are breached.

