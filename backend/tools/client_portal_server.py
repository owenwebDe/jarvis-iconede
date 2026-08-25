"""Client Portal MCP Server.

External-facing dashboard for clients to view their leads, campaigns, and reports.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("client_portal")
mcp = FastMCP("ClientPortal")


# Client storage
_clients: Dict[str, Dict[str, Any]] = {}
_client_data: Dict[str, Dict[str, Any]] = {
    "leads": {},
    "campaigns": {},
    "reports": {},
    "invoices": {},
}
_client_tokens: Dict[str, Dict[str, Any]] = {}


@mcp.tool()
def create_client(
    client_id: str,
    company_name: str,
    contact_name: str,
    email: str,
    phone: str = "",
    industry: str = "",
    package: str = "standard",
) -> str:
    """Create a new client account.

    Args:
        client_id: Unique client identifier
        company_name: Client company name
        contact_name: Primary contact name
        email: Contact email
        phone: Contact phone (optional)
        industry: Client industry (optional)
        package: Service package ('basic', 'standard', 'premium')

    Returns:
        JSON with client details
    """
    if client_id in _clients:
        return json.dumps({"status": "error", "message": "Client already exists"})

    _clients[client_id] = {
        "id": client_id,
        "company_name": company_name,
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
        "industry": industry,
        "package": package,
        "created_at": time.time(),
        "active": True,
    }

    # Initialize empty data
    _client_data["leads"][client_id] = []
    _client_data["campaigns"][client_id] = []
    _client_data["reports"][client_id] = []
    _client_data["invoices"][client_id] = []

    return json.dumps({
        "status": "created",
        "client_id": client_id,
        "company_name": company_name,
        "package": package,
    })


@mcp.tool()
def generate_client_token(client_id: str) -> str:
    """Generate access token for client portal.

    Args:
        client_id: Client ID

    Returns:
        JSON with access token
    """
    if client_id not in _clients:
        return json.dumps({"status": "error", "message": "Client not found"})

    import secrets
    token = secrets.token_hex(32)

    _client_tokens[token] = {
        "client_id": client_id,
        "created_at": time.time(),
        "expires_at": time.time() + 30 * 86400,  # 30 days
    }

    return json.dumps({
        "status": "success",
        "token": token,
        "client_id": client_id,
        "expires_in_days": 30,
    })


@mcp.tool()
def add_client_lead(
    client_id: str,
    company_name: str,
    contact_name: str,
    score: int,
    status: str = "new",
) -> str:
    """Add a lead to client's dashboard.

    Args:
        client_id: Client ID
        company_name: Lead company
        contact_name: Lead contact
        score: Lead score (0-100)
        status: Lead status

    Returns:
        JSON confirmation
    """
    if client_id not in _client_data["leads"]:
        return json.dumps({"status": "error", "message": "Client not found"})

    lead = {
        "id": f"lead-{int(time.time())}",
        "company_name": company_name,
        "contact_name": contact_name,
        "score": score,
        "status": status,
        "created_at": time.time(),
    }

    _client_data["leads"][client_id].append(lead)

    return json.dumps({
        "status": "added",
        "client_id": client_id,
        "lead_id": lead["id"],
        "score": score,
    })


@mcp.tool()
def add_client_campaign(
    client_id: str,
    campaign_name: str,
    status: str = "active",
    budget: float = 0,
    spent: float = 0,
    conversions: int = 0,
) -> str:
    """Add a campaign to client's dashboard.

    Args:
        client_id: Client ID
        campaign_name: Campaign name
        status: Campaign status
        budget: Campaign budget
        spent: Amount spent
        conversions: Number of conversions

    Returns:
        JSON confirmation
    """
    if client_id not in _client_data["campaigns"]:
        return json.dumps({"status": "error", "message": "Client not found"})

    campaign = {
        "id": f"camp-{int(time.time())}",
        "name": campaign_name,
        "status": status,
        "budget": budget,
        "spent": spent,
        "conversions": conversions,
        "created_at": time.time(),
    }

    _client_data["campaigns"][client_id].append(campaign)

    return json.dumps({
        "status": "added",
        "client_id": client_id,
        "campaign_id": campaign["id"],
    })


@mcp.tool()
def get_client_dashboard(token: str) -> str:
    """Get client dashboard data.

    Args:
        token: Client access token

    Returns:
        JSON with dashboard data
    """
    token_data = _client_tokens.get(token)
    if not token_data or time.time() > token_data["expires_at"]:
        return json.dumps({"status": "error", "message": "Invalid or expired token"})

    client_id = token_data["client_id"]
    client = _clients.get(client_id)

    leads = _client_data["leads"].get(client_id, [])
    campaigns = _client_data["campaigns"].get(client_id, [])

    # Calculate metrics
    total_leads = len(leads)
    qualified_leads = len([l for l in leads if l["score"] >= 70])
    total_campaigns = len(campaigns)
    active_campaigns = len([c for c in campaigns if c["status"] == "active"])
    total_budget = sum(c["budget"] for c in campaigns)
    total_spent = sum(c["spent"] for c in campaigns)
    total_conversions = sum(c["conversions"] for c in campaigns)

    return json.dumps({
        "status": "success",
        "client": {
            "company": client["company_name"],
            "contact": client["contact_name"],
            "package": client["package"],
        },
        "metrics": {
            "total_leads": total_leads,
            "qualified_leads": qualified_leads,
            "lead_quality_rate": f"{(qualified_leads / total_leads * 100) if total_leads > 0 else 0:.1f}%",
            "total_campaigns": total_campaigns,
            "active_campaigns": active_campaigns,
            "total_budget": total_budget,
            "total_spent": total_spent,
            "remaining_budget": total_budget - total_spent,
            "total_conversions": total_conversions,
            "cost_per_conversion": f"{(total_spent / total_conversions) if total_conversions > 0 else 0:.2f}",
        },
        "recent_leads": leads[-5:],
        "active_campaigns": [c for c in campaigns if c["status"] == "active"][:3],
    })


@mcp.tool()
def get_client_leads(token: str, status: str = "", limit: int = 50) -> str:
    """Get client's leads.

    Args:
        token: Client access token
        status: Filter by status
        limit: Max leads (default 50)

    Returns:
        JSON with leads
    """
    token_data = _client_tokens.get(token)
    if not token_data or time.time() > token_data["expires_at"]:
        return json.dumps({"status": "error", "message": "Invalid or expired token"})

    client_id = token_data["client_id"]
    leads = _client_data["leads"].get(client_id, [])

    if status:
        leads = [l for l in leads if l["status"] == status]

    leads = leads[-limit:]
    leads.reverse()

    return json.dumps({
        "status": "success",
        "leads": leads,
        "total": len(leads),
    })


@mcp.tool()
def get_client_campaigns(token: str) -> str:
    """Get client's campaigns.

    Args:
        token: Client access token

    Returns:
        JSON with campaigns
    """
    token_data = _client_tokens.get(token)
    if not token_data or time.time() > token_data["expires_at"]:
        return json.dumps({"status": "error", "message": "Invalid or expired token"})

    client_id = token_data["client_id"]
    campaigns = _client_data["campaigns"].get(client_id, [])

    return json.dumps({
        "status": "success",
        "campaigns": campaigns,
        "total": len(campaigns),
    })


@mcp.tool()
def generate_client_report(
    client_id: str,
    report_type: str = "monthly",
    period: str = "",
) -> str:
    """Generate a report for a client.

    Args:
        client_id: Client ID
        report_type: Report type ('weekly', 'monthly', 'quarterly')
        period: Specific period (optional)

    Returns:
        JSON with report
    """
    client = _clients.get(client_id)
    if not client:
        return json.dumps({"status": "error", "message": "Client not found"})

    leads = _client_data["leads"].get(client_id, [])
    campaigns = _client_data["campaigns"].get(client_id, [])

    report = {
        "id": f"report-{int(time.time())}",
        "client_id": client_id,
        "company_name": client["company_name"],
        "type": report_type,
        "generated_at": time.time(),
        "summary": {
            "total_leads": len(leads),
            "qualified_leads": len([l for l in leads if l["score"] >= 70]),
            "total_campaigns": len(campaigns),
            "total_conversions": sum(c["conversions"] for c in campaigns),
            "total_spent": sum(c["spent"] for c in campaigns),
        },
    }

    _client_data["reports"][client_id].append(report)

    return json.dumps({
        "status": "generated",
        "report": report,
    })


@mcp.tool()
def list_clients() -> str:
    """List all clients.

    Returns:
        JSON with client list
    """
    clients = []
    for cid, client in _clients.items():
        leads_count = len(_client_data["leads"].get(cid, []))
        campaigns_count = len(_client_data["campaigns"].get(cid, []))

        clients.append({
            "id": cid,
            "company_name": client["company_name"],
            "contact_name": client["contact_name"],
            "package": client["package"],
            "active": client["active"],
            "leads_count": leads_count,
            "campaigns_count": campaigns_count,
        })

    return json.dumps({
        "status": "success",
        "clients": clients,
        "total": len(clients),
    })


if __name__ == "__main__":
    mcp.run()
