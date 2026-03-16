"""
agent.py — Core tool-use agent loop

Runs a Gemini function-calling loop with two tools:
  - web_search    (Tavily)
  - computer_use  (screenshot / click / type / key / scroll)

Every step is instrumented with BMasterAI logging and monitoring.

Architecture:
  user prompt
      ↓
  gemini_call (tools: web_search, computer_use)
      ↓
  function_calls present?
     ├── yes → dispatch tool(s) → append function_response(s) → loop back
     └── no  → return final text response
"""

import os
import time
import json
import base64
from typing import Optional

from google import genai
from google.genai import types

from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor

from tools import ALL_TOOL_SCHEMAS, dispatch_tool

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

AGENT_ID = "gemini-web-computer-agent"
DEFAULT_MODEL = "gemini-3-flash-preview"
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
    A Gemini function-calling agent combining web search and computer use,
    fully instrumented with BMasterAI telemetry.
    """

    def __init__(self, model: str = DEFAULT_MODEL, verbose: bool = True):
        self.model = model
        self.verbose = verbose
        api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.bm, self.monitor = setup_logging()
        self.monitor.start_monitoring()

    # ── Public entry point ────────────────────────────────────────────────────

    def run(self, user_message: str) -> str:
        """
        Run the agent on a user message.
        Returns the final text response from Gemini.
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

        messages = [
            types.Content(role="user", parts=[
                types.Part.from_text(text=user_message)
            ])
        ]
        turn = 0
        final_response = ""

        try:
            while turn < MAX_TURNS:
                turn += 1
                if self.verbose:
                    print(f"🔄  Turn {turn}/{MAX_TURNS}")

                # ── Gemini API call ───────────────────────────────────────────
                response, latency_ms, input_tokens, output_tokens = self._call_gemini(messages, turn)

                if response.candidates and response.candidates[0].content:
                    messages.append(response.candidates[0].content)

                function_calls = response.function_calls

                # ── End turn: no more tools ───────────────────────────────────
                if not function_calls:
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
                tool_results = self._dispatch_tools(function_calls, turn)
                messages.append(types.Content(role="user", parts=tool_results))

                self.bm.log_event(
                    agent_id=AGENT_ID,
                    event_type=EventType.DECISION_POINT,
                    message=f"continue — {len(tool_results)} tool result(s) appended",
                    metadata={"turn": turn, "tool_count": len(tool_results)},
                )
                continue

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
            import traceback
            self.bm.log_event(
                agent_id=AGENT_ID,
                event_type=EventType.TASK_ERROR,
                message=f"Agent error: {type(e).__name__}: {e}",
                level=LogLevel.ERROR,
                metadata={
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "turn": turn,
                    "message_count": len(messages),
                    "traceback": traceback.format_exc(limit=5),
                },
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

    # ── Internal: Gemini API call ─────────────────────────────────────────────

    def _call_gemini(self, messages: list, turn: int):
        """Call Gemini and record telemetry. Returns (response, latency_ms, in_tokens, out_tokens)."""
        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.LLM_CALL,
            message=f"Calling {self.model} (turn {turn})",
            metadata={"model": self.model, "turn": turn, "message_count": len(messages)},
        )

        t0 = time.time()
        
        declarations = []
        for schema in ALL_TOOL_SCHEMAS:
            declarations.append(types.FunctionDeclaration(
                name=schema["name"],
                description=schema["description"],
                parameters=schema["input_schema"]
            ))
        gemini_tools = [types.Tool(function_declarations=declarations)]
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=messages,
            config=types.GenerateContentConfig(
                tools=gemini_tools,
                temperature=0.0,
            )
        )
        latency_ms = (time.time() - t0) * 1000

        input_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
        output_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
        total_tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0

        self.monitor.track_llm_call(
            agent_id=AGENT_ID,
            model=self.model,
            tokens_used=total_tokens,
            duration_ms=latency_ms,
        )
        self.monitor.track_task_duration(AGENT_ID, f"llm_call_turn_{turn}", latency_ms)

        function_calls = response.function_calls
        stop_reason = "tool_use" if function_calls else "end_turn"

        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.LLM_CALL,
            message=f"Gemini responded — stop_reason={stop_reason}",
            metadata={
                "turn": turn,
                "stop_reason": stop_reason,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": round(latency_ms, 1),
            },
        )

        if self.verbose:
            print(f"   🧠  {self.model} | {input_tokens}+{output_tokens} tokens | "
                  f"{latency_ms:.0f}ms | stop={stop_reason}")

        return response, latency_ms, input_tokens, output_tokens

    # ── Internal: Tool dispatch ───────────────────────────────────────────────

    def _dispatch_tools(self, function_calls: list, turn: int) -> list:
        """Dispatch all function calls, log each one, return list of Parts."""
        tool_results = []

        for call in function_calls:
            tool_name = call.name
            tool_input = call.args
            if not isinstance(tool_input, dict):
                try:
                    tool_input = dict(tool_input)
                except (ValueError, TypeError):
                    tool_input = {}
                    
            # Gemini function calls may or may not have an id field in the SDK depending on the model.
            tool_use_id = getattr(call, "id", "")

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

            # Format result for Gemini
            if tool_name == "computer_use" and result.get("action") == "screenshot" and result.get("success"):
                try:
                    image_bytes = base64.b64decode(result["image_base64"])
                    # Provide the function response part
                    tool_results.append(types.Part.from_function_response(
                        name=tool_name,
                        response={"success": True, "note": "Screenshot captured"}
                    ))
                    # And append the image part separately
                    tool_results.append(types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/png"
                    ))
                except Exception as e:
                    tool_results.append(types.Part.from_function_response(
                        name=tool_name,
                        response={"error": f"Failed to decode base64 screenshot: {str(e)}"}
                    ))
            else:
                clean = {k: v for k, v in result.items() if k != "image_base64"}
                tool_results.append(types.Part.from_function_response(
                    name=tool_name,
                    response=clean
                ))

        return tool_results

    # ── Internal: helpers ─────────────────────────────────────────────────────

    def _extract_text(self, response) -> str:
        """Extract the final text from a Gemini response."""
        try:
            return response.text if response.text else ""
        except (ValueError, AttributeError):
            return ""

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
