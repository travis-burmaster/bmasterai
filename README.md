# BMasterAI • Agent Learning Lab

> Launch compelling AI agent experiences, showcase them like case studies, and teach your team how to ship with confidence.

*Need the deep technical reference? Jump to [`README.content.md`](README.content.md).*

BMasterAI reframes multi-agent development as a marketing-ready product studio. Instead of burying features in raw engineering docs, we surface real-world playbooks, storytelling assets, and telemetry hooks that help you promote every agent you build.

Whether you're new to agents or leveling up a team, every asset is designed to teach best practices while you ship polished experiences.

## Why Builders Choose BMasterAI
- **Story-first blueprints** – Each example doubles as a mini campaign with positioning, value props, and demo scripts.
- **Telemetry-ready agents** – Track outcomes, reasoning, and costs out of the box so your marketing and product teams can brag with data.
- **Enterprise-ready launchpad** – From laptop experiments to Kubernetes rollouts, the same agents scale without rework.

## Pick Your Learning Track
- **Start Fast** → `docs/getting-started.md`, `lessons/` walkthroughs, and `examples/basic_usage.py` get a chatbot live in minutes.
- **Build Skills** → follow the `lessons/` workshops and remix prompts inside `examples/` folders to learn agent patterns hands-on.
- **Ship Experiences** → `examples/` catalog curates industry narratives (finance, real estate, growth) you can customize for demos.
- **Scale the Story** → `k8s/`, `helm/`, and telemetry packages show how to operate agents in production campaigns.

## Featured Agent Playbooks
- **Launch in Minutes** – [`examples/basic_usage.py`](examples/basic_usage.py), [`examples/minimal-rag/`](examples/minimal-rag/), [`examples/enhanced_examples.py`](examples/enhanced_examples.py)
- **Industry Spotlights** – [`examples/ai-real-estate-agent-team/`](examples/ai-real-estate-agent-team/), [`examples/ai-stock-research-agent/`](examples/ai-stock-research-agent/), [`examples/ai-sports_betting_analysis/`](examples/ai-sports_betting_analysis/)
- **Executive Insights** – [`examples/ai-stress-linkedin-reasoning/`](examples/ai-stress-linkedin-reasoning/), [`examples/reasoning_logging_example.py`](examples/reasoning_logging_example.py)
- **Interactive Launch Assets** – [`examples/gemini-reasoning-streamlit/`](examples/gemini-reasoning-streamlit/), [`examples/mcp-github-streamlit/`](examples/mcp-github-streamlit/), [`examples/streamlit-app/`](examples/streamlit-app/)
- **Operations & Telemetry** – [`examples/kubernetes-telemetry/`](examples/kubernetes-telemetry/), [`examples/agno-telemetry/`](examples/agno-telemetry/), [`bmasterai_telemetry/`](bmasterai_telemetry/)

Use these playbooks as templates for blog posts, launch landing pages, webinars, or customer enablement decks. Each directory includes scripts, assets, or configs you can remix into your own campaign.

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
- **Document the story** – Update `docs/` with campaign briefs and customer journeys as you ship new agents.
- **Instrument outcomes** – Use `src/bmasterai/logging.py` and `bmasterai_telemetry/` to capture success metrics and decision trails.
- **Deploy with confidence** – Follow `README-k8s.md` and `docs/kubernetes-deployment.md` to graduate from demo to production.

## Join the Campaign
We welcome community stories, launch recaps, and new playbooks. Open a PR with:
- A marketing-ready description of your agent
- Screenshots, Looms, or Streamlit share links
- Lessons learned so others can replicate your win

Let’s build the go-to showcase of AI agent excellence—one playbook at a time.