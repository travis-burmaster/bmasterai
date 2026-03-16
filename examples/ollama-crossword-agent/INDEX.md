# Ollama Crossword Agent — File Index

Complete bmasterai example: hybrid crossword solver with vision model + constraint engine.

## Files

### Core Implementation (4 files, 1,030 lines)

**agent.py** (529 lines)
- `CrosswordAgent` — main solver class
- `setup_logging()` — BMasterAI configuration
- `async run()` — entry point (real mode + demo mode)
- `_run_real()` — with Ollama + Playwright
- `_run_demo()` — hardcoded clues, no external dependencies
- `_propose_all_answers()` — batch vision calls
- `_setup_grid_from_clues()` — parse OCR output
- `_print_dashboard()` — telemetry display

**grid.py** (215 lines)
- `CrosswordGrid` — state management and constraint engine
- `add_clue(number, direction, start_row, start_col, length, clue_text)`
- `propose_answer(number, direction, answer)` — store proposed answer
- `commit_agreed_cells()` → int — enforce crossing agreement, return count
- `get_conflicts()` → list — identify disagreements
- `get_context_for_clue(number, direction)` → str — crossing hints
- `is_solved()` → bool — completion check
- `to_display_string()` → str — ASCII art grid
- `get_empty_cell_count()` → int — progress metric

**vision.py** (179 lines)
- `ask_vision(prompt, image_b64, model)` → str — Ollama API call
- `extract_clues_from_screenshot(image_b64)` → dict — OCR → JSON
- `propose_answer(clue, length, context, image_b64)` → str — solve with hints
- `screenshot_to_base64(image_bytes)` → str — image encoding

**main.py** (107 lines)
- `check_dependencies()` — pre-flight verification
- `main()` — CLI argument parsing and asyncio wrapper
- Supports: --demo, --url, --size flags

### Configuration (3 files)

**requirements.txt**
```
ollama>=0.3.0
playwright>=1.44.0
bmasterai>=0.2.3
python-dotenv>=1.0.0
psutil>=5.9.0
Pillow>=10.0.0
```

**.env.example**
- PUZZLE_URL (optional)
- OLLAMA_HOST (optional)
- DEBUG (optional)

**.gitignore**
- Standard Python ignores
- logs/, screenshots/, __pycache__
- .venv, *.log, .env

### Documentation (1 file, 444 lines)

**README.md**
- What It Demonstrates
- Architecture (diagram + explanation)
- BMasterAI Instrumentation (table)
- Setup instructions (Ollama, Playwright)
- Usage examples (demo, real, custom)
- Example run output with grid progression
- How It Works (step-by-step)
- Why Hybrid (vs pure LLM)
- Extending (customization points)
- Troubleshooting (common errors)
- Logs (telemetry guide)
- Testing (verification)
- References (links)

## Quick Start

### 1. Test Demo (No Setup Required)
```bash
python main.py --demo
```

### 2. Setup Real Mode
```bash
# Install Ollama: https://ollama.ai
ollama pull qwen2.5vl:7b

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 3. Run Real Puzzle
```bash
python main.py                              # NYT Mini (default)
python main.py --url "https://..."          # Custom puzzle
python main.py --size 7                     # 7x7 grid
```

## Architecture Summary

**3-Component System:**

1. **Vision (qwen2.5vl:7b via Ollama)**
   - Extracts clues from screenshots
   - Proposes answers for each clue

2. **Browser (Playwright)**
   - Navigates to puzzle URL
   - Takes screenshots
   - Types answers into grid

3. **Constraint Engine (Python)**
   - Tracks proposed answers
   - Enforces crossing agreement (key insight!)
   - Commits cells where ALL crossings agree
   - Provides context for retries

**Solve Loop:**
1. Screenshot puzzle
2. Extract clues (round 1)
3. Propose answers for all clues
4. Commit agreed cells
5. Type answers via Playwright
6. Repeat until solved (max 5 rounds)

## BMasterAI Integration

**Logger:**
```python
from bmasterai.logging import get_logger, EventType
bm = get_logger()  # No arguments
bm.log_event(agent_id=AGENT_ID, event_type=EventType.LLM_CALL, ...)
```

**Monitor:**
```python
from bmasterai.monitoring import get_monitor
monitor = get_monitor()  # No arguments
monitor.track_agent_start(AGENT_ID)
monitor.track_llm_call(agent_id=AGENT_ID, model="qwen2.5vl:7b", ...)
```

**Events Logged:**
- AGENT_START / AGENT_STOP
- LLM_CALL (on every vision query)
- TOOL_USE (screenshots, clicks)
- DECISION_POINT (constraint decisions)
- TASK_COMPLETE / TASK_ERROR
- LLM_REASONING (proposal details)

**Output:**
- logs/agent.log — human-readable
- logs/agent.jsonl — structured JSON
- logs/agent_reasoning.jsonl — reasoning chains
- screenshots/round_*.png — grid states

## Testing

**Syntax Check:**
```bash
python -m py_compile agent.py grid.py vision.py main.py
```

**Demo Mode:**
```bash
python main.py --demo
```

**Structural Verification:**
```bash
python -c "from agent import CrosswordAgent; from grid import CrosswordGrid; print('OK')"
```

## Key Features

✓ Vision-based clue extraction (no HTML parsing)
✓ Constraint enforcement (crossing agreement)
✓ Context-aware retry (automatic guidance)
✓ Local Ollama (no cloud, no API keys)
✓ Playwright for reliable automation
✓ Full BMasterAI instrumentation
✓ Demo mode (no dependencies)
✓ Production-ready error handling
✓ Comprehensive documentation

## Extension Points

- **Vision:** Modify extraction prompt, add OCR fallback
- **Browser:** Implement cell typing for specific sites
- **Constraints:** Add symmetry, word validation
- **Model:** Switch to different Ollama models

## File Statistics

```
agent.py              529 lines
grid.py               215 lines
vision.py             179 lines
main.py               107 lines
README.md             444 lines
requirements.txt        6 lines
.env.example           11 lines
.gitignore             48 lines
────────────────────────────
Total               1,539 lines
```

## Constants

```python
AGENT_ID = "ollama-crossword-agent"
DEFAULT_MODEL = "qwen2.5vl:7b"
MAX_ROUNDS = 5
GRID_SIZE = 5
DEFAULT_PUZZLE_URL = "https://www.nytimes.com/crosswords/game/mini"
```

## Next Steps

1. Review README.md for detailed architecture
2. Run `python main.py --demo` to test
3. Setup Ollama and Playwright for real mode
4. Extend grid.py or vision.py for custom puzzles
5. Check logs/ for telemetry

See README.md for complete documentation.
