"""
Property Search Agent — BMasterAI + Strands A2A Implementation

Searches for real estate listings based on user criteria.
Can run locally (A2AServer) or on Amazon Bedrock AgentCore Runtime.
"""

import os
import time
import uuid
from typing import Optional

from strands import Agent, tool
from strands.multiagent.a2a import A2AServer

from bmasterai.logging import configure_logging, LogLevel, EventType

# ── Config ────────────────────────────────────────────────────────────────────
AGENT_ID = os.getenv("AGENT_ID", "property-search-agent")
MODEL_ID  = os.getenv("MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0")

# ── BMasterAI telemetry ───────────────────────────────────────────────────────
bm = configure_logging(
    log_level=LogLevel.INFO,
    enable_console=True,
    enable_file=True,
    enable_json=True,
)

bm.log_event(
    agent_id=AGENT_ID,
    event_type=EventType.AGENT_START,
    message="Property Search Agent starting",
    metadata={"model_id": MODEL_ID},
)


def _log_tool(name: str, metadata: dict):
    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TOOL_USE,
        message=f"Tool: {name}",
        metadata={"tool": name, **metadata},
    )


def _log_done(name: str, duration_ms: float, extra: dict = {}):
    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TASK_COMPLETE,
        message=f"{name} completed in {duration_ms:.0f}ms",
        metadata={"tool": name, **extra},
        duration_ms=duration_ms,
    )


def _log_err(name: str, error: Exception):
    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TASK_ERROR,
        message=f"{name} failed: {error}",
        metadata={"tool": name, "error": str(error)},
    )


# ── Mock property database ────────────────────────────────────────────────────
MOCK_PROPERTIES = [
    {
        "id": "PROP001",
        "title": "Modern Downtown Apartment",
        "location": "New York, NY",
        "price": 3500,
        "property_type": "apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "square_feet": 1200,
        "amenities": ["gym", "parking", "doorman"],
        "available": True,
        "description": "Beautiful modern apartment in the heart of downtown with stunning city views.",
    },
    {
        "id": "PROP002",
        "title": "Cozy Suburban House",
        "location": "Austin, TX",
        "price": 2800,
        "property_type": "house",
        "bedrooms": 3,
        "bathrooms": 2.5,
        "square_feet": 2000,
        "amenities": ["garden", "garage", "pool"],
        "available": True,
        "description": "Spacious family home with large backyard and modern kitchen.",
    },
    {
        "id": "PROP003",
        "title": "Luxury Penthouse",
        "location": "San Francisco, CA",
        "price": 8500,
        "property_type": "apartment",
        "bedrooms": 3,
        "bathrooms": 3,
        "square_feet": 2500,
        "amenities": ["gym", "concierge", "rooftop terrace", "parking"],
        "available": True,
        "description": "Exclusive penthouse with panoramic bay views and premium finishes.",
    },
    {
        "id": "PROP004",
        "title": "Charming Studio Downtown",
        "location": "Boston, MA",
        "price": 1800,
        "property_type": "apartment",
        "bedrooms": 1,
        "bathrooms": 1,
        "square_feet": 600,
        "amenities": ["laundry", "heating"],
        "available": True,
        "description": "Perfect studio apartment for young professionals, close to public transit.",
    },
    {
        "id": "PROP005",
        "title": "Beachfront Villa",
        "location": "Miami, FL",
        "price": 12000,
        "property_type": "house",
        "bedrooms": 5,
        "bathrooms": 4,
        "square_feet": 4000,
        "amenities": ["beach access", "pool", "garage", "smart home"],
        "available": True,
        "description": "Stunning beachfront property with direct ocean access and luxury amenities.",
    },
    {
        "id": "PROP006",
        "title": "Mountain Cabin Retreat",
        "location": "Denver, CO",
        "price": 2200,
        "property_type": "house",
        "bedrooms": 2,
        "bathrooms": 2,
        "square_feet": 1400,
        "amenities": ["fireplace", "deck", "mountain views"],
        "available": False,
        "description": "Cozy mountain retreat perfect for nature lovers and outdoor enthusiasts.",
    },
    {
        "id": "PROP007",
        "title": "Urban Loft",
        "location": "Seattle, WA",
        "price": 3200,
        "property_type": "apartment",
        "bedrooms": 2,
        "bathrooms": 1.5,
        "square_feet": 1100,
        "amenities": ["exposed brick", "high ceilings", "parking"],
        "available": True,
        "description": "Industrial-style loft in trendy neighborhood with modern updates.",
    },
    {
        "id": "PROP008",
        "title": "Family Home with Yard",
        "location": "Portland, OR",
        "price": 3000,
        "property_type": "house",
        "bedrooms": 4,
        "bathrooms": 3,
        "square_feet": 2400,
        "amenities": ["garden", "garage", "playroom"],
        "available": True,
        "description": "Spacious family home with large yard and excellent school district.",
    },
]


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def search_properties(
    location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    property_type: Optional[str] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
) -> str:
    """
    Search for properties based on specified criteria.

    Args:
        location: City or area to search in (e.g., 'New York', 'Austin')
        min_price: Minimum monthly rent/price
        max_price: Maximum monthly rent/price
        property_type: Type of property ('apartment', 'house', 'condo')
        min_bedrooms: Minimum number of bedrooms
        max_bedrooms: Maximum number of bedrooms

    Returns:
        Formatted list of matching properties
    """
    t0 = time.time()
    request_id = str(uuid.uuid4())[:8]
    _log_tool("search_properties", {
        "request_id": request_id,
        "location": location,
        "min_price": min_price,
        "max_price": max_price,
        "property_type": property_type,
        "min_bedrooms": min_bedrooms,
        "max_bedrooms": max_bedrooms,
    })

    try:
        filtered = []
        for prop in MOCK_PROPERTIES:
            if not prop.get("available"):
                continue
            if location and location.lower() not in prop["location"].lower():
                continue
            if min_price and prop["price"] < min_price:
                continue
            if max_price and prop["price"] > max_price:
                continue
            if property_type and prop["property_type"].lower() != property_type.lower():
                continue
            if min_bedrooms and prop["bedrooms"] < min_bedrooms:
                continue
            if max_bedrooms and prop["bedrooms"] > max_bedrooms:
                continue
            filtered.append(prop)

        dur = (time.time() - t0) * 1000
        _log_done("search_properties", dur, {"results": len(filtered), "request_id": request_id})

        if not filtered:
            return "No properties found matching your criteria. Please try adjusting your search parameters."

        lines = [f"Found {len(filtered)} properties matching your criteria:\n"]
        for i, p in enumerate(filtered, 1):
            amen = ", ".join(p["amenities"][:3])
            if len(p["amenities"]) > 3:
                amen += f" + {len(p['amenities']) - 3} more"
            lines.append(
                f"\n{i}. {p['title']} (ID: {p['id']})\n"
                f"   Location: {p['location']}\n"
                f"   Price: ${p['price']}/month\n"
                f"   Type: {p['property_type'].title()}\n"
                f"   Bedrooms: {p['bedrooms']} | Bathrooms: {p['bathrooms']}\n"
                f"   Size: {p['square_feet']} sq ft\n"
                f"   Amenities: {amen}\n"
                f"   Description: {p['description']}\n"
            )
        return "".join(lines)

    except Exception as e:
        _log_err("search_properties", e)
        return f"Error searching for properties: {e}"


@tool
def get_property_details(property_id: str) -> str:
    """
    Get detailed information about a specific property.

    Args:
        property_id: The unique identifier of the property (e.g., 'PROP001')

    Returns:
        Detailed property information
    """
    t0 = time.time()
    request_id = str(uuid.uuid4())[:8]
    _log_tool("get_property_details", {"property_id": property_id, "request_id": request_id})

    try:
        prop = next((p for p in MOCK_PROPERTIES if p["id"].upper() == property_id.upper()), None)

        dur = (time.time() - t0) * 1000

        if not prop:
            _log_done("get_property_details", dur, {"found": False, "request_id": request_id})
            return f"Error: Property with ID '{property_id}' not found. Please check the ID and try again."

        amen_list = "\n   - ".join(prop["amenities"])
        status = "✓ Available" if prop["available"] else "✗ Not Available"

        _log_done("get_property_details", dur, {"found": True, "request_id": request_id})

        return (
            f"Property Details — {prop['title']}\n"
            f"{'=' * 60}\n\n"
            f"Property ID: {prop['id']}\n"
            f"Location: {prop['location']}\n"
            f"Status: {status}\n\n"
            f"PRICING:\n"
            f"  Monthly Rent: ${prop['price']}\n\n"
            f"SPECIFICATIONS:\n"
            f"  Type: {prop['property_type'].title()}\n"
            f"  Bedrooms: {prop['bedrooms']}\n"
            f"  Bathrooms: {prop['bathrooms']}\n"
            f"  Square Feet: {prop['square_feet']}\n\n"
            f"AMENITIES:\n"
            f"   - {amen_list}\n\n"
            f"DESCRIPTION:\n"
            f"  {prop['description']}\n"
        )

    except Exception as e:
        _log_err("get_property_details", e)
        return f"Error retrieving property details: {e}"


# ── Agent & A2A server ────────────────────────────────────────────────────────

def create_agent() -> Agent:
    return Agent(
        name=os.getenv("AGENT_NAME", "Property Search Agent"),
        description=os.getenv(
            "AGENT_DESCRIPTION",
            "Searches for real estate properties based on user criteria including location, price, type, and amenities",
        ),
        tools=[search_properties, get_property_details],
        model=MODEL_ID,
    )


def create_server() -> A2AServer:
    agent = create_agent()
    host = os.getenv("AGENT_HOST", "0.0.0.0")  # nosec B104
    port = int(os.getenv("AGENT_PORT", "5002"))
    version = os.getenv("AGENT_VERSION", "1.0.0")

    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.AGENT_START,
        message=f"Starting A2A server on {host}:{port}",
        metadata={"host": host, "port": port},
    )

    return A2AServer(agent=agent, host=host, port=port, version=version)


if __name__ == "__main__":
    server = create_server()
    print(f"Property Search Agent A2A server → http://{server.host}:{server.port}")
    print(f"Agent card: http://{server.host}:{server.port}/.well-known/agent-card.json")
    server.serve()
