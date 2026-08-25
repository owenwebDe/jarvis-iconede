"""Lean Lead Memory MCP Tool Server.

Provides ONLY prospect/lead tools to LeadResearchAgent without loading
the full shared-memory server (ad_creative, campaign, board_meeting tools).
This reduces tool schema tokens from ~12 to ~2 for token-budget-sensitive agents.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).parent.parent))

from services import shared_memory

logger = logging.getLogger("lead_memory_server")
mcp = FastMCP("IconEdgeLeadMemory")


@mcp.tool()
def prospect_save(
    company_name: str,
    contact_name: str = "",
    email: str = "",
    phone: str = "",
    website: str = "",
    country: str = "Global",
    city: str = "",
    industry: str = "",
    source_agent: str = "LeadResearchAgent",
    status: str = "new",
    lead_score: int = 50,
    notes: str = "",
) -> dict:
    """Save or update a business lead/prospect into shared persistent memory.

    Use this tool whenever you discover new businesses or update contact status.
    """
    try:
        return shared_memory.upsert_prospect(
            company_name=company_name,
            contact_name=contact_name or None,
            email=email or None,
            phone=phone or None,
            website=website or None,
            country=country or "Global",
            city=city or None,
            industry=industry or None,
            source_agent=source_agent,
            status=status,
            lead_score=lead_score,
            notes=notes or None,
        )
    except Exception as exc:
        logger.exception("Error saving prospect")
        return {"error": str(exc)}


@mcp.tool()
def prospect_search(
    query: str = "",
    status: str = "",
    country: str = "",
    industry: str = "",
    limit: int = 20,
) -> dict:
    """Search and query stored prospects in shared memory.

    Allows filtering by keyword, status ('new', 'qualified', 'contacted', 'converted'),
    country, or industry.
    """
    try:
        results = shared_memory.search_prospects(
            query=query or None,
            status=status or None,
            country=country or None,
            industry=industry or None,
            limit=limit,
        )
        return {"prospects": results, "count": len(results)}
    except Exception as exc:
        return {"error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
