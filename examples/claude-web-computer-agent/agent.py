"""
agent.py — Core tool-use agent loop

Runs a Claude tool-use loop with two tools:
  - web_search    (Tavily)
  - computer_use  (screenshot / click / type / key / scroll)

Every step is instrumented with BMasterAI logging and monitoring.

Architecture:
  user prompt
      ↓
  claude_call (tools: web_search, computer_use)
      ↓
  stop_reason == "tool_use"?
     ├── yes → dispatch tool(s) → append tool_result(s) → loop back
     └── no  → return final text response
"""

import os
import time
import json
from typing import Optional

import anthropic

from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor

from tools import ALL_TOOL_SCHEMAS, dispatch_tool

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

AGENT_ID = "claude-web-computer-agent"
DEFAULT_MODEL = "claude-opus-4-6"
MAX_TURNS = 20          # hard cap on tool-use iterations
MAX_TOKENS = 4096


# ─────────────────────────────────────────────────────────────────────────────
# Setup BMasterAI
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging():
    configure_logging(
        log_file="agent.log",
        json_log_file="agent.jsonl",
        reasoning_log_file="agent_reasoning.jsonl",
        log_level=LogLevel.INFO,
        enable_console=True,
        enable_file=True,
        enable_json=True,
        enable_reasoning_logs=True,
    )
    return get_logger(), get_monitor()


# ─────────────────────────────────────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────────────────────────────────────

class WebComputerAgent:
    """
    A Claude tool-use agent combining web search, computer use,
    and math — fully instrumented with BMasterAI telemetry.
    """

    def __init__(self, model: str = DEFAULT_MODEL, verbose: bool = True):
        self.model = model
        self.verbose = verbose
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.bm, self.monitor = setup_logging()
        self.monitor.start_monitoring()

    # ── Public entry point ────────────────────────────────────────────────────

    def run(self, user_message: str) -> str:
        """
        Run the agent on a user message.
        Returns the final text response from Claude.
        """
        self.monitor.track_agent_start(AGENT_ID)
        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.AGENT_START,
            message=f"Agent started",
            metadata={"model": self.model, "query": user_message[:200]},
        )

        if self.verbose:
            print(f"\n{'═'*60}")
            print(f"🤖  {AGENT_ID}")
            print(f"{'─'*60}")
            print(f"📝  Query: {user_message}")
            print(f"{'═'*60}\n")

        messages = [{"role": "user", "content": user_message}]
        turn = 0
        final_response = ""

        try:
            while turn < MAX_TURNS:
                turn += 1
                if self.verbose:
                    print(f"🔄  Turn {turn}/{MAX_TURNS}")

                # ── Claude API call ───────────────────────────────────────────
                response, latency_ms, input_tokens, output_tokens = self._call_claude(messages, turn)

                messages.append({"role": "assistant", "content": response.content})

                # ── End turn: no more tools ───────────────────────────────────
                if response.stop_reason == "end_turn":
                    self.bm.log_event(
                        agent_id=AGENT_ID,
                        event_type=EventType.DECISION_POINT,
                        message="end_turn — agent finished",
                        metadata={"turn": turn, "total_input_tokens": input_tokens,
                                  "total_output_tokens": output_tokens},
                    )
                    final_response = self._extract_text(response)
                    if self.verbose:
                        print(f"\n✅  Done in {turn} turn(s)\n")
                    break

                # ── Tool use ──────────────────────────────────────────────────
                if response.stop_reason == "tool_use":
                    tool_results = self._dispatch_tools(response, turn)
                    messages.append({"role": "user", "content": tool_results})

                    self.bm.log_event(
                        agent_id=AGENT_ID,
                        event_type=EventType.DECISION_POINT,
                        message=f"continue — {len(tool_results)} tool result(s) appended",
                        metadata={"turn": turn, "tool_count": len(tool_results)},
                    )
                    continue

                # ── Unexpected stop reason ────────────────────────────────────
                self.bm.log_event(
                    agent_id=AGENT_ID,
                    event_type=EventType.TASK_ERROR,
                    message=f"Unexpected stop_reason: {response.stop_reason}",
                    level=LogLevel.WARNING,
                    metadata={"stop_reason": response.stop_reason, "turn": turn},
                )
                final_response = self._extract_text(response)
                break

            else:
                # Hit MAX_TURNS
                self.bm.log_event(
                    agent_id=AGENT_ID,
                    event_type=EventType.TASK_ERROR,
                    message=f"Reached MAX_TURNS ({MAX_TURNS}) without end_turn",
                    level=LogLevel.WARNING,
                    metadata={"max_turns": MAX_TURNS},
                )
                final_response = self._extract_text(response)

        except Exception as e:
            self.bm.log_event(
                agent_id=AGENT_ID,
                event_type=EventType.TASK_ERROR,
                message=f"Agent error: {e}",
                level=LogLevel.ERROR,
                metadata={"error": str(e), "turn": turn},
            )
            self.monitor.track_error(AGENT_ID, type(e).__name__)
            raise

        finally:
            self.monitor.track_agent_stop(AGENT_ID)
            self.bm.log_event(
                agent_id=AGENT_ID,
                event_type=EventType.AGENT_STOP,
                message="Agent stopped",
                metadata={"turns_used": turn},
            )
            if self.verbose:
                self._print_dashboard()

        return final_response

    # ── Internal: Claude API call ─────────────────────────────────────────────

    def _call_claude(self, messages: list, turn: int):
        """Call Claude and record telemetry. Returns (response, latency_ms, in_tokens, out_tokens)."""
        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.LLM_CALL,
            message=f"Calling {self.model} (turn {turn})",
            metadata={"model": self.model, "turn": turn, "message_count": len(messages)},
        )

        t0 = time.time()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            tools=ALL_TOOL_SCHEMAS,
            messages=messages,
        )
        latency_ms = (time.time() - t0) * 1000

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens

        self.monitor.track_llm_call(
            agent_id=AGENT_ID,
            model=self.model,
            tokens_used=total_tokens,
            duration_ms=latency_ms,
        )
        self.monitor.track_task_duration(AGENT_ID, f"llm_call_turn_{turn}", latency_ms)

        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.LLM_CALL,
            message=f"Claude responded — stop_reason={response.stop_reason}",
            metadata={
                "turn": turn,
                "stop_reason": response.stop_reason,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": round(latency_ms, 1),
            },
        )

        if self.verbose:
            print(f"   🧠  {self.model} | {input_tokens}+{output_tokens} tokens | "
                  f"{latency_ms:.0f}ms | stop={response.stop_reason}")

        return response, latency_ms, input_tokens, output_tokens

    # ── Internal: Tool dispatch ───────────────────────────────────────────────

    def _dispatch_tools(self, response, turn: int) -> list:
        """Dispatch all tool_use blocks, log each one, return tool_result list."""
        tool_results = []

        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            tool_use_id = block.id

            self.bm.log_event(
                agent_id=AGENT_ID,
                event_type=EventType.TOOL_USE,
                message=f"Dispatching tool: {tool_name}",
                metadata={
                    "tool_name": tool_name,
                    "tool_use_id": tool_use_id,
                    "input": {k: str(v)[:200] for k, v in tool_input.items()},
                    "turn": turn,
                },
            )

            if self.verbose:
                print(f"   🔧  Tool: {tool_name}({json.dumps(tool_input)[:120]})")

            # Execute
            t0 = time.time()
            result = dispatch_tool(tool_name, tool_input)
            duration_ms = (time.time() - t0) * 1000

            self.monitor.track_task_duration(AGENT_ID, f"tool_{tool_name}", duration_ms)

            # Determine success
            is_error = "error" in result
            event_type = EventType.TASK_ERROR if is_error else EventType.TASK_COMPLETE
            log_level = LogLevel.WARNING if is_error else LogLevel.INFO

            self.bm.log_event(
                agent_id=AGENT_ID,
                event_type=event_type,
                message=f"Tool {tool_name} {'failed' if is_error else 'succeeded'}",
                level=log_level,
                metadata={
                    "tool_name": tool_name,
                    "tool_use_id": tool_use_id,
                    "duration_ms": round(duration_ms, 1),
                    "result_preview": str(result)[:300],
                    "success": not is_error,
                },
            )

            if self.verbose:
                status = "❌" if is_error else "✅"
                result_preview = result.get("error", str(result))[:100]
                print(f"   {status}  {tool_name} → {result_preview} ({duration_ms:.0f}ms)")

            # Format result for Claude
            # Screenshots get special treatment — strip base64 from log preview
            result_content = self._format_tool_result(tool_name, result)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result_content,
                "is_error": is_error,
            })

        return tool_results

    # ── Internal: helpers ─────────────────────────────────────────────────────

    def _format_tool_result(self, tool_name: str, result: dict) -> str:
        """
        Format a tool result for inclusion in the messages array.
        Screenshots return a multimodal content block; others return JSON text.
        """
        if tool_name == "computer_use" and result.get("action") == "screenshot" and result.get("success"):
            # Return image block so Claude can actually see the screen
            return [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result["image_base64"],
                    },
                }
            ]
        # Strip large base64 blobs from non-screenshot results before serialising
        clean = {k: v for k, v in result.items() if k != "image_base64"}
        return json.dumps(clean, indent=2)

    def _extract_text(self, response) -> str:
        """Extract the final text from a Claude response."""
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts).strip()

    def _print_dashboard(self):
        """Print a telemetry summary."""
        dash = self.monitor.get_agent_dashboard(AGENT_ID)
        health = self.monitor.get_system_health()

        print(f"\n{'═'*60}")
        print("📊  BMASTERAI TELEMETRY")
        print(f"{'─'*60}")
        print(f"  Agent status : {dash.get('status', 'unknown').upper()}")
        print(f"  Total errors : {dash['metrics'].get('total_errors', 0)}")

        perf = dash.get("performance", {})
        if perf:
            print(f"\n  Task timings:")
            for task, stats in sorted(perf.items()):
                print(f"    {task:<35} avg={stats['avg_duration_ms']:.0f}ms  "
                      f"calls={stats['total_calls']}")

        sys_m = dash.get("system", {})
        cpu = sys_m.get("cpu_usage", {})
        mem = sys_m.get("memory_usage", {})
        if cpu or mem:
            print(f"\n  System:")
            if cpu:
                print(f"    CPU    : {cpu.get('latest', 0):.1f}%")
            if mem:
                print(f"    Memory : {mem.get('latest', 0):.1f}%")

        print(f"\n  Telemetry logs:")
        print(f"    logs/agent.log       — human-readable")
        print(f"    logs/agent.jsonl     — structured JSON")
        print(f"    logs/reasoning/      — decision points & reasoning")
        print(f"{'═'*60}\n")
