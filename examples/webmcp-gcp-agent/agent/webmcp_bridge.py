"""
WebMCP Bridge
=============
Connects a Python agent to a website that exposes tools via the WebMCP API
(navigator.modelContext). Uses Playwright to:

  1. Launch a headless Chromium browser
  2. Inject the WebMCP polyfill (if the browser doesn't support it natively)
  3. Navigate to the target website
  4. Discover available tools via window.__webmcp_list_tools()
  5. Call tools via window.__webmcp_call_tool(name, args)

Usage:
    bridge = WebMCPBridge("http://localhost:8080")
    await bridge.connect()

    tools = await bridge.list_tools()
    result = await bridge.call_tool("search_products", {"query": "laptop"})

    await bridge.close()

Works as an async context manager:
    async with WebMCPBridge("http://localhost:8080") as bridge:
        tools = await bridge.list_tools()
"""

import json
import asyncio
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright, Page, Browser


# Minimal polyfill script injected before the page loads.
# This handles the case where the site doesn't include webmcp-polyfill.js.
_BRIDGE_INJECT_SCRIPT = """
(function() {
  // Register tool storage if not already set up
  if (!window.__webmcp_bridge_injected) {
    window.__webmcp_tools = window.__webmcp_tools || {};

    window.__webmcp_list_tools = function() {
      return Object.values(window.__webmcp_tools).map(function(t) {
        return { name: t.name, description: t.description, inputSchema: t.inputSchema || {} };
      });
    };

    window.__webmcp_call_tool = async function(name, args) {
      var tool = window.__webmcp_tools[name];
      if (!tool) throw new Error('WebMCP bridge: tool not found: ' + name);
      var client = {
        requestUserInteraction: async function(cb) { return await cb(); }
      };
      return await tool.execute(args, client);
    };

    // Polyfill navigator.modelContext if absent
    if (!navigator.modelContext) {
      var mc = {
        provideContext: function(opts) {
          window.__webmcp_tools = {};
          (opts && opts.tools || []).forEach(function(t) { mc.registerTool(t); });
        },
        registerTool: function(tool) {
          window.__webmcp_tools[tool.name] = tool;
        },
        unregisterTool: function(name) { delete window.__webmcp_tools[name]; },
        clearContext: function() { window.__webmcp_tools = {}; }
      };
      try {
        Object.defineProperty(navigator, 'modelContext', { value: mc, configurable: false });
      } catch(e) { navigator.modelContext = mc; }
    }

    window.__webmcp_ready = true;
    window.dispatchEvent(new Event('webmcp:ready'));
    window.__webmcp_bridge_injected = true;
  }
})();
"""


class WebMCPBridge:
    """
    Playwright-based bridge that exposes WebMCP browser tools to Python.
    """

    def __init__(
        self,
        url: str,
        headless: bool = True,
        timeout_ms: int = 10_000,
    ):
        self.url = url
        self.headless = headless
        self.timeout_ms = timeout_ms

        self._playwright = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._tools_cache: list[dict] | None = None

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Launch browser, navigate to the target URL, and wait for WebMCP tools."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        self._page = await self._browser.new_page()

        # Inject bridge script before any page JS runs
        await self._page.add_init_script(script=_BRIDGE_INJECT_SCRIPT)

        # Navigate and wait for the page to load
        await self._page.goto(self.url, wait_until="domcontentloaded", timeout=self.timeout_ms)

        # Wait for WebMCP tools to be registered (up to timeout)
        try:
            await self._page.wait_for_function(
                "window.__webmcp_tools && Object.keys(window.__webmcp_tools).length > 0",
                timeout=self.timeout_ms,
            )
        except Exception:
            pass  # Page may have no tools; list_tools() will return []

        # Warm up the cache
        self._tools_cache = None

    async def close(self) -> None:
        """Close the browser and clean up."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._browser = None
        self._playwright = None

    # ── Context manager ───────────────────────────────────────────────────────

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *_):
        await self.close()

    # ── Tool discovery ────────────────────────────────────────────────────────

    async def list_tools(self) -> list[dict]:
        """
        Return all tools registered on the page via navigator.modelContext.
        Each tool is a dict: { name, description, inputSchema }.
        """
        self._assert_connected()
        tools = await self._page.evaluate("window.__webmcp_list_tools()")
        self._tools_cache = tools or []
        return self._tools_cache

    def get_cached_tools(self) -> list[dict]:
        """Return the last fetched tool list (no browser round-trip)."""
        return self._tools_cache or []

    # ── Tool execution ────────────────────────────────────────────────────────

    async def call_tool(self, name: str, args: dict | None = None) -> Any:
        """
        Call a WebMCP tool on the page and return its result.

        Args:
            name: Tool name as registered via navigator.modelContext.registerTool()
            args: Input arguments matching the tool's inputSchema

        Returns:
            The tool's return value (deserialized from JSON)

        Raises:
            ValueError: If the tool is not found on the page
            RuntimeError: If the tool call throws an error
        """
        self._assert_connected()
        args = args or {}

        try:
            result = await self._page.evaluate(
                """([name, args]) => window.__webmcp_call_tool(name, args)""",
                [name, args],
            )
        except Exception as e:
            raise RuntimeError(f"WebMCP tool call failed [{name}]: {e}") from e

        return result

    # ── Page interaction ─────────────────────────────────────────────────────

    async def screenshot(self, path: str = "screenshot.png") -> None:
        """Capture a screenshot of the current page (useful for debugging)."""
        self._assert_connected()
        await self._page.screenshot(path=path, full_page=True)

    async def get_page_title(self) -> str:
        self._assert_connected()
        return await self._page.title()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _assert_connected(self):
        if not self._page:
            raise RuntimeError("WebMCPBridge: not connected. Call await bridge.connect() first.")

    def __repr__(self):
        status = "connected" if self._page else "disconnected"
        return f"WebMCPBridge(url={self.url!r}, status={status})"
