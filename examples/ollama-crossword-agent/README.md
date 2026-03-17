# ollama-crossword-agent

A hybrid crossword-solving agent that combines **qwen2.5:7b** (via Ollama), **Playwright** browser automation, and **constraint logic** — fully instrumented with **BMasterAI** telemetry.

This agent demonstrates how to build a system where:
- DOM extraction reliably pulls clues and grid structure directly from the puzzle's HTML
- A text LLM (Qwen 2.5 7B) proposes answers for each clue
- Deterministic code enforces hard constraints (crossing letters must agree)
- The LLM is guided by feedback (context from committed crossings) on retry

**Key insight:** The LLM is not the source of truth — the constraint engine is. Cells are only committed when all crossing answers agree, ensuring a valid grid solution.

---

## What It Demonstrates

- **DOM-based clue extraction:** Parses the PuzzleMe widget's HTML structure directly via JavaScript — no OCR or vision model required
- **Grid inference:** Constructs the puzzle grid from clue positions and black cell detection
- **Hybrid control:** LLM proposes, code decides (crossing constraint enforcement)
- **Retry with context:** Failed cells are re-solved with hints from committed crossings
- **Browser automation:** Navigate puzzle, interact with PuzzleMe iframe, type answers via Playwright
- **Full BMasterAI instrumentation:** Every LLM call, tool use, constraint decision is logged
- **Replay mode:** Browser-based visualization that types known correct answers with animated delays

---

## Architecture

```
┌─ Browser (Playwright)
│  ├─ Navigate to The Atlantic crossword (PuzzleMe widget)
│  ├─ Detect and enter PuzzleMe iframe
│  ├─ Extract clues + grid via JavaScript/DOM parsing
│  └─ Type answers into grid cells
│
├─ LLM (Ollama qwen2.5:7b — text model)
│  ├─ Propose answer for each clue (with crossing context)
│  └─ Fallback: Claude CLI (primary), Ollama (secondary)
│
└─ Constraint Engine (Python — grid.py)
   ├─ Track grid state (row × col committed letters)
   ├─ For each cell: collect all proposed letters from crossing answers
   ├─ commit_agreed_cells(): commit only if all crossings agree
   ├─ commit_all_proposed(): force-commit with ACROSS-first priority
   ├─ Identify conflicts: cells where crossings disagree
   └─ Provide hints: "Across is C_A_E, Down is CHO_R → both have C at (0,0)"
```

**Solve loop (per round):**

```
1. Extract clues from DOM (round 1 only)
2. For each clue:
   a. Ask model: "Solve this clue, length=5, context: _ R _ N _"
   b. Collect proposed answers
3. Constraint engine:
   a. For each cell, check: do all crossing answers agree?
   b. If YES: commit letter
   c. If CONFLICT: mark for retry
4. Type committed answers into grid via Playwright
5. Check for PuzzleMe congratulations modal (solved?)
6. Repeat until solved or MAX_ROUNDS (100) reached
```

---

## BMasterAI Instrumentation

Every step is tracked:

| Event | BMasterAI call | Details |
|---|---|---|
| Agent starts | `log_event(AGENT_START)` | URL, grid size, model |
| Screenshot taken | `log_event(TOOL_USE)` | PNG saved to screenshots/ |
| Clues extracted | `log_event(LLM_CALL)` | across + down count |
| Each answer proposed | `log_event(LLM_REASONING)` | clue, length, context, answer |
| Cells committed | `log_event(DECISION_POINT)` | count, empty cells remaining |
| Conflict detected | `log_event(TASK_ERROR)` | cell, proposed letters |
| Round complete | `log_event(TASK_COMPLETE)` | round latency |
| Puzzle solved | `log_event(TASK_COMPLETE)` | round number |
| Max rounds hit / errors | `log_event(TASK_ERROR)` | rounds used, error context |

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
| `vision.py` | Ollama helpers, clue extraction, answer proposal |
| `main.py` | CLI entry point, argument parsing, replay mode |
| `requirements.txt` | Python dependencies |
| `.env.example` | Configuration template (no API keys needed) |
| `INDEX.md` | Project index |
| `.gitignore` | Git exclusions |

---

## Setup

### Prerequisites

- **Python 3.10+**
- **Ollama** running locally with `qwen2.5:7b` model
  ```bash
  # Install Ollama: https://ollama.ai
  # Pull the model:
  ollama pull qwen2.5:7b
  # Ollama should be running on http://localhost:11434 (default)
  ```

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

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

Test the example without setting up Ollama or a browser. Runs a fully worked example using the hardcoded Atlantic crossword from March 16, 2026:

```bash
python main.py --demo
```

### Replay Mode (Browser Visualization)

Open a visible browser, navigate to the puzzle, and type the known correct answers with animated per-letter delays (400ms). Useful for demos and debugging the Playwright integration:

```bash
python main.py --replay
```

### Real Mode (The Atlantic Daily Crossword)

Solve the live Atlantic crossword with full LLM + constraint solving:

```bash
python main.py
# or specify a URL explicitly:
python main.py --url "https://www.theatlantic.com/games/daily-crossword/"
```

### CLI Arguments

| Argument | Description |
|---|---|
| `--url URL` | Custom puzzle URL (default: The Atlantic daily crossword) |
| `--size N` | Grid size, e.g. `--size 5` for 5×5 (default: 5) |
| `--demo` | Run console demo without browser or Ollama |
| `--replay` | Browser replay with hardcoded correct answers and animation |

---

## How It Works

### 1. Clue Extraction (DOM-based)

The agent uses Playwright's JavaScript execution to parse the PuzzleMe widget's HTML structure directly, extracting clues and their grid positions without relying on a vision model or OCR:

```python
# Pseudocode — actual extraction in agent.py
clues = page.evaluate("""
  () => {
    // Find PuzzleMe iframe, extract clue list elements,
    // parse number + direction + text + grid coordinates
  }
""")
```

Extracted clues are structured as:
```json
{
  "across": { "1": {"text": "Frozen water", "row": 0, "col": 0, "length": 3} },
  "down":   { "1": {"text": "Burn with fire", "row": 0, "col": 0, "length": 3} }
}
```

### 2. Answer Proposal

For each clue, the LLM proposes an answer of the correct length. The model receives any already-committed crossing letters as context:

```
Clue: "Frozen water" (3 letters)
Context: _ _ _  (no crossing info yet)
Model → "ICE"

Clue: "Frozen water" (3 letters)
Context: I _ _  (crossing DOWN committed 'I' at col 0)
Model → "ICE"  (consistent)
```

`vision.py` includes fallback logic: tries exact-length matches first, then approximate, then pads with underscores.

### 3. Constraint Checking

`grid.py`'s `commit_agreed_cells()` checks every unfilled cell:

```
Cell (0,0):
  - ACROSS clue 1 proposes: I
  - DOWN clue 1 proposes:   I
  ✓ Agreement → commit 'I'

Cell (0,1):
  - ACROSS clue 1 proposes: C
  - DOWN clue 2 proposes:   O
  ✗ Conflict → don't commit, flag for retry
```

When most cells have converged, `commit_all_proposed()` can force-commit remaining answers, with ACROSS answers taking priority at crossings.

### 4. Guided Retry

On the next round, the model receives crossing hints built from committed letters:

```
Clue: "On switch" (2 letters)
Context: _ O  (DOWN clue 2 committed 'O' at row 1)
Model corrects: "NO" → "ON"  (valid, O agrees at crossing)
```

### 5. Completion Check

After typing answers, the agent checks for the PuzzleMe congratulations modal. If detected, the puzzle is marked solved. Otherwise the loop continues up to `MAX_ROUNDS = 100`.

---

## Why Hybrid?

**Pure LLM approach:** Ask the model to solve all clues at once. May get 2–3 right, rarely all on the first attempt, and has no mechanism for self-correction.

**Hybrid approach:**
1. DOM extraction reliably captures clues without vision model errors
2. LLM proposes answers per-clue with lightweight context
3. Code enforces constraints (crossing agreement) — no hallucinated grids
4. LLM only retries conflicted clues, with pinpoint crossing hints
5. Typically solves in a small number of rounds

**Benefits:**
- LLM doesn't need to track entire grid state
- LLM gets feedback only where needed
- Committed cells are guaranteed valid (deterministic constraint logic)
- Faster convergence; fewer wasted LLM calls

---

## Extending

### Add New Puzzle Source

1. Write a Playwright script that navigates to the puzzle and extracts clues via DOM or JS
2. Modify `_type_answers_into_grid()` in `agent.py` to click/type into that puzzle's input cells
3. Test with `--demo` first to validate constraint logic without a live browser

### Improve Answer Proposal

1. Tune the prompt in `vision.py::propose_answer()` for your target domain or language
2. Add fallback OCR (e.g., `pytesseract`) if a puzzle has no accessible DOM structure
3. Log proposal confidence and retry on low-confidence answers

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
Error: model qwen2.5:7b not found
```
→ Run: `ollama pull qwen2.5:7b`

**Playwright timeout:**
```
TimeoutError: page.goto() timeout
```
→ Increase timeout or check if puzzle URL is correct and reachable

**No clues extracted:**
```
"across": {}, "down": {}
```
→ DOM structure may have changed. Inspect the PuzzleMe iframe and update the JavaScript extraction logic in `agent.py`.

**PuzzleMe iframe not found:**
→ The Atlantic may have updated their embed. Check that the iframe selector in `agent.py` matches the current page structure.

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

Verify all Python files parse correctly:

```bash
python -m py_compile grid.py vision.py agent.py main.py
```

Run the console demo (no browser or Ollama required):

```bash
python main.py --demo
```

Run the browser replay (Ollama not required, browser required):

```bash
python main.py --replay
```

---

## License

Part of the bmasterai examples. See parent repository for license.

---

## References

- [Ollama](https://ollama.ai) — Local LLM runtime
- [Playwright](https://playwright.dev) — Browser automation
- [BMasterAI](https://github.com/travis-burmaster/bmasterai) — Agent instrumentation framework
- [Qwen 2.5](https://huggingface.co/Qwen/Qwen2.5-7B) — Text language model
- [The Atlantic Daily Crossword](https://www.theatlantic.com/games/daily-crossword/) — Default puzzle target
