"""Multi-Source Search MCP Server.

Provides parallel search across multiple sources for comprehensive lead research.
Used by LeadResearchAgent for deep prospect discovery.
"""
from __future__ import annotations

import json
import logging
import asyncio
import urllib.request
import urllib.parse
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from mcp.server.fastmcp import FastMCP
from ddgs import DDGS
from bs4 import BeautifulSoup

logger = logging.getLogger("multi_source_search")
mcp = FastMCP("MultiSourceSearch")

# Thread pool for parallel I/O operations
_executor = ThreadPoolExecutor(max_workers=5)


def _search_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search DuckDuckGo and return structured results."""
    try:
        results = list(DDGS().text(query, max_results=max_results))
        return [
            {
                "source": "duckduckgo",
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}")
        return []


def _search_linkedin(company_name: str) -> List[Dict[str, str]]:
    """Search LinkedIn for company info (via DuckDuckGo site-specific search)."""
    try:
        query = f"site:linkedin.com/company {company_name}"
        results = list(DDGS().text(query, max_results=3))
        return [
            {
                "source": "linkedin",
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"LinkedIn search failed: {e}")
        return []


def _search_twitter(query: str) -> List[Dict[str, str]]:
    """Search Twitter/X for businesses."""
    try:
        results = list(DDGS().text(f"site:twitter.com {query} business", max_results=3))
        return [
            {"source": "twitter", "title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in results
        ]
    except Exception as e:
        logger.warning(f"Twitter search failed: {e}")
        return []


def _search_crunchbase(query: str) -> List[Dict[str, str]]:
    """Search Crunchbase for company data."""
    try:
        results = list(DDGS().text(f"site:crunchbase.com {query}", max_results=3))
        return [
            {"source": "crunchbase", "title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in results
        ]
    except Exception as e:
        logger.warning(f"Crunchbase search failed: {e}")
        return []


def _scrape_company_page(url: str, max_chars: int = 3000) -> Dict[str, Any]:
    """Scrape a company website for contact info and key details."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="replace")
            soup = BeautifulSoup(html, "html.parser")

            # Remove scripts and styles
            for script in soup(["script", "style", "nav", "footer"]):
                script.extract()

            text = soup.get_text(separator=" ", strip=True)
            if len(text) > max_chars:
                text = text[:max_chars] + "..."

            # Extract emails and phones
            emails = list(set(re.findall(r'[\w.-]+@[\w.-]+\.\w+', text)))
            phones = list(set(re.findall(r'[\+\(]?\d[\d\s\-\(\)]{7,}\d', text)))

            return {
                "url": url,
                "text_preview": text[:1000],
                "emails_found": emails[:3],
                "phones_found": phones[:3],
            }
    except Exception as e:
        return {"url": url, "error": str(e)}


@mcp.tool()
def multi_source_search(
    query: str,
    industry: str = "",
    location: str = "",
    max_results_per_source: int = 5,
) -> str:
    """Search across multiple sources in parallel for comprehensive lead research.

    Combines DuckDuckGo web search, LinkedIn, Twitter, and Crunchbase
    to find business contacts and company information.

    Args:
        query: Main search query (e.g., 'logistics companies', 'digital agencies')
        industry: Industry filter (e.g., 'technology', 'healthcare', 'finance')
        location: Location filter (e.g., 'Abuja', 'London', 'New York')
        max_results_per_source: Max results per source (default 5)

    Returns:
        JSON string with combined results from all sources
    """
    # Build search queries for different sources
    full_query = f"{query} {industry} {location}".strip()

    # Run searches in parallel using thread pool
    loop = asyncio.get_event_loop()

    async def run_parallel_searches():
        futures = [
            loop.run_in_executor(_executor, _search_duckduckgo, full_query, max_results_per_source),
            loop.run_in_executor(_executor, _search_linkedin, f"{query} {industry}"),
            loop.run_in_executor(_executor, _search_twitter, full_query),
            loop.run_in_executor(_executor, _search_crunchbase, query),
        ]
        return await asyncio.gather(*futures, return_exceptions=True)

    try:
        results = asyncio.run(run_parallel_searches())
    except Exception as e:
        logger.error(f"Parallel search failed: {e}")
        results = [[], [], [], []]

    # Combine results
    all_results = {
        "duckduckgo": results[0] if isinstance(results[0], list) else [],
        "linkedin": results[1] if isinstance(results[1], list) else [],
        "twitter": results[2] if isinstance(results[2], list) else [],
        "crunchbase": results[3] if isinstance(results[3], list) else [],
    }

    totals = {source: len(r) for source, r in all_results.items()}

    return json.dumps({
        "status": "success",
        "query": full_query,
        "totals": totals,
        "results": all_results,
    }, indent=2)


@mcp.tool()
def enrich_company(url: str, max_chars: int = 3000) -> str:
    """Scrape a company website to extract contact info and key details.

    Args:
        url: Company website URL to scrape
        max_chars: Max characters to extract (default 3000)

    Returns:
        JSON string with extracted company info
    """
    result = _scrape_company_page(url, max_chars)
    return json.dumps(result, indent=2)


@mcp.tool()
def find_decision_makers(company_name: str, industry: str = "") -> str:
    """Search for key decision-makers at a company.

    Uses LinkedIn and web search to find CEO, COO, Marketing Director,
    and other C-level contacts.

    Args:
        company_name: Company name to search
        industry: Industry for context (optional)

    Returns:
        JSON string with potential contacts found
    """
    queries = [
        f"CEO {company_name} {industry}",
        f"COO {company_name} contact",
        f"Marketing Director {company_name} LinkedIn",
        f"{company_name} leadership team",
    ]

    all_contacts = []
    for query in queries[:3]:
        results = _search_duckduckgo(query, max_results=3)
        for r in results:
            title = r.get("title", "").lower()
            if any(t in title for t in ["ceo", "coo", "director", "founder", "owner", "manager"]):
                all_contacts.append({
                    "name": r.get("title", ""),
                    "role": next((t.upper() for t in ["CEO", "COO", "Director", "Founder", "Owner"] if t.lower() in title), "Unknown"),
                    "source_url": r.get("url", ""),
                    "snippet": r.get("snippet", ""),
                })

    # Deduplicate
    seen = set()
    unique_contacts = []
    for c in all_contacts:
        key = c["name"].lower()
        if key not in seen:
            seen.add(key)
            unique_contacts.append(c)

    return json.dumps({
        "company": company_name,
        "contacts_found": len(unique_contacts),
        "contacts": unique_contacts[:10],
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
