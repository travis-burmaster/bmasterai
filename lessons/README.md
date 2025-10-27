# BMasterAI Learning Campaigns

*Prefer the detailed syllabus view? See [`README.content.md`](README.content.md) in this folder.*

Welcome to the programming calendar for agent skill-building. Each lesson is designed as a live workshop or self-paced lab you can run for teammates, cohorts, or community groups exploring agent-powered workflows.

## Curriculum Highlights
- **Lesson 01 · GitHub MCP + Streamlit** (`lesson-01-github-mcp-streamlit/`)
  - Format: 60-minute interactive build-along focused on teaching agent orchestration fundamentals
  - Storyline: Turn repository audits into a sharable Streamlit report powered by MCP agents
  - Assets: Slide deck prompts, feature request worksheet, demo checklist

- **Shared Resources** (`shared/`)
  - `repository-analysis-guide.md` – Use as a pre-read or follow-up reference for technical audiences
  - `feature-request-workflow.md` – Workshop script for guiding learners from idea to shipped agent

## How to Run a Session
1. **Align on the Hook** – Clarify who you are teaching (e.g., product engineers, applied scientists) and the aha moment you want them to share.
2. **Prep the Assets** – Clone the repository, provision API keys, and share the worksheets from `shared/`.
3. **Tell the Story** – Narrate the business problem first, then walk through the agent build with code, telemetry, and outcomes.
4. **Capture Proof** – Encourage participants to save dashboards, reasoning logs, or Streamlit outputs for review and reflection.
5. **Package the Win** – Update this folder with tweaks, scripts, or new lesson directories so the next facilitator has the latest playbook.

## Prerequisites (Share Ahead of Time)
- Accounts: GitHub + OpenAI (or alternate LLM provider)
- Tools: Python 3.8+, Node.js 18+, Git, optional Docker for container segments
- Skills: Comfortable with basic CLI usage and reading Python scripts

## Extend the Series
Want to add a new workshop? Create `lesson-0X-topic/` with:
```
lesson-0X-topic/
├── README.md          # Session outline + talking points
├── assets/            # Slides, imagery, or video notes
├── code-examples/     # Demo scripts and snippets
├── exercises/         # Hands-on challenges
└── recap/             # Post-session metrics, testimonials, follow-up links
```
Then submit a PR describing the audience, promise, and key takeaways. Let’s grow a catalogue of agent learning experiences people love to attend.
