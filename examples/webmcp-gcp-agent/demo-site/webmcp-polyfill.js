/**
 * WebMCP Polyfill + Bridge Injection Script
 *
 * Two roles:
 *  1. Polyfill navigator.modelContext for browsers that don't support WebMCP yet
 *  2. Expose __webmcp_* globals so the Python Playwright bridge can list/call tools
 *
 * Spec: https://webmachinelearning.github.io/webmcp/
 */

(function () {
  "use strict";

  // Tool registry — keyed by tool name
  window.__webmcp_tools = {};

  // List all registered tools (schema only, no execute fn)
  window.__webmcp_list_tools = function () {
    return Object.values(window.__webmcp_tools).map(function (t) {
      return {
        name: t.name,
        description: t.description,
        inputSchema: t.inputSchema || {},
        annotations: t.annotations || {},
      };
    });
  };

  // Call a registered tool by name with args dict
  // Returns a Promise — Playwright's evaluate will await it automatically
  window.__webmcp_call_tool = async function (name, args) {
    const tool = window.__webmcp_tools[name];
    if (!tool) {
      throw new Error(`WebMCP: tool not found: "${name}"`);
    }

    // ModelContextClient stub — requestUserInteraction runs the callback immediately
    const client = {
      requestUserInteraction: async function (callback) {
        return await callback();
      },
    };

    return await tool.execute(args, client);
  };

  // Polyfill navigator.modelContext if the browser doesn't have it
  if (!navigator.modelContext) {
    const modelContext = {
      /**
       * Register a batch of tools, clearing any existing registrations.
       * @param {Object} options - { tools: ModelContextTool[] }
       */
      provideContext: function (options) {
        options = options || {};
        window.__webmcp_tools = {};
        for (const tool of options.tools || []) {
          modelContext.registerTool(tool);
        }
      },

      /**
       * Register a single tool without clearing existing tools.
       * Throws if a tool with the same name already exists.
       * @param {Object} tool - ModelContextTool
       */
      registerTool: function (tool) {
        if (!tool.name || !tool.description || !tool.execute) {
          throw new TypeError(
            "WebMCP: tool must have name, description, and execute"
          );
        }
        if (window.__webmcp_tools[tool.name]) {
          throw new Error(
            `WebMCP: tool "${tool.name}" already registered`
          );
        }
        window.__webmcp_tools[tool.name] = tool;
        console.debug(`[WebMCP] Tool registered: ${tool.name}`);
      },

      /**
       * Unregister a tool by name.
       * @param {string} name
       */
      unregisterTool: function (name) {
        delete window.__webmcp_tools[name];
        console.debug(`[WebMCP] Tool unregistered: ${name}`);
      },

      /**
       * Unregister all tools.
       */
      clearContext: function () {
        window.__webmcp_tools = {};
        console.debug("[WebMCP] Context cleared");
      },
    };

    // Attach to navigator (read-only in some browsers, hence try/catch)
    try {
      Object.defineProperty(navigator, "modelContext", {
        value: modelContext,
        writable: false,
        configurable: false,
      });
    } catch (e) {
      navigator.modelContext = modelContext;
    }

    console.info("[WebMCP] Polyfill active — navigator.modelContext ready");
  } else {
    // Native support — still wire up the bridge globals by intercepting calls
    const native = navigator.modelContext;
    const origRegister = native.registerTool.bind(native);
    const origProvide = native.provideContext.bind(native);
    const origUnregister = native.unregisterTool.bind(native);
    const origClear = native.clearContext.bind(native);

    native.registerTool = function (tool) {
      window.__webmcp_tools[tool.name] = tool;
      return origRegister(tool);
    };
    native.provideContext = function (options) {
      window.__webmcp_tools = {};
      for (const t of (options || {}).tools || []) {
        window.__webmcp_tools[t.name] = t;
      }
      return origProvide(options);
    };
    native.unregisterTool = function (name) {
      delete window.__webmcp_tools[name];
      return origUnregister(name);
    };
    native.clearContext = function () {
      window.__webmcp_tools = {};
      return origClear();
    };
    console.info("[WebMCP] Native support detected — bridge wired");
  }

  // Signal that polyfill is ready
  window.__webmcp_ready = true;
  window.dispatchEvent(new Event("webmcp:ready"));
})();
