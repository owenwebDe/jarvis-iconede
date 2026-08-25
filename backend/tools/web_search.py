"""Web search tool for autonomous agents.
Usage:
    python tools/web_search.py "query" [--max 5]
"""
import sys
import json
import argparse

def search(query: str, max_results: int = 5):
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, max_results=max_results))
        return results
    except Exception as e:
        return [{"error": str(e)}]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Search for Jarvis Agents")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--max", type=int, default=5, help="Max results")
    args = parser.parse_args()

    res = search(args.query, max_results=args.max)
    print(json.dumps(res, indent=2))
