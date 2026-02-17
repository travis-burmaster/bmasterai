/**
 * WebMCP Tool Registrations — Demo Tech Store
 *
 * Registers store tools via navigator.modelContext so any AI agent
 * (browser-native or via the Python bridge) can call them.
 *
 * Tools:
 *   - search_products      Search catalog by query + optional filters
 *   - get_product_details  Get full details for a product ID
 *   - add_to_cart          Add a product to the cart
 *   - get_cart             Get current cart contents
 *   - checkout             Complete the purchase (mock)
 */

(function registerStoreTools() {
  // Wait for polyfill/native WebMCP to be ready
  function onReady(fn) {
    if (window.__webmcp_ready || navigator.modelContext) {
      fn();
    } else {
      window.addEventListener("webmcp:ready", fn, { once: true });
    }
  }

  onReady(function () {
    // ─────────────────────────────────────────────────
    // Tool: search_products
    // ─────────────────────────────────────────────────
    navigator.modelContext.registerTool({
      name: "search_products",
      description:
        "Search the tech store product catalog. Returns matching products " +
        "with id, name, price, stock, and short description. Use this to " +
        "find products before adding them to the cart.",
      inputSchema: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "Natural language search query, e.g. 'gaming laptop under 1500'",
          },
          category: {
            type: "string",
            enum: ["laptops", "monitors", "peripherals", "audio", "accessories", ""],
            description: "Optional category filter",
          },
          max_price: {
            type: "number",
            description: "Optional maximum price filter in USD",
          },
        },
        required: ["query"],
      },
      annotations: { readOnlyHint: true },
      execute: async function (input, _client) {
        const query = (input.query || "").toLowerCase();
        const maxPrice = input.max_price || Infinity;
        const category = (input.category || "").toLowerCase();

        let results = window.PRODUCT_CATALOG.filter(function (p) {
          const matchesQuery =
            p.name.toLowerCase().includes(query) ||
            p.tags.some((t) => query.includes(t) || t.includes(query.split(" ")[0]));
          const matchesCategory = !category || p.category === category;
          const matchesPrice = p.price <= maxPrice;
          return matchesQuery && matchesCategory && matchesPrice;
        });

        // Fallback: partial word match if nothing found
        if (results.length === 0) {
          const words = query.split(" ").filter((w) => w.length > 2);
          results = window.PRODUCT_CATALOG.filter((p) =>
            words.some(
              (w) =>
                p.name.toLowerCase().includes(w) ||
                p.category.includes(w) ||
                p.tags.includes(w)
            )
          );
        }

        return {
          results: results.map((p) => ({
            id: p.id,
            name: p.name,
            category: p.category,
            price: p.price,
            stock: p.stock,
            in_stock: p.stock > 0,
          })),
          total: results.length,
        };
      },
    });

    // ─────────────────────────────────────────────────
    // Tool: get_product_details
    // ─────────────────────────────────────────────────
    navigator.modelContext.registerTool({
      name: "get_product_details",
      description:
        "Get full details for a specific product by its ID, including specs and tags. " +
        "Use after search_products to get more information before recommending or purchasing.",
      inputSchema: {
        type: "object",
        properties: {
          product_id: {
            type: "string",
            description: "Product ID from search results, e.g. 'p001'",
          },
        },
        required: ["product_id"],
      },
      annotations: { readOnlyHint: true },
      execute: async function (input, _client) {
        const product = window.PRODUCT_CATALOG.find(
          (p) => p.id === input.product_id
        );
        if (!product) {
          return { error: `Product not found: ${input.product_id}` };
        }
        return { product };
      },
    });

    // ─────────────────────────────────────────────────
    // Tool: add_to_cart
    // ─────────────────────────────────────────────────
    navigator.modelContext.registerTool({
      name: "add_to_cart",
      description:
        "Add a product to the shopping cart. Returns the updated cart. " +
        "Requires the product to be in stock.",
      inputSchema: {
        type: "object",
        properties: {
          product_id: {
            type: "string",
            description: "Product ID to add, e.g. 'p001'",
          },
          quantity: {
            type: "integer",
            minimum: 1,
            description: "Quantity to add (default: 1)",
          },
        },
        required: ["product_id"],
      },
      execute: async function (input, client) {
        const quantity = input.quantity || 1;
        const product = window.PRODUCT_CATALOG.find(
          (p) => p.id === input.product_id
        );

        if (!product) {
          return { error: `Product not found: ${input.product_id}` };
        }
        if (product.stock < quantity) {
          return {
            error: `Insufficient stock. Available: ${product.stock}, Requested: ${quantity}`,
          };
        }

        // Request user confirmation before adding to cart
        const confirmed = await client.requestUserInteraction(async function () {
          // In a real app, this would show a dialog. We auto-confirm in demo.
          return true;
        });

        if (!confirmed) {
          return { error: "User cancelled add to cart" };
        }

        // Check if already in cart
        const existing = window.SHOPPING_CART.find(
          (item) => item.product_id === input.product_id
        );
        if (existing) {
          existing.quantity += quantity;
        } else {
          window.SHOPPING_CART.push({
            product_id: product.id,
            name: product.name,
            price: product.price,
            quantity,
          });
        }

        // Update UI if present
        if (typeof window.updateCartUI === "function") {
          window.updateCartUI();
        }

        const cartTotal = window.SHOPPING_CART.reduce(
          (sum, item) => sum + item.price * item.quantity,
          0
        );

        return {
          success: true,
          message: `Added ${quantity}× ${product.name} to cart`,
          cart_items: window.SHOPPING_CART.length,
          cart_total: Math.round(cartTotal * 100) / 100,
        };
      },
    });

    // ─────────────────────────────────────────────────
    // Tool: get_cart
    // ─────────────────────────────────────────────────
    navigator.modelContext.registerTool({
      name: "get_cart",
      description: "Get the current shopping cart contents and total price.",
      inputSchema: { type: "object", properties: {} },
      annotations: { readOnlyHint: true },
      execute: async function (_input, _client) {
        const total = window.SHOPPING_CART.reduce(
          (sum, item) => sum + item.price * item.quantity,
          0
        );
        return {
          items: window.SHOPPING_CART,
          item_count: window.SHOPPING_CART.length,
          total: Math.round(total * 100) / 100,
        };
      },
    });

    // ─────────────────────────────────────────────────
    // Tool: checkout
    // ─────────────────────────────────────────────────
    navigator.modelContext.registerTool({
      name: "checkout",
      description:
        "Complete the purchase. Clears the cart and returns an order confirmation. " +
        "Only call this after confirming the cart contents with the user.",
      inputSchema: {
        type: "object",
        properties: {
          shipping_address: {
            type: "string",
            description: "Shipping address for the order",
          },
        },
        required: ["shipping_address"],
      },
      execute: async function (input, client) {
        if (window.SHOPPING_CART.length === 0) {
          return { error: "Cart is empty" };
        }

        // Request final user confirmation
        await client.requestUserInteraction(async function () {
          return true; // Auto-confirm in demo
        });

        const total = window.SHOPPING_CART.reduce(
          (sum, item) => sum + item.price * item.quantity,
          0
        );

        const orderId = "ORD-" + Date.now().toString(36).toUpperCase();
        const items = [...window.SHOPPING_CART];

        // Clear cart
        window.SHOPPING_CART = [];
        if (typeof window.updateCartUI === "function") {
          window.updateCartUI();
        }

        return {
          success: true,
          order_id: orderId,
          items_purchased: items,
          total_charged: Math.round(total * 100) / 100,
          shipping_to: input.shipping_address,
          estimated_delivery: "3-5 business days",
        };
      },
    });

    console.info(
      "[WebMCP] Store tools registered:",
      Object.keys(window.__webmcp_tools)
    );
  });
})();
