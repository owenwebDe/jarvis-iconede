"""Web Search & Scraping FastMCP Server.

Provides live DuckDuckGo web search and webpage content extraction for
LeadResearchAgent and ResearchAgent without requiring paid API keys.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from bs4 import BeautifulSoup
from ddgs import DDGS
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("web_search_server")
mcp = FastMCP("WebSearchService")


@mcp.tool()
def web_search(query: str, max_results: int = 8) -> str:
    """Search the live web using DuckDuckGo.

    Returns real-time search results including titles, links, and snippets.

    Args:
        query: Search query (e.g. 'restaurants in Wuse 2 Abuja phone whatsapp').
        max_results: Max number of results to return (default 8).
    """
    try:
        results = list(DDGS().text(query, max_results=max_results))
        return json.dumps({
            "status": "success",
            "query": query,
            "count": len(results),
            "results": results,
        }, indent=2)
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}")
        return json.dumps({"status": "error", "message": f"Search error: {e}"})


@mcp.tool()
def scrape_webpage(url: str, max_chars: int = 8000) -> str:
    """Fetch and extract clean readable text from any website URL.

    Args:
        url: The web page URL to scrape.
        max_chars: Max characters to return (default 8000).
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode("utf-8", errors="replace")
            soup = BeautifulSoup(html, "html.parser")

            # Remove scripts and styles
            for script in soup(["script", "style", "nav", "footer"]):
                script.extract()

            text = soup.get_text(separator=" ", strip=True)
            if len(text) > max_chars:
                text = text[:max_chars] + "... [truncated]"

            return json.dumps({
                "status": "success",
                "url": url,
                "text": text,
            }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to scrape '{url}': {e}"})


if __name__ == "__main__":
    mcp.run()
