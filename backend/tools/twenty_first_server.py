"""21st.dev Component Marketplace & Local Vault FastMCP Server.

Provides tools for searching 12,000+ UI components on 21st.dev,
retrieving source code, managing daily quotas, and caching everything
in a durable local SQLite vault for offline 0ms reuse.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from services.twenty_first_service import get_twenty_first_vault

logger = logging.getLogger("twenty_first_server")
mcp = FastMCP("TwentyFirstVault")


@mcp.tool()
def twenty_first_get_usage() -> str:
    """Check 21st.dev account tier, daily quota limit, and remaining pulls."""
    vault = get_twenty_first_vault()
    res = vault.get_usage()
    return json.dumps(res, indent=2)


@mcp.tool()
def twenty_first_search(query: str, limit: int = 10) -> str:
    """Search 12,000+ hand-crafted React, Tailwind, and Motion components on 21st.dev.

    Also checks local Component Vault to show already-saved components.

    Args:
        query: Search term (e.g. 'hero', '3d card', 'shader', 'bento grid', 'drawer', 'navbar').
        limit: Max results to return.
    """
    vault = get_twenty_first_vault()
    res = vault.search_components(query=query, limit=limit)
    return json.dumps(res, indent=2)


@mcp.tool()
def twenty_first_get_component(component_id: str) -> str:
    """Download full source code for a component from 21st.dev and automatically save to local vault.

    Prioritizes local vault cache to save daily API quota.

    Args:
        component_id: The ID or slug of the component (from twenty_first_search).
    """
    vault = get_twenty_first_vault()
    res = vault.get_component_code(component_id_or_slug=component_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def twenty_first_list_vault(limit: int = 50) -> str:
    """List all components currently stored in the local Component Vault."""
    vault = get_twenty_first_vault()
    items = vault.list_vaulted_components(limit=limit)
    return json.dumps({
        "status": "success",
        "cached_count": len(items),
        "components": items,
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
