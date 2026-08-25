"""Customer Success MCP Server.

Client onboarding, health scoring, churn prevention, and retention.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("customer_success")
mcp = FastMCP("CustomerSuccess")


# Client storage
_clients: Dict[str, Dict[str, Any]] = {}
_interactions: List[Dict[str, Any]] = []
_tickets: List[Dict[str, Any]] = []


@mcp.tool()
def track_client_health(
    client_id: str,
    health_score: int,
    factors: str = "",
) -> str:
    """Track client health score.

    Args:
        client_id: Client identifier
        health_score: Health score (0-100)
        factors: JSON of health factors (optional)

    Returns:
        JSON confirmation
    """
    if client_id not in _clients:
        _clients[client_id] = {"id": client_id, "interactions": 0}

    _clients[client_id]["health_score"] = health_score
    _clients[client_id]["last_health_check"] = time.time()

    if factors:
        try:
            _clients[client_id]["health_factors"] = json.loads(factors)
        except json.JSONDecodeError:
            pass

    # Determine risk level
    if health_score < 30:
        risk = "critical"
    elif health_score < 50:
        risk = "high"
    elif health_score < 70:
        risk = "medium"
    else:
        risk = "low"

    return json.dumps({
        "status": "tracked",
        "client_id": client_id,
        "health_score": health_score,
        "risk_level": risk,
    })


@mcp.tool()
def log_client_interaction(
    client_id: str,
    interaction_type: str,
    summary: str,
    sentiment: str = "neutral",
) -> str:
    """Log a client interaction.

    Args:
        client_id: Client identifier
        interaction_type: Type ('call', 'email', 'meeting', 'support')
        summary: Interaction summary
        sentiment: Client sentiment ('positive', 'neutral', 'negative')

    Returns:
        JSON confirmation
    """
    interaction = {
        "id": f"interaction-{int(time.time())}",
        "client_id": client_id,
        "type": interaction_type,
        "summary": summary,
        "sentiment": sentiment,
        "timestamp": time.time(),
    }
    _interactions.append(interaction)

    # Update client interaction count
    if client_id in _clients:
        _clients[client_id]["interactions"] = _clients[client_id].get("interactions", 0) + 1
        _clients[client_id]["last_interaction"] = time.time()

    return json.dumps({
        "status": "logged",
        "interaction_id": interaction["id"],
    })


@mcp.tool()
def create_support_ticket(
    client_id: str,
    subject: str,
    description: str,
    priority: str = "medium",
) -> str:
    """Create a support ticket.

    Args:
        client_id: Client identifier
        subject: Ticket subject
        description: Issue description
        priority: Priority ('low', 'medium', 'high', 'urgent')

    Returns:
        JSON with ticket details
    """
    ticket = {
        "id": f"ticket-{int(time.time())}",
        "client_id": client_id,
        "subject": subject,
        "description": description,
        "priority": priority,
        "status": "open",
        "created_at": time.time(),
    }
    _tickets.append(ticket)

    return json.dumps({
        "status": "created",
        "ticket_id": ticket["id"],
    })


@mcp.tool()
def get_client_risk_report() -> str:
    """Get report of at-risk clients.

    Returns:
        JSON with risk report
    """
    at_risk = []
    for client_id, data in _clients.items():
        health = data.get("health_score", 50)
        if health < 50:
            at_risk.append({
                "client_id": client_id,
                "health_score": health,
                "risk_level": "critical" if health < 30 else "high",
                "last_interaction": data.get("last_interaction"),
                "recommendation": _get_retention_recommendation(health),
            })

    # Sort by health score
    at_risk.sort(key=lambda x: x["health_score"])

    return json.dumps({
        "status": "success",
        "at_risk_clients": at_risk,
        "total_at_risk": len(at_risk),
    })


@mcp.tool()
def get_open_tickets(priority: str = "") -> str:
    """Get open support tickets.

    Args:
        priority: Filter by priority

    Returns:
        JSON with open tickets
    """
    open_tickets = [t for t in _tickets if t["status"] == "open"]
    if priority:
        open_tickets = [t for t in open_tickets if t["priority"] == priority]

    # Sort by priority
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    open_tickets.sort(key=lambda x: priority_order.get(x["priority"], 4))

    return json.dumps({
        "status": "success",
        "tickets": open_tickets,
        "total": len(open_tickets),
    })


@mcp.tool()
def get_client_summary(client_id: str) -> str:
    """Get comprehensive client summary.

    Args:
        client_id: Client identifier

    Returns:
        JSON with client summary
    """
    client = _clients.get(client_id, {"id": client_id})
    client_interactions = [i for i in _interactions if i["client_id"] == client_id]
    client_tickets = [t for t in _tickets if t["client_id"] == client_id]

    return json.dumps({
        "status": "success",
        "client": client,
        "total_interactions": len(client_interactions),
        "recent_interactions": client_interactions[-5:],
        "total_tickets": len(client_tickets),
        "open_tickets": len([t for t in client_tickets if t["status"] == "open"]),
    })


def _get_retention_recommendation(health_score: int) -> str:
    """Get retention recommendation based on health score."""
    if health_score < 20:
        return "URGENT: Schedule executive call immediately"
    elif health_score < 30:
        return "Schedule check-in call within 24 hours"
    elif health_score < 40:
        return "Send personalized email and offer support"
    else:
        return "Monitor and schedule regular check-in"


if __name__ == "__main__":
    mcp.run()
