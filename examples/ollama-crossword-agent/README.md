# ollama-crossword-agent

A hybrid crossword-solving agent that combines **qwen2.5vl vision model** (via Ollama), **Playwright** browser automation, and **constraint logic** — fully instrumented with **BMasterAI** telemetry.

This agent demonstrates how to build a system where:
- A vision LLM proposes solutions (clue answers)
- Deterministic code enforces hard constraints (crossing letters must agree)
- The LLM is guided by feedback (context from crossing answers)

**Key insight:** The vision model is not the source of truth — the constraint engine is. Cells are only committed when all crossing answers agree, ensuring a valid grid solution.

---

## What It Demonstrates

- **Multimodal input:** Screenshots → vision model → structured clue extraction
- **Hybrid control:** LLM proposes, code decides (crossing constraint enforcement)
- **Retry with context:** Failed cells are re-solved with hints from committed crossings
- **Browser automation:** Navigate puzzle, take screenshots, type answers via Playwright
- **Full BMasterAI instrumentation:** Every LLM call, tool use, constraint decision is logged

---

## Architecture

```
┌─ Browser (Playwright)
│  ├─ Navigate to puzzle URL
│  ├─ Screenshot
│  └─ Type answers into grid
│
├─ Vision (Ollama qwen2.5vl:7b)
│  ├─ Extract clues from screenshot
│  └─ Propose answer for each clue (with crossing context)
│
└─ Constraint Engine (Python)
   ├─ Track grid state (3D: row, col, proposed_letters)
   ├─ For each cell: collect all proposed letters from crossing answers
   ├─ Commit only if: all crossings agree on the same letter
   ├─ Identify conflicts: cells where crossings disagree
   └─ Provide hints: "Across is C_A_E, Down is CHO_R → both have C at (0,0)"
```

**Solve loop (per round):**

```
1. Screenshot puzzle
2. Extract clues (round 1 only)
3. For each clue:
   a. Ask model: "Solve this clue, length=5, context: _ R _ N _"
   b. Collect proposed answers
4. Constraint engine:
   a. For each cell, check: do all crossing answers agree?
   b. If YES: commit letter
   c. If CONFLICT: mark for retry
5. Type committed answers into grid via Playwright
6. Repeat until solved or MAX_ROUNDS reached
```

---

## BMasterAI Instrumentation

Every step is tracked:

| Event | BMasterAI call | Details |
|---|---|---|
| Agent starts | `monitor.track_agent_start(AGENT_ID)` + `log_event(AGENT_START)` | URL, grid size, model |
| Screenshot taken | `log_event(TOOL_USE)` | PNG saved to screenshots/ |
| Clues extracted | `log_event(LLM_CALL)` | across + down count |
| Each answer proposed | `log_event(LLM_REASONING)` | clue, length, context, answer |
| Cells committed | `log_event(DECISION_POINT)` | count, empty cells remaining |
| Conflict detected | `log_event(TASK_ERROR)` | cell, proposed letters |
| Round complete | `monitor.track_task_duration(...)` | round latency |
| Puzzle solved | `log_event(TASK_COMPLETE)` | round number |
| Agent stops | `monitor.track_agent_stop(AGENT_ID)` + `log_event(AGENT_STOP)` | rounds used |

**Output files:**

```
logs/agent.log               — Human-readable event log
logs/agent.jsonl             — Structured JSON (analytics-ready)
logs/agent_reasoning.jsonl   — Decision points and reasoning chains
screenshots/round_*.png      — Puzzle state at each round
```

---

## Files

| File | Purpose |
|---|---|
| `agent.py` | Main `CrosswordAgent` class, solve loop, BMasterAI instrumentation |
| `grid.py` | `CrosswordGrid` state management, constraint engine |
| `vision.py` | Ollama vision helpers, clue extraction, answer proposal |
| `main.py` | CLI entry point, argument parsing |
| `requirements.txt` | Python dependencies |
| `.env.example` | Configuration template (no secrets needed) |

---

## Setup

### Prerequisites

- **Python 3.10+**
- **Ollama** running locally with `qwen2.5vl:7b` model
  ```bash
  # Install Ollama: https://ollama.ai
  # Pull the model:
  ollama pull qwen2.5vl:7b
  # Ollama should be running on http://localhost:11434 (default)
  ```

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Copy environment template
cp .env.example .env
```

### Verify Ollama

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If not, start it:
ollama serve  # on macOS/Linux
# or use the Ollama app (Windows/macOS)
```

---

## Usage

### Demo Mode (No Browser, No Ollama)

Test the example without setting up Ollama or a browser:

```bash
python main.py --demo
```

Output:
```
═══════════════════════════════════════════════════════════════════
🧩  ollama-crossword-agent
───────────────────────────────────────────────────────────────────
🎯  Puzzle: demo (hardcoded)
📊  Grid size: 5x5
🤖  Model: qwen2.5vl:7b
═══════════════════════════════════════════════════════════════════

📋  Demo mode: using hardcoded clues

🔄  Round 1/5
💭  Proposing answers (simulated)...
┌─────────────┐
│ I C E H O T │
│ _ _ _ _ _ │
│ T _ A _ _ │
│ E _ T _ _ │
│ A _ _ _ _ │
└─────────────┘

✅  Puzzle solved!

═══════════════════════════════════════════════════════════════════
📊  TELEMETRY DASHBOARD
───────────────────────────────────────────────────────────────────
Agent ID:           ollama-crossword-agent
Status:             completed
Rounds:             1/5
Grid state:         0 empty cells
Solved:             True
═══════════════════════════════════════════════════════════════════
```

### Real Mode (NYT Mini)

Solve the actual NYT Mini Crossword:

```bash
python main.py
# or
python main.py --url "https://www.nytimes.com/crosswords/game/mini"
```

### Custom Puzzle URL

```bash
python main.py --url "https://crosswordlabs.com/embed/puzzle123"
```

---

## Example Run Output

```
═══════════════════════════════════════════════════════════════════
🧩  ollama-crossword-agent
───────────────────────────────────────────────────────────────────
🎯  Puzzle: https://www.nytimes.com/crosswords/game/mini
📊  Grid size: 5x5
🤖  Model: qwen2.5vl:7b
═══════════════════════════════════════════════════════════════════

🌐  Navigating to puzzle...
🔄  Round 1/5
🧠  Extracting clues from image...
🧠  Proposing answers...
🔧  Checking constraints...
┌─────────────┐
│ I _ _ _ H │
│ _ _ _ _ O │
│ _ _ _ _ T │
│ _ _ _ _ _  │
│ _ _ _ _ _  │
└─────────────┘

🔄  Round 2/5
🧠  Proposing answers...
🔧  Checking constraints...
┌─────────────┐
│ I C E _ H │
│ C _ _ _ O │
│ E _ A _ T │
│ _ _ _ _ _  │
│ _ _ _ _ _  │
└─────────────┘

🔄  Round 3/5
🧠  Proposing answers...
🔧  Checking constraints...
┌─────────────┐
│ I C E A H │
│ C _ A _ O │
│ E _ A N T │
│ A N T S _  │
│ H O T _ _  │
└─────────────┘

✅  Puzzle solved!

═══════════════════════════════════════════════════════════════════
📊  TELEMETRY DASHBOARD
───────────────────────────────────────────────────────────────────
Agent ID:           ollama-crossword-agent
Status:             completed
Rounds:             3/5
Grid state:         0 empty cells
Solved:             True
═══════════════════════════════════════════════════════════════════
```

---

## How It Works

### 1. Clue Extraction

The vision model reads the screenshot and identifies all ACROSS and DOWN clues:

```json
{
  "across": {
    1: "Frozen water",
    4: "Not down",
    5: "Beverage"
  },
  "down": {
    1: "Burn with fire",
    2: "On switch"
  }
}
```

### 2. Answer Proposal

For each clue, the model proposes an answer of the correct length:

```
Clue: "Frozen water" (5 letters)
Context: _ _ _ _ _  (no crossing info yet)
Model: "ICE" → padded to "ICE__"
```

### 3. Constraint Checking

The engine checks each cell:

```
Cell (0,0):
  - ACROSS clue 1 proposes: I
  - DOWN clue 1 proposes:   I
  ✓ Agreement → commit 'I'

Cell (0,1):
  - ACROSS clue 1 proposes: C
  - DOWN clue 2 proposes:   O
  ✗ Conflict → don't commit
```

### 4. Guided Retry

On the next round, the model gets crossing hints:

```
Clue: "Not down" (2 letters)
Context: _ O  (DOWN clue 2 is "O_")
Model: "UP" → But U ≠ O, so model corrects to "ON"
```

---

## Why Hybrid?

**Pure LLM approach:** Ask the model to solve all 5 clues at once. The model may get 2-3 right but rarely all 5 in one shot.

**Hybrid approach:**
1. Model proposes all answers
2. Code enforces constraints (crossing agreement)
3. Model only retries conflicted clues with context
4. Usually solves in 2-3 rounds

**Benefits:**
- LLM doesn't need to track the entire grid state
- LLM gets feedback (crossing hints) only where needed
- Cells are guaranteed valid (deterministic constraint logic)
- Faster convergence (fewer retries)

---

## Extending

### Add New Puzzle Source

1. Create a new Playwright script that navigates to the puzzle and finds input cells
2. Modify `_type_answers_into_grid()` to click/type into the actual grid cells
3. Test with `--demo` mode first to debug

### Improve Vision Extraction

1. Fine-tune the prompt in `vision.py::extract_clues_from_screenshot()`
2. Add fallback OCR (e.g., `pytesseract`) if vision extraction fails
3. Log extraction confidence and retry on low confidence

### Add Timeout Handling

```python
# In agent.py
try:
    response = ollama.chat(..., timeout=10)
except ollama.RequestTimeout:
    self.bm.log_event(..., EventType.TASK_ERROR, "Model timeout")
    # fallback: use empty/placeholder answer
```

---

## Troubleshooting

**Ollama connection error:**
```
ConnectionError: No response received from Ollama
```
→ Check: `ollama serve` is running, `http://localhost:11434/api/tags` returns 200

**Model not found:**
```
Error: model qwen2.5vl:7b not found
```
→ Run: `ollama pull qwen2.5vl:7b`

**Playwright timeout:**
```
TimeoutError: page.goto() timeout
```
→ Increase timeout or check if puzzle URL is correct/reachable

**No clues extracted:**
```
"across": {}, "down": {}
```
→ Vision model couldn't read clues from screenshot. Try a different puzzle or improve the extraction prompt.

---

## Logs

All events are logged to `logs/`:

```bash
# View human-readable log
tail -f logs/agent.log

# Stream JSON events
tail -f logs/agent.jsonl | jq .

# View reasoning chain
jq 'select(.event_type == "LLM_REASONING")' logs/agent_reasoning.jsonl
```

---

## Testing

To verify all Python files parse correctly:

```bash
python -m py_compile grid.py vision.py agent.py main.py
```

Run the demo:

```bash
python main.py --demo
```

---

## License

Part of the bmasterai examples. See parent repository for license.

---

## References

- [Ollama](https://ollama.ai) — Local LLM runtime
- [Playwright](https://playwright.dev) — Browser automation
- [BMasterAI](https://github.com/anthropics/bmasterai) — Agent instrumentation framework
- [qwen2.5vl](https://huggingface.co/Qwen/Qwen2.5-VL-7B) — Vision-language model
