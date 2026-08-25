"""Comprehensive Lead Sources MCP Server.

Provides access to ALL possible B2B lead generation sources:
- Web search (DuckDuckGo, Bing)
- Social media (Twitter/X, LinkedIn, Facebook, Instagram)
- Business directories (Yelp, Yellow Pages, industry-specific)
- Startup platforms (AngelList, Crunchbase, Product Hunt)
- Tech communities (GitHub, Indie Hackers, Dev.to)
- Agency platforms (Clutch, G2, Capterra)
- Job boards (Indeed, LinkedIn Jobs - hiring = growing)
- News & press releases
- Trade associations & chambers of commerce
- Conference speakers & podcast guests
"""
from __future__ import annotations

import json
import logging
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from mcp.server.fastmcp import FastMCP
from ddgs import DDGS
from bs4 import BeautifulSoup

logger = logging.getLogger("lead_sources")
mcp = FastMCP("LeadSources")

# Thread pool for parallel I/O
_executor = ThreadPoolExecutor(max_workers=8)


# ══════════════════════════════════════════════════════════════════════════════
# CORE SEARCH FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _ddg_search(query: str, max_results: int = 8) -> List[Dict[str, str]]:
    """Search DuckDuckGo."""
    try:
        results = list(DDGS().text(query, max_results=max_results))
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in results
        ]
    except Exception as e:
        logger.warning(f"DDG search failed: {e}")
        return []


def _scrape_page(url: str, max_chars: int = 2000) -> str:
    """Scrape a webpage for text content."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.extract()
            text = soup.get_text(separator=" ", strip=True)
            return text[:max_chars] if len(text) > max_chars else text
    except Exception as e:
        return f"Error: {e}"


def _extract_emails(text: str) -> List[str]:
    """Extract email addresses from text."""
    return list(set(re.findall(r'[\w.-]+@[\w.-]+\.\w+', text)))[:5]


def _extract_phones(text: str) -> List[str]:
    """Extract phone numbers from text."""
    return list(set(re.findall(r'[\+\(]?\d[\d\s\-\(\)]{7,}\d', text)))[:5]


# ══════════════════════════════════════════════════════════════════════════════
# LEAD SOURCE: SOCIAL MEDIA
# ══════════════════════════════════════════════════════════════════════════════

def _search_twitter(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Twitter/X for businesses and decision-makers."""
    results = _ddg_search(f"site:twitter.com {query} business", max_results)
    return [{"source": "twitter", **r} for r in results]


def _search_linkedin_people(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search LinkedIn for people/decision-makers."""
    results = _ddg_search(f"site:linkedin.com/in {query} CEO OR founder OR director", max_results)
    return [{"source": "linkedin_people", **r} for r in results]


def _search_linkedin_companies(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search LinkedIn for company pages."""
    results = _ddg_search(f"site:linkedin.com/company {query}", max_results)
    return [{"source": "linkedin_companies", **r} for r in results]


def _search_facebook_business(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Facebook for business pages."""
    results = _ddg_search(f"site:facebook.com {query} business page", max_results)
    return [{"source": "facebook", **r} for r in results]


def _search_instagram_business(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Instagram for business accounts."""
    results = _ddg_search(f"site:instagram.com {query} business official", max_results)
    return [{"source": "instagram", **r} for r in results]


# ══════════════════════════════════════════════════════════════════════════════
# LEAD SOURCE: BUSINESS DIRECTORIES
# ══════════════════════════════════════════════════════════════════════════════

def _search_yelp(query: str, location: str = "", max_results: int = 5) -> List[Dict[str, str]]:
    """Search Yelp for local businesses."""
    search = f"site:yelp.com {query} {location}".strip()
    results = _ddg_search(search, max_results)
    return [{"source": "yelp", **r} for r in results]


def _search_yellow_pages(query: str, location: str = "", max_results: int = 5) -> List[Dict[str, str]]:
    """Search Yellow Pages for businesses."""
    search = f"site:yellowpages.com {query} {location}".strip()
    results = _ddg_search(search, max_results)
    return [{"source": "yellow_pages", **r} for r in results]


def _search_chamber_of_commerce(location: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Chamber of Commerce directories."""
    results = _ddg_search(f"site:chamberofcommerce.com {location} members", max_results)
    return [{"source": "chamber_of_commerce", **r} for r in results]


def _search_tradewind(industry: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search trade association member directories."""
    results = _ddg_search(f"{industry} association members directory", max_results)
    return [{"source": "trade_association", **r} for r in results]


# ══════════════════════════════════════════════════════════════════════════════
# LEAD SOURCE: STARTUP & TECH PLATFORMS
# ══════════════════════════════════════════════════════════════════════════════

def _search_crunchbase(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Crunchbase for company data."""
    results = _ddg_search(f"site:crunchbase.com {query}", max_results)
    return [{"source": "crunchbase", **r} for r in results]


def _search_angellist(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search AngelList/Wellfound for startups."""
    results = _ddg_search(f"site:wellfound.com {query} startup", max_results)
    return [{"source": "angellist", **r} for r in results]


def _search_product_hunt(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Product Hunt for new companies."""
    results = _ddg_search(f"site:producthunt.com {query}", max_results)
    return [{"source": "product_hunt", **r} for r in results]


def _search_github_orgs(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search GitHub for tech company organizations."""
    results = _ddg_search(f"site:github.com {query} organization", max_results)
    return [{"source": "github", **r} for r in results]


def _search_indie_hackers(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Indie Hackers for small business founders."""
    results = _ddg_search(f"site:indiehackers.com {query}", max_results)
    return [{"source": "indie_hackers", **r} for r in results]


# ══════════════════════════════════════════════════════════════════════════════
# LEAD SOURCE: REVIEW & COMPARISON PLATFORMS
# ══════════════════════════════════════════════════════════════════════════════

def _search_clutch(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Clutch for agencies and service providers."""
    results = _ddg_search(f"site:clutch.co {query}", max_results)
    return [{"source": "clutch", **r} for r in results]


def _search_g2(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search G2 for software companies."""
    results = _ddg_search(f"site:g2.com {query}", max_results)
    return [{"source": "g2", **r} for r in results]


def _search_capterra(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Capterra for software vendors."""
    results = _ddg_search(f"site:capterra.com {query}", max_results)
    return [{"source": "capterra", **r} for r in results]


# ══════════════════════════════════════════════════════════════════════════════
# LEAD SOURCE: JOB BOARDS (Hiring = Growing Companies)
# ══════════════════════════════════════════════════════════════════════════════

def _search_indeed_jobs(query: str, location: str = "", max_results: int = 5) -> List[Dict[str, str]]:
    """Search Indeed for companies hiring (signal of growth)."""
    search = f"site:indeed.com {query} jobs {location}".strip()
    results = _ddg_search(search, max_results)
    return [{"source": "indeed_jobs", **r} for r in results]


def _search_linkedin_jobs(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search LinkedIn Jobs for active hirers."""
    results = _ddg_search(f"site:linkedin.com/jobs {query}", max_results)
    return [{"source": "linkedin_jobs", **r} for r in results]


def _search_glassdoor(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Glassdoor for company info and hiring signals."""
    results = _ddg_search(f"site:glassdoor.com {query} company", max_results)
    return [{"source": "glassdoor", **r} for r in results]


# ══════════════════════════════════════════════════════════════════════════════
# LEAD SOURCE: NEWS & PRESS
# ══════════════════════════════════════════════════════════════════════════════

def _search_news_companies(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search news for companies in the spotlight (funding, launches, etc.)."""
    results = _ddg_search(f"{query} company funding OR launch OR announcement", max_results)
    return [{"source": "news", **r} for r in results]


def _search_pr_newswire(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search press releases for company announcements."""
    results = _ddg_search(f"site:prnewswire.com {query}", max_results)
    return [{"source": "pr_newswire", **r} for r in results]


# ══════════════════════════════════════════════════════════════════════════════
# LEAD SOURCE: COMMUNITY & EVENTS
# ══════════════════════════════════════════════════════════════════════════════

def _search_conference_speakers(industry: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search for conference speakers (thought leaders = decision-makers)."""
    results = _ddg_search(f"{industry} conference speaker 2024 2025", max_results)
    return [{"source": "conference_speakers", **r} for r in results]


def _search_podcast_guests(industry: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search for podcast guests in the industry."""
    results = _ddg_search(f"{industry} podcast guest founder CEO", max_results)
    return [{"source": "podcast_guests", **r} for r in results]


def _search_reddit_business(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Reddit for business discussions and founders."""
    results = _ddg_search(f"site:reddit.com {query} founder owner business", max_results)
    return [{"source": "reddit", **r} for r in results]


def _search_quora_experts(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search Quora for industry experts and founders."""
    results = _ddg_search(f"site:quora.com {query} founder CEO expert", max_results)
    return [{"source": "quora", **r} for r in results]


# ══════════════════════════════════════════════════════════════════════════════
# LEAD SOURCE: GOVERNMENT & PUBLIC RECORDS
# ══════════════════════════════════════════════════════════════════════════════

def _search_business_registrations(query: str, location: str = "", max_results: int = 5) -> List[Dict[str, str]]:
    """Search government business registrations."""
    search = f"{query} business registration {location} official".strip()
    results = _ddg_search(search, max_results)
    return [{"source": "gov_registration", **r} for r in results]


def _search_sec_filings(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search SEC for company filings (public companies)."""
    results = _ddg_search(f"site:sec.gov {query} filing", max_results)
    return [{"source": "sec_filings", **r} for r in results]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN TOOL: COMPREHENSIVE LEAD SEARCH
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def comprehensive_lead_search(
    industry: str,
    location: str = "",
    company_size: str = "",
    sources: str = "all",
    max_results_per_source: int = 5,
) -> str:
    """Search ALL possible lead sources for comprehensive B2B prospect discovery.

    Args:
        industry: Target industry (e.g., 'logistics', 'healthcare', 'fintech')
        location: Target location (e.g., 'Abuja', 'London', 'New York')
        company_size: Target size ('startup', 'smb', 'midmarket', 'enterprise')
        sources: Comma-separated list of sources to search, or 'all' for everything
                 Options: social, directories, startups, reviews, jobs, news, community, gov, all
        max_results_per_source: Max results per source (default 5)

    Returns:
        JSON with leads grouped by source category
    """
    query = f"{industry} {company_size}".strip()

    # Define source groups
    source_groups = {
        "social": [
            ("Twitter/X", lambda: _search_twitter(query, max_results_per_source)),
            ("LinkedIn People", lambda: _search_linkedin_people(f"{industry} {location}", max_results_per_source)),
            ("LinkedIn Companies", lambda: _search_linkedin_companies(query, max_results_per_source)),
            ("Facebook Business", lambda: _search_facebook_business(query, max_results_per_source)),
            ("Instagram Business", lambda: _search_instagram_business(query, max_results_per_source)),
        ],
        "directories": [
            ("Yelp", lambda: _search_yelp(industry, location, max_results_per_source)),
            ("Yellow Pages", lambda: _search_yellow_pages(industry, location, max_results_per_source)),
            ("Chamber of Commerce", lambda: _search_chamber_of_commerce(location, max_results_per_source)),
            ("Trade Associations", lambda: _search_tradewind(industry, max_results_per_source)),
        ],
        "startups": [
            ("Crunchbase", lambda: _search_crunchbase(query, max_results_per_source)),
            ("AngelList/Wellfound", lambda: _search_angellist(query, max_results_per_source)),
            ("Product Hunt", lambda: _search_product_hunt(industry, max_results_per_source)),
            ("GitHub Orgs", lambda: _search_github_orgs(query, max_results_per_source)),
            ("Indie Hackers", lambda: _search_indie_hackers(query, max_results_per_source)),
        ],
        "reviews": [
            ("Clutch", lambda: _search_clutch(query, max_results_per_source)),
            ("G2", lambda: _search_g2(query, max_results_per_source)),
            ("Capterra", lambda: _search_capterra(query, max_results_per_source)),
        ],
        "jobs": [
            ("Indeed Jobs", lambda: _search_indeed_jobs(industry, location, max_results_per_source)),
            ("LinkedIn Jobs", lambda: _search_linkedin_jobs(query, max_results_per_source)),
            ("Glassdoor", lambda: _search_glassdoor(query, max_results_per_source)),
        ],
        "news": [
            ("News", lambda: _search_news_companies(query, max_results_per_source)),
            ("PR Newswire", lambda: _search_pr_newswire(query, max_results_per_source)),
        ],
        "community": [
            ("Conference Speakers", lambda: _search_conference_speakers(industry, max_results_per_source)),
            ("Podcast Guests", lambda: _search_podcast_guests(industry, max_results_per_source)),
            ("Reddit", lambda: _search_reddit_business(query, max_results_per_source)),
            ("Quora", lambda: _search_quora_experts(query, max_results_per_source)),
        ],
        "gov": [
            ("Business Registrations", lambda: _search_business_registrations(industry, location, max_results_per_source)),
            ("SEC Filings", lambda: _search_sec_filings(query, max_results_per_source)),
        ],
    }

    # Determine which sources to search
    if sources == "all":
        active_groups = list(source_groups.keys())
    else:
        active_groups = [s.strip() for s in sources.split(",") if s.strip() in source_groups]

    # Execute searches
    results = {}
    totals = {}

    for group_name in active_groups:
        group_results = {}
        for source_name, search_fn in source_groups[group_name]:
            try:
                data = search_fn()
                group_results[source_name] = data
                totals[source_name] = len(data)
            except Exception as e:
                group_results[source_name] = [{"error": str(e)}]
                totals[source_name] = 0

        results[group_name] = group_results

    # Calculate grand total
    grand_total = sum(totals.values())

    return json.dumps({
        "status": "success",
        "query": query,
        "location": location,
        "sources_searched": active_groups,
        "totals_by_source": totals,
        "grand_total": grand_total,
        "results": results,
    }, indent=2)


@mcp.tool()
def deep_enrich_leads(
    urls: str,
    extract_contacts: bool = True,
) -> str:
    """Deep-enrich a list of lead URLs by scraping each page for contact info.

    Args:
        urls: Comma-separated list of URLs to enrich
        extract_contacts: Whether to extract emails and phones (default True)

    Returns:
        JSON with enriched data for each URL
    """
    url_list = [u.strip() for u in urls.split(",") if u.strip()]
    enriched = []

    for url in url_list[:10]:  # Limit to 10 URLs
        try:
            text = _scrape_page(url)
            entry = {"url": url, "text_preview": text[:500]}

            if extract_contacts:
                entry["emails"] = _extract_emails(text)
                entry["phones"] = _extract_phones(text)

            enriched.append(entry)
        except Exception as e:
            enriched.append({"url": url, "error": str(e)})

    return json.dumps({
        "status": "success",
        "urls_processed": len(enriched),
        "results": enriched,
    }, indent=2)


@mcp.tool()
def find_company_contacts(
    company_name: str,
    website: str = "",
    industry: str = "",
) -> str:
    """Find decision-maker contacts at a specific company.

    Searches multiple sources to find CEO, COO, Marketing Director, etc.

    Args:
        company_name: Company name to search
        website: Company website (optional, will scrape if provided)
        industry: Industry context (optional)

    Returns:
        JSON with contacts and company info found
    """
    # Search for people at this company
    queries = [
        f"CEO {company_name}",
        f"founder {company_name}",
        f"COO {company_name} contact",
        f"Marketing Director {company_name}",
        f"{company_name} leadership team",
    ]

    contacts = []
    for query in queries[:3]:
        results = _ddg_search(query, max_results=3)
        for r in results:
            title = r.get("title", "").lower()
            if any(role in title for role in ["ceo", "coo", "cto", "cfo", "founder", "owner", "director", "manager", "head"]):
                contacts.append({
                    "name": r.get("title", ""),
                    "role": next((r.upper() for r in ["CEO", "COO", "CTO", "CFO", "Founder", "Owner", "Director"] if r.lower() in title), "Unknown"),
                    "source": r.get("url", ""),
                    "snippet": r.get("snippet", ""),
                })

    # Scrape website if provided
    website_data = None
    if website:
        text = _scrape_page(website)
        website_data = {
            "emails": _extract_emails(text),
            "phones": _extract_phones(text),
            "text_preview": text[:500],
        }

    # Deduplicate contacts
    seen = set()
    unique_contacts = []
    for c in contacts:
        key = c["name"].lower()
        if key not in seen:
            seen.add(key)
            unique_contacts.append(c)

    return json.dumps({
        "company": company_name,
        "contacts_found": len(unique_contacts),
        "contacts": unique_contacts[:10],
        "website_data": website_data,
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
