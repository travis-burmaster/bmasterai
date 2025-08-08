## Agno + BMasterAI Telemetry Example

This example shows how the [Agno](https://github.com/agno-ai/agno) agent framework can
call Google's Gemini models while recording rich BMasterAI telemetry.

### Why it's exciting

- **Native Agno agent** – uses the high level `Agent` interface to interact with Gemini.
- **Full observability** – BMasterAI logging and monitoring capture agent lifecycle
  events, token usage and latency metrics out of the box.
- **Minimal setup** – a single script demonstrates how to combine the two libraries.

### Requirements

- Python 3.10+
- Environment variable `GOOGLE_API_KEY` containing a valid Gemini API key.
- Install dependencies:

```bash
pip install agno google-generativeai bmasterai
```

### Run

```bash
export GOOGLE_API_KEY=your-key
python gemini_agno_example.py
```

The script prints the Gemini response and records structured telemetry in logs and metrics files.

