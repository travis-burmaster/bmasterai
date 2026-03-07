"""
Property Booking Agent — BMasterAI + Strands A2A Implementation

Manages property bookings, reservations, and lease agreements.
Can run locally (A2AServer) or on Amazon Bedrock AgentCore Runtime.
"""

import os
import time
import uuid as _uuid
from datetime import datetime, timedelta
from typing import Optional

from strands import Agent, tool
from strands.multiagent.a2a import A2AServer

from bmasterai.logging import configure_logging, LogLevel, EventType

# ── Config ────────────────────────────────────────────────────────────────────
AGENT_ID = os.getenv("AGENT_ID", "property-booking-agent")
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
    message="Property Booking Agent starting",
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


# ── Mock data ─────────────────────────────────────────────────────────────────
MOCK_BOOKINGS: dict = {}

AVAILABLE_PROPERTIES = {
    "PROP001": {"title": "Modern Downtown Apartment",  "price": 3500,  "available": True},
    "PROP002": {"title": "Cozy Suburban House",        "price": 2800,  "available": True},
    "PROP003": {"title": "Luxury Penthouse",            "price": 8500,  "available": True},
    "PROP004": {"title": "Charming Studio Downtown",    "price": 1800,  "available": True},
    "PROP005": {"title": "Beachfront Villa",            "price": 12000, "available": True},
    "PROP006": {"title": "Mountain Cabin Retreat",      "price": 2200,  "available": False},
    "PROP007": {"title": "Urban Loft",                  "price": 3200,  "available": True},
    "PROP008": {"title": "Family Home with Yard",       "price": 3000,  "available": True},
}


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def create_booking(
    property_id: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    move_in_date: str,
    lease_duration_months: int = 12,
) -> str:
    """
    Create a booking reservation for a property.

    Args:
        property_id: The property ID to book (e.g., 'PROP001')
        customer_name: Full name of the customer
        customer_email: Email address of the customer
        customer_phone: Phone number of the customer
        move_in_date: Desired move-in date in YYYY-MM-DD format
        lease_duration_months: Length of lease in months (default: 12)

    Returns:
        Booking confirmation details
    """
    t0 = time.time()
    request_id = str(_uuid.uuid4())[:8]
    _log_tool("create_booking", {
        "request_id": request_id,
        "property_id": property_id,
        "customer_email": customer_email,
        "lease_duration_months": lease_duration_months,
    })

    try:
        pid = property_id.upper()

        if pid not in AVAILABLE_PROPERTIES:
            _log_done("create_booking", (time.time() - t0) * 1000, {"success": False, "reason": "not_found"})
            return f"Error: Property '{property_id}' not found. Please verify the property ID."

        prop = AVAILABLE_PROPERTIES[pid]
        if not prop["available"]:
            _log_done("create_booking", (time.time() - t0) * 1000, {"success": False, "reason": "unavailable"})
            return f"Error: Property '{property_id}' is not currently available for booking."

        # Validate date
        try:
            move_in_dt = datetime.strptime(move_in_date, "%Y-%m-%d")
            if move_in_dt < datetime.now():
                return "Error: Move-in date cannot be in the past. Please provide a future date."
        except ValueError:
            return "Error: Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-06-01)."

        lease_end_dt = move_in_dt + timedelta(days=lease_duration_months * 30)
        booking_id = f"BOOK-{_uuid.uuid4().hex[:8].upper()}"
        monthly_rent = prop["price"]
        total_cost = monthly_rent * lease_duration_months
        deposit = monthly_rent * 2

        booking_data = {
            "booking_id": booking_id,
            "property_id": pid,
            "property_title": prop["title"],
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "move_in_date": move_in_date,
            "lease_end_date": lease_end_dt.strftime("%Y-%m-%d"),
            "lease_duration_months": lease_duration_months,
            "monthly_rent": monthly_rent,
            "total_cost": total_cost,
            "security_deposit": deposit,
            "status": "confirmed",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        MOCK_BOOKINGS[booking_id] = booking_data

        dur = (time.time() - t0) * 1000
        _log_done("create_booking", dur, {"success": True, "booking_id": booking_id})

        return (
            f"✓ BOOKING CONFIRMED\n"
            f"{'=' * 60}\n\n"
            f"Booking ID: {booking_id}\n"
            f"Status: CONFIRMED\n\n"
            f"PROPERTY DETAILS:\n"
            f"  Property: {prop['title']}\n"
            f"  Property ID: {pid}\n\n"
            f"CUSTOMER INFORMATION:\n"
            f"  Name: {customer_name}\n"
            f"  Email: {customer_email}\n"
            f"  Phone: {customer_phone}\n\n"
            f"LEASE INFORMATION:\n"
            f"  Move-in Date: {move_in_date}\n"
            f"  Lease End Date: {lease_end_dt.strftime('%Y-%m-%d')}\n"
            f"  Lease Duration: {lease_duration_months} months\n\n"
            f"FINANCIAL DETAILS:\n"
            f"  Monthly Rent: ${monthly_rent:,.2f}\n"
            f"  Security Deposit: ${deposit:,.2f}\n"
            f"  Total Lease Cost: ${total_cost:,.2f}\n\n"
            f"Next Steps:\n"
            f"  1. Confirmation email sent to {customer_email}\n"
            f"  2. Security deposit of ${deposit:,.2f} due within 48 hours\n"
            f"  3. Lease agreement will be sent for signing\n"
            f"  4. Property inspection scheduled before move-in\n\n"
            f"Reference Booking ID ({booking_id}) for all future communications.\n"
        )

    except Exception as e:
        _log_err("create_booking", e)
        return f"Error creating booking: {e}"


@tool
def check_booking_status(booking_id: str) -> str:
    """
    Check the status of an existing booking.

    Args:
        booking_id: The booking ID to check (e.g., 'BOOK-ABC12345')

    Returns:
        Booking status and details
    """
    t0 = time.time()
    _log_tool("check_booking_status", {"booking_id": booking_id})

    try:
        bid = booking_id.upper()
        if bid not in MOCK_BOOKINGS:
            _log_done("check_booking_status", (time.time() - t0) * 1000, {"found": False})
            return f"Error: Booking with ID '{booking_id}' not found. Please check the booking ID and try again."

        b = MOCK_BOOKINGS[bid]
        _log_done("check_booking_status", (time.time() - t0) * 1000, {"found": True, "status": b["status"]})

        return (
            f"BOOKING STATUS REPORT\n"
            f"{'=' * 60}\n\n"
            f"Booking ID: {b['booking_id']}\n"
            f"Status: {b['status'].upper()}\n"
            f"Created: {b['created_at']}\n\n"
            f"PROPERTY:\n"
            f"  {b['property_title']} (ID: {b['property_id']})\n\n"
            f"CUSTOMER:\n"
            f"  Name: {b['customer_name']}\n"
            f"  Email: {b['customer_email']}\n"
            f"  Phone: {b['customer_phone']}\n\n"
            f"LEASE DATES:\n"
            f"  Move-in: {b['move_in_date']}\n"
            f"  Lease End: {b['lease_end_date']}\n"
            f"  Duration: {b['lease_duration_months']} months\n\n"
            f"FINANCIALS:\n"
            f"  Monthly Rent: ${b['monthly_rent']:,.2f}\n"
            f"  Security Deposit: ${b['security_deposit']:,.2f}\n"
            f"  Total Cost: ${b['total_cost']:,.2f}\n"
        )

    except Exception as e:
        _log_err("check_booking_status", e)
        return f"Error checking booking status: {e}"


@tool
def cancel_booking(booking_id: str, reason: Optional[str] = None) -> str:
    """
    Cancel an existing booking.

    Args:
        booking_id: The booking ID to cancel (e.g., 'BOOK-ABC12345')
        reason: Optional reason for cancellation

    Returns:
        Cancellation confirmation
    """
    t0 = time.time()
    _log_tool("cancel_booking", {"booking_id": booking_id, "reason": reason})

    try:
        bid = booking_id.upper()
        if bid not in MOCK_BOOKINGS:
            _log_done("cancel_booking", (time.time() - t0) * 1000, {"success": False, "reason": "not_found"})
            return f"Error: Booking with ID '{booking_id}' not found."

        b = MOCK_BOOKINGS[bid]
        if b["status"] == "cancelled":
            return f"Error: Booking '{booking_id}' is already cancelled."

        b["status"] = "cancelled"
        b["cancelled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if reason:
            b["cancellation_reason"] = reason

        _log_done("cancel_booking", (time.time() - t0) * 1000, {"success": True})

        confirmation = (
            f"✓ BOOKING CANCELLED\n"
            f"{'=' * 60}\n\n"
            f"Booking ID: {b['booking_id']}\n"
            f"Status: CANCELLED\n"
            f"Cancelled At: {b['cancelled_at']}\n\n"
            f"PROPERTY:\n"
            f"  {b['property_title']} (ID: {b['property_id']})\n\n"
            f"CUSTOMER:\n"
            f"  Name: {b['customer_name']}\n"
            f"  Email: {b['customer_email']}\n\n"
        )
        if reason:
            confirmation += f"CANCELLATION REASON:\n  {reason}\n\n"
        confirmation += (
            f"REFUND INFORMATION:\n"
            f"  Refund confirmation sent to {b['customer_email']}\n"
            f"  Security deposit refunded within 7-10 business days\n"
        )
        return confirmation

    except Exception as e:
        _log_err("cancel_booking", e)
        return f"Error cancelling booking: {e}"


@tool
def list_customer_bookings(customer_email: str) -> str:
    """
    List all bookings for a specific customer.

    Args:
        customer_email: Email address of the customer

    Returns:
        List of customer's bookings
    """
    t0 = time.time()
    _log_tool("list_customer_bookings", {"customer_email": customer_email})

    try:
        matches = [b for b in MOCK_BOOKINGS.values() if b["customer_email"].lower() == customer_email.lower()]
        dur = (time.time() - t0) * 1000
        _log_done("list_customer_bookings", dur, {"count": len(matches)})

        if not matches:
            return f"No bookings found for customer email: {customer_email}"

        lines = [f"Found {len(matches)} booking(s) for {customer_email}:\n"]
        for i, b in enumerate(matches, 1):
            lines.append(
                f"\n{i}. Booking ID: {b['booking_id']}\n"
                f"   Property: {b['property_title']}\n"
                f"   Status: {b['status'].upper()}\n"
                f"   Move-in: {b['move_in_date']}\n"
                f"   Monthly Rent: ${b['monthly_rent']:,.2f}\n"
                f"   Created: {b['created_at']}\n"
            )
        return "".join(lines)

    except Exception as e:
        _log_err("list_customer_bookings", e)
        return f"Error listing customer bookings: {e}"


# ── Agent & A2A server ────────────────────────────────────────────────────────

def create_agent() -> Agent:
    return Agent(
        name=os.getenv("AGENT_NAME", "Property Booking Agent"),
        description=os.getenv(
            "AGENT_DESCRIPTION",
            "Manages property bookings, reservations, and lease agreements for real estate properties",
        ),
        tools=[create_booking, check_booking_status, cancel_booking, list_customer_bookings],
        model=MODEL_ID,
    )


def create_server() -> A2AServer:
    agent = create_agent()
    host = os.getenv("AGENT_HOST", "0.0.0.0")  # nosec B104
    port = int(os.getenv("AGENT_PORT", "5001"))
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
    print(f"Property Booking Agent A2A server → http://{server.host}:{server.port}")
    print(f"Agent card: http://{server.host}:{server.port}/.well-known/agent-card.json")
    server.serve()
