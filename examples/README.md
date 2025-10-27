# Agent Playbook Catalog

Every directory in `examples/` is a self-contained learning module. Use this catalog to pick a scenario, dissect how it works, and practice adapting the agent to your own data or workflows.

## Quick Picks
- **Rapid Launchers** – [`basic_usage.py`](basic_usage.py), [`minimal-rag/`](minimal-rag/), [`enhanced_examples.py`](enhanced_examples.py)
- **Industry Wins** – [`ai-real-estate-agent-team/`](ai-real-estate-agent-team/), [`ai-stock-research-agent/`](ai-stock-research-agent/), [`ai-sports_betting_analysis/`](ai-sports_betting_analysis/)
- **Decision Intelligence** – [`ai-stress-linkedin-reasoning/`](ai-stress-linkedin-reasoning/), [`reasoning_logging_example.py`](reasoning_logging_example.py)
- **Experience Layers** – [`gemini-reasoning-streamlit/`](gemini-reasoning-streamlit/), [`mcp-github-streamlit/`](mcp-github-streamlit/), [`streamlit-app/`](streamlit-app/), [`gradio-anthropic/`](gradio-anthropic/)
- **Operations & Telemetry** – [`kubernetes-telemetry/`](kubernetes-telemetry/), [`agno-telemetry/`](agno-telemetry/), [`google-adk/`](google-adk/)

## How to Activate a Playbook
1. **Clone the repo** and install dependencies (`pip install -e .[dev]`).
2. **Open the example** folder, read the README or inline notes, and identify the skills you want to practice.
3. **Run the scripts** – follow the setup steps, observe the agent flow, and inspect the telemetry that is generated.
4. **Experiment** – tweak prompts, swap tools, or adjust workflows to see how the agent responds.
5. **Share your learnings** – document what worked (and what didn’t) so future contributors can build on your insights.

## Contribute a New Playbook
Create a folder named after the outcome (e.g., `ai-patient-intake-navigator/`). Include:
- `README.md` describing the learning objective, prerequisites, and success criteria
- Demo scripts or notebooks
- Suggested follow-up exercises or variations for learners

Then open a PR highlighting the skills covered, datasets or APIs required, and telemetry dashboards that help learners validate their results.
