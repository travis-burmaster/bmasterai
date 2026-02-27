"""
Bash Tool
=========
Wraps AgentCore Code Interpreter for executing shell commands.

The Code Interpreter runs in a sandboxed environment managed by AgentCore,
so the agent cannot escape to the host filesystem or network. Commands
execute with a configurable timeout and return stdout + stderr.
"""

import json
import logging

import boto3
from strands.tools import tool

logger = logging.getLogger(__name__)

# AgentCore Code Interpreter client
_ci_client = boto3.client("bedrock-agentcore", region_name="us-east-1")


# ---------------------------------------------------------------------------
# Blocked commands — defence in depth on top of Cedar policies
# ---------------------------------------------------------------------------
BLOCKED_PREFIXES = [
    "rm -rf /",
    "mkfs",
    "dd if=",
    ":(){ :|:&",  # fork bomb
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
]


def _is_safe(command: str) -> bool:
    """Basic client-side safety check before sending to the sandbox."""
    cmd_lower = command.strip().lower()
    return not any(cmd_lower.startswith(b) for b in BLOCKED_PREFIXES)


# ---------------------------------------------------------------------------
# Strands tool definition
# ---------------------------------------------------------------------------
@tool
def bash_execute(command: str, timeout_seconds: int = 30) -> dict:
    """
    Execute a bash command in a secure AgentCore Code Interpreter sandbox.

    Use this tool when you need to:
    - Run shell commands (ls, grep, curl, jq, etc.)
    - Process files or text with standard Unix tools
    - Perform quick computations
    - Install and run Python/Node scripts

    Args:
        command: The bash command to execute. Multi-line scripts are supported.
        timeout_seconds: Max execution time (1–120). Defaults to 30.

    Returns:
        dict with keys: stdout, stderr, exit_code
    """
    if not _is_safe(command):
        return {
            "stdout": "",
            "stderr": "Command blocked by safety filter.",
            "exit_code": 1,
        }

    timeout_seconds = max(1, min(timeout_seconds, 120))

    logger.info("Executing bash: %.120s (timeout=%ds)", command, timeout_seconds)

    try:
        response = _ci_client.invoke_code_interpreter(
            language="bash",
            code=command,
            timeoutSeconds=timeout_seconds,
        )

        result = {
            "stdout": response.get("stdout", ""),
            "stderr": response.get("stderr", ""),
            "exit_code": response.get("exitCode", -1),
        }

        logger.info(
            "Bash result: exit_code=%d stdout_len=%d stderr_len=%d",
            result["exit_code"],
            len(result["stdout"]),
            len(result["stderr"]),
        )
        return result

    except Exception as e:
        logger.exception("Code Interpreter invocation failed")
        return {
            "stdout": "",
            "stderr": f"Execution error: {e}",
            "exit_code": 1,
        }


class BashTool:
    """Wrapper class so the tool can be passed to Strands Agent."""

    def __call__(self):
        return bash_execute
