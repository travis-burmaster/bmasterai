"""
Agent endpoint test — no GCP credentials needed.
Mocks Vertex AI so we can test /health and /tools locally.
"""
import sys, types

# ── Mock vertexai before agent imports it ────────────────────────────────────
vertexai_mock = types.ModuleType("vertexai")
vertexai_mock.init = lambda **kw: None
sys.modules["vertexai"] = vertexai_mock

gm = types.ModuleType("vertexai.generative_models")
class _FakePart:
    @staticmethod
    def from_function_response(name, response): return object()
gm.GenerativeModel = lambda *a, **kw: None
gm.FunctionDeclaration = lambda **kw: None
gm.Tool = lambda **kw: None
gm.Content = lambda **kw: None
gm.Part = _FakePart
sys.modules["vertexai.generative_models"] = gm

# ── Now import FastAPI test client ────────────────────────────────────────────
sys.path.insert(0, "agent")
from fastapi.testclient import TestClient

# Patch DEMO_SITE_URL before importing agent
import os
os.environ["DEMO_SITE_URL"] = "http://localhost:8080"

from agent import app

client = TestClient(app)

print("=" * 55)
print("  WebMCP Agent Endpoint Tests")
print("=" * 55)

# ── GET / ─────────────────────────────────────────────────────────────────────
print("\n[1] GET / (root)")
r = client.get("/")
assert r.status_code == 200
data = r.json()
print(f"    service: {data['service']}")
print(f"    endpoints: {list(data['endpoints'].keys())}")
assert "POST /run" in data["endpoints"]
print("    ✅")

# ── GET /health ───────────────────────────────────────────────────────────────
print("\n[2] GET /health")
r = client.get("/health")
assert r.status_code == 200
data = r.json()
print(f"    status: {data['status']}")
print(f"    model: {data['model']}")
print(f"    site: {data['site']}")
assert data["status"] == "ok"
print("    ✅")

# ── GET /tools ────────────────────────────────────────────────────────────────
print("\n[3] GET /tools (discovers WebMCP tools from live demo site)")
r = client.get("/tools")
assert r.status_code == 200
data = r.json()
tools = data["tools"]
print(f"    Site: {data['site_url']}")
print(f"    Tools found: {len(tools)}")
for t in tools:
    print(f"      ✅ {t['name']}")
assert len(tools) == 5, f"Expected 5 tools, got {len(tools)}"
expected = {"search_products", "get_product_details", "add_to_cart", "get_cart", "checkout"}
assert {t["name"] for t in tools} == expected
print("    ✅")

# ── POST /run validation (empty task) ─────────────────────────────────────────
print("\n[4] POST /run — empty task validation")
r = client.post("/run", json={"task": ""})
assert r.status_code == 400
print(f"    Status: {r.status_code} (400 expected) ✅")

print("\n" + "=" * 55)
print("  ALL ENDPOINT TESTS PASSED ✅")
print("=" * 55)
print("\nNote: POST /run with a real task requires GCP credentials (Vertex AI).")
print("      Run with GOOGLE_CLOUD_PROJECT set to test the full agent loop.")
