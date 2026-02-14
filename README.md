# BMasterAI • Agent Learning Lab

> Learn how to build, instrument, and ship AI agents through polished, real-world examples that you can run end to end.

*Need the deep technical reference? Jump to [`README.content.md`](README.content.md).*

BMasterAI reframes multi-agent development as a hands-on learning studio. Instead of burying features in raw engineering docs, we surface real-world playbooks, storytelling assets, and telemetry hooks that help you understand how production-grade agents come together.

Whether you're new to agents or leveling up a team, every asset is designed to teach best practices while you ship polished experiences.

## Why Builders Choose BMasterAI
- **Story-first blueprints** – Each example pairs code with narrative context so you can see how an agent solves a real problem.
- **Telemetry-ready agents** – Track outcomes, reasoning, and costs out of the box to learn how production monitoring is done.
- **Enterprise-ready launchpad** – From laptop experiments to Kubernetes rollouts, the same agents scale without rework.

## Pick Your Learning Track
- **Start Fast** → `docs/getting-started.md`, `lessons/` walkthroughs, and `examples/basic_usage.py` get a chatbot live in minutes.
- **Build Skills** → follow the `lessons/` workshops and remix prompts inside `examples/` folders to learn agent patterns hands-on.
- **Explore Scenarios** → the `examples/` catalog curates industry narratives (finance, real estate, growth) to study end-to-end flows.
- **Scale the Story** → `k8s/`, `helm/`, and telemetry packages show how to operate agents in real deployments.

## Featured Agent Playbooks
- **Launch in Minutes** – [`examples/basic_usage.py`](examples/basic_usage.py), [`examples/minimal-rag/`](examples/minimal-rag/), [`examples/enhanced_examples.py`](examples/enhanced_examples.py)
- **Industry Spotlights** – [`examples/ai-real-estate-agent-team/`](examples/ai-real-estate-agent-team/), [`examples/ai-stock-research-agent/`](examples/ai-stock-research-agent/), [`examples/ai-sports_betting_analysis/`](examples/ai-sports_betting_analysis/)
- **Executive Insights** – [`examples/ai-stress-linkedin-reasoning/`](examples/ai-stress-linkedin-reasoning/), [`examples/reasoning_logging_example.py`](examples/reasoning_logging_example.py)
- **Interactive Launch Assets** – [`examples/gemini-reasoning-streamlit/`](examples/gemini-reasoning-streamlit/), [`examples/mcp-github-streamlit/`](examples/mcp-github-streamlit/), [`examples/streamlit-app/`](examples/streamlit-app/)
- **Operations & Telemetry** – [`examples/kubernetes-telemetry/`](examples/kubernetes-telemetry/), [`examples/agno-telemetry/`](examples/agno-telemetry/), [`examples/openclaw-telemetry/`](examples/openclaw-telemetry/) (OpenClaw AI agent observability), [`bmasterai_telemetry/`](bmasterai_telemetry/)

Use these playbooks to study prompts, orchestration patterns, and telemetry practices. Rebuild them locally, experiment with your own data, then adapt the flows to your projects when you're ready.

## Getting Started
```bash
# Set up a local studio
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai
python3 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]

# Run your first agent
python examples/basic_usage.py
```
Add telemetry (optional): `pytest --cov=src/bmasterai`, `python examples/reasoning_logging_example.py`, or stream data into the dashboards under `examples/kubernetes-telemetry/`.

## Build, Measure, Scale
- **Document what you learn** – Update `docs/` with runbooks, troubleshooting notes, and walkthroughs for future learners.
- **Instrument outcomes** – Use `src/bmasterai/logging.py` and `bmasterai_telemetry/` to capture success metrics and decision trails.
- **Deploy with confidence** – Follow `README-k8s.md` and `docs/kubernetes-deployment.md` to graduate from demo to production.

## Share What You Discover
We welcome new tutorials, walkthroughs, and refined playbooks. Open a PR with:
- A clear learning objective for the agent or workflow
- Screenshots, Looms, or Streamlit share links that reinforce the lesson
- Lessons learned so others can replicate (or extend) your approach

Let’s build the go-to showcase for learning AI agent excellence—one playbook at a time.