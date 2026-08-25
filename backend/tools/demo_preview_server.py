"""Demo Preview MCP Server.

Live preview of generated demos before deployment.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("demo_preview")
mcp = FastMCP("DemoPreview")

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEMOS_DIR = _BACKEND_DIR / "data" / "demos"


@mcp.tool()
def preview_demo(demo_id: str) -> str:
    """Get preview URL for a generated demo.

    Args:
        demo_id: Demo ID to preview

    Returns:
        JSON with preview URL
    """
    demo_dir = _DEMOS_DIR / demo_id
    if not demo_dir.exists():
        return json.dumps({"status": "error", "message": "Demo not found"})

    # Check for index.html
    index_file = demo_dir / "index.html"
    if not index_file.exists():
        return json.dumps({"status": "error", "message": "Demo has no index.html"})

    # In production, this would serve the file via a local server
    # For now, return the file path
    return json.dumps({
        "status": "success",
        "demo_id": demo_id,
        "file_path": str(index_file),
        "preview_url": f"/preview/{demo_id}",
        "message": "Preview available. In production, this serves via local dev server.",
    })


@mcp.tool()
def list_demos() -> str:
    """List all generated demos.

    Returns:
        JSON with demo list
    """
    demos = []
    if _DEMOS_DIR.exists():
        for demo_dir in _DEMOS_DIR.iterdir():
            if demo_dir.is_dir():
                index_file = demo_dir / "index.html"
                if index_file.exists():
                    stat = index_file.stat()
                    demos.append({
                        "demo_id": demo_dir.name,
                        "created_at": stat.st_ctime,
                        "size_kb": round(stat.st_size / 1024, 1),
                        "has_preview": True,
                    })

    # Sort by creation time
    demos.sort(key=lambda x: x["created_at"], reverse=True)

    return json.dumps({
        "status": "success",
        "demos": demos,
        "total": len(demos),
    })


@mcp.tool()
def delete_demo(demo_id: str) -> str:
    """Delete a generated demo.

    Args:
        demo_id: Demo ID to delete

    Returns:
        JSON confirmation
    """
    demo_dir = _DEMOS_DIR / demo_id
    if not demo_dir.exists():
        return json.dumps({"status": "error", "message": "Demo not found"})

    import shutil
    shutil.rmtree(demo_dir)

    return json.dumps({
        "status": "deleted",
        "demo_id": demo_id,
    })


@mcp.tool()
def get_demo_info(demo_id: str) -> str:
    """Get detailed info about a demo.

    Args:
        demo_id: Demo ID

    Returns:
        JSON with demo info
    """
    demo_dir = _DEMOS_DIR / demo_id
    if not demo_dir.exists():
        return json.dumps({"status": "error", "message": "Demo not found"})

    # Read index.html to extract info
    index_file = demo_dir / "index.html"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        # Extract title
        import re
        title_match = re.search(r"<title>(.*?)</title>", content)
        title = title_match.group(1) if title_match else "Untitled"

        # Extract meta description
        desc_match = re.search(r'<meta name="description" content="(.*?)"', content)
        description = desc_match.group(1) if desc_match else ""

        # Count lines
        line_count = len(content.split("\n"))

        return json.dumps({
            "status": "success",
            "demo_id": demo_id,
            "title": title,
            "description": description,
            "line_count": line_count,
            "size_kb": round(index_file.stat().st_size / 1024, 1),
        })

    return json.dumps({"status": "error", "message": "No index.html found"})


if __name__ == "__main__":
    mcp.run()
