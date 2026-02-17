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
import logging
from typing import Any

from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)


# ── Custom exceptions ────────────────────────────────────────────────────────

class WebMCPError(Exception):
    """Base class for WebMCP bridge errors."""


class WebMCPToolNotFoundError(WebMCPError):
    """Raised when a requested tool is not registered on the page."""


class WebMCPToolCallError(WebMCPError):
    """Raised when a tool call throws an error on the browser side."""


class WebMCPConnectionError(WebMCPError):
    """Raised when the bridge fails to connect or navigate."""


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

    // Polyfill navigator.modelContext if absent (i.e. no native WebMCP support).
    // If the browser already exposes a native navigator.modelContext, skip
    // injection entirely so we don't interfere with the native implementation.
    // We use configurable: true so a future native implementation loaded later
    // can override our polyfill via defineProperty.
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
        // configurable: true — allows a native WebMCP implementation to
        // override this polyfill if it loads later (e.g. via browser update).
        Object.defineProperty(navigator, 'modelContext', { value: mc, configurable: true, writable: false });
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

        # Wait for WebMCP tools to be registered — retry with exponential backoff.
        # Tools may finish registering after initial domcontentloaded (e.g. async
        # fetch or dynamic imports), so we poll rather than waiting for a single
        # event that may already have fired.
        await self._wait_for_tools_with_backoff()

        # Warm up the cache
        self._tools_cache = None

    async def _wait_for_tools_with_backoff(self) -> None:
        """
        Poll for WebMCP tools to appear, using exponential backoff.
        Retries up to 5 times before giving up (page may have no tools).
        """
        delay_ms = 200
        max_retries = 5
        for attempt in range(max_retries):
            try:
                await self._page.wait_for_function(
                    "window.__webmcp_tools && Object.keys(window.__webmcp_tools).length > 0",
                    timeout=delay_ms * (2 ** attempt),
                )
                return  # Tools found
            except Exception:
                if attempt < max_retries - 1:
                    logger.debug(
                        "WebMCP tools not yet registered (attempt %d/%d), retrying in %dms...",
                        attempt + 1, max_retries, delay_ms * (2 ** attempt),
                    )
                    await asyncio.sleep((delay_ms * (2 ** attempt)) / 1000)
                # else: give up — list_tools() will return []

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
            WebMCPToolNotFoundError: If the tool is not registered on the page
            WebMCPToolCallError: If the tool call throws an error on the browser side
        """
        self._assert_connected()
        args = args or {}

        try:
            result = await self._page.evaluate(
                """([name, args]) => window.__webmcp_call_tool(name, args)""",
                [name, args],
            )
        except Exception as e:
            err = str(e)
            if "tool not found" in err.lower():
                raise WebMCPToolNotFoundError(f"Tool not registered on page: {name!r}") from e
            raise WebMCPToolCallError(f"Tool call failed [{name}]: {e}") from e

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
