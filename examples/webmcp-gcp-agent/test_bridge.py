"""
WebMCP Bridge Test — runs without GCP/Vertex AI
Tests: tool discovery, search, product details, add_to_cart, get_cart, checkout
"""
import asyncio
import sys
sys.path.insert(0, "agent")
from webmcp_bridge import WebMCPBridge

SITE_URL = "http://localhost:8080"

async def main():
    print("=" * 55)
    print("  WebMCP Bridge Test")
    print("=" * 55)

    async with WebMCPBridge(SITE_URL, headless=True) as bridge:

        # ── 1. Tool discovery ────────────────────────────────────
        print("\n[1] Discovering WebMCP tools...")
        tools = await bridge.list_tools()
        print(f"    Found {len(tools)} tools:")
        for t in tools:
            print(f"      ✅ {t['name']:25s} — {t['description'][:55]}...")
        assert len(tools) == 5, f"Expected 5 tools, got {len(tools)}"

        # ── 2. search_products ───────────────────────────────────
        print("\n[2] search_products(query='laptop', max_price=1000)...")
        result = await bridge.call_tool("search_products", {"query": "laptop", "max_price": 1000})
        print(f"    Results: {result['total']} found")
        for p in result["results"]:
            print(f"      {p['id']} — {p['name']} — ${p['price']}")
        assert result["total"] > 0, "No laptops found under $1000"

        # ── 3. get_product_details ───────────────────────────────
        first_id = result["results"][0]["id"]
        print(f"\n[3] get_product_details(product_id='{first_id}')...")
        detail = await bridge.call_tool("get_product_details", {"product_id": first_id})
        p = detail["product"]
        print(f"    Name: {p['name']}")
        print(f"    Price: ${p['price']} | Stock: {p['stock']}")
        print(f"    Specs: {p['specs']}")

        # ── 4. add_to_cart ───────────────────────────────────────
        print(f"\n[4] add_to_cart(product_id='{first_id}', quantity=1)...")
        cart_result = await bridge.call_tool("add_to_cart", {"product_id": first_id, "quantity": 1})
        print(f"    {cart_result['message']}")
        print(f"    Cart items: {cart_result['cart_items']} | Total: ${cart_result['cart_total']}")
        assert cart_result["success"] is True

        # ── 5. get_cart ──────────────────────────────────────────
        print("\n[5] get_cart()...")
        cart = await bridge.call_tool("get_cart", {})
        print(f"    Items: {cart['item_count']} | Total: ${cart['total']}")
        for item in cart["items"]:
            print(f"      {item['quantity']}x {item['name']} @ ${item['price']}")
        assert cart["item_count"] == 1

        # ── 6. checkout ──────────────────────────────────────────
        print("\n[6] checkout(shipping_address='123 Main St, Denver CO')...")
        order = await bridge.call_tool("checkout", {"shipping_address": "123 Main St, Denver CO 80202"})
        print(f"    Order ID: {order['order_id']}")
        print(f"    Total charged: ${order['total_charged']}")
        print(f"    Ships to: {order['shipping_to']}")
        print(f"    ETA: {order['estimated_delivery']}")
        assert order["success"] is True

        # ── 7. Verify cart cleared ───────────────────────────────
        print("\n[7] Verifying cart cleared after checkout...")
        empty_cart = await bridge.call_tool("get_cart", {})
        print(f"    Cart items: {empty_cart['item_count']} ✅")
        assert empty_cart["item_count"] == 0

        # ── Screenshot ───────────────────────────────────────────
        await bridge.screenshot("/tmp/webmcp_test_result.png")
        print("\n    Screenshot saved: /tmp/webmcp_test_result.png")

    print("\n" + "=" * 55)
    print("  ALL TESTS PASSED ✅")
    print("=" * 55)

asyncio.run(main())
