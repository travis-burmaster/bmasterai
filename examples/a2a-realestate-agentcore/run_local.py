"""
run_local.py — Start all three agents locally for end-to-end testing.

Usage:
    python run_local.py

Starts:
    • Property Booking Agent  → http://localhost:5001
    • Property Search Agent   → http://localhost:5002
    • Real Estate Coordinator → interactive REPL (talks to the two above)

Press Ctrl+C to shut down.
"""

import asyncio
import os
import subprocess
import sys
import time

SEARCH_PORT  = int(os.getenv("SEARCH_PORT",  "5002"))
BOOKING_PORT = int(os.getenv("BOOKING_PORT", "5001"))

BASE = os.path.dirname(__file__)
SEARCH_AGENT_SCRIPT  = os.path.join(BASE, "propertysearchagent",  "agent.py")
BOOKING_AGENT_SCRIPT = os.path.join(BASE, "propertybookingagent", "agent.py")
COORD_SCRIPT         = os.path.join(BASE, "realestate_coordinator", "agent.py")


def _start_server(script: str, port: int, name: str) -> subprocess.Popen:
    env = {**os.environ, "AGENT_PORT": str(port)}
    proc = subprocess.Popen(
        [sys.executable, script],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(f"[run_local] Started {name} (PID {proc.pid}) on port {port}")
    return proc


def _wait_for_port(host: str, port: int, timeout: float = 30.0):
    import socket
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def main():
    procs = []
    try:
        # 1. Start sub-agents
        search_proc  = _start_server(SEARCH_AGENT_SCRIPT,  SEARCH_PORT,  "PropertySearchAgent")
        booking_proc = _start_server(BOOKING_AGENT_SCRIPT, BOOKING_PORT, "PropertyBookingAgent")
        procs = [search_proc, booking_proc]

        print("[run_local] Waiting for agents to be ready...")
        for port, name in [(SEARCH_PORT, "Search"), (BOOKING_PORT, "Booking")]:
            if _wait_for_port("localhost", port):
                print(f"[run_local] {name} agent ready on port {port}")
            else:
                print(f"[run_local] WARNING: {name} agent did not start in time on port {port}")

        # 2. Launch coordinator in same process as REPL
        os.environ["PROPERTY_SEARCH_AGENT_URL"]  = f"http://localhost:{SEARCH_PORT}"
        os.environ["PROPERTY_BOOKING_AGENT_URL"] = f"http://localhost:{BOOKING_PORT}"

        print("\n[run_local] All agents running. Starting coordinator REPL...\n")
        os.execv(sys.executable, [sys.executable, COORD_SCRIPT])  # replaces this process

    except KeyboardInterrupt:
        print("\n[run_local] Shutting down...")
    finally:
        for p in procs:
            p.terminate()
        print("[run_local] Done.")


if __name__ == "__main__":
    main()
