"""21st.dev MCP Integration & Local Component Vault Service for IconEdge Technology.

Connects to 21st.dev's official MCP endpoint (https://21st.dev/api/mcp) with caching:
• Searches 12,000+ design-engineered React/Tailwind/Motion components.
• Automatically caches downloaded source code into a durable local SQLite vault.
• Prioritizes local cache hits to preserve the daily 21st.dev free retrieval quota.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("twenty_first_vault")

_VAULT_DIR = Path(__file__).resolve().parent.parent / "data" / "component_vault"
_VAULT_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = _VAULT_DIR / "vault.db"
_COMPONENTS_DIR = _VAULT_DIR / "components"
_COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)


def _init_vault_db():
    """Initialize local SQLite database for the Component Vault."""
    with sqlite3.connect(str(_DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vaulted_components (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                category TEXT,
                author TEXT,
                description TEXT,
                tags TEXT,
                source_code TEXT NOT NULL,
                file_path TEXT,
                cached_at REAL NOT NULL
            )
        """)
        conn.commit()


_init_vault_db()


class TwentyFirstVaultService:
    """Manages 21st.dev MCP requests and local component vault caching."""

    MCP_URL = "https://21st.dev/api/mcp"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get(
            "TWENTY_FIRST_API_KEY",
            "21st_sk_3f57745744c69a371dd1a1c2b803c7896d88580166a17fc92cd69a969d31c242",
        )
        _init_vault_db()

    def _call_mcp(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a JSON-RPC request to 21st.dev MCP endpoint."""
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params or {},
        }
        req = urllib.request.Request(
            self.MCP_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Jarvis-IconEdge/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except Exception as e:
            logger.error(f"21st.dev MCP call failed ({method}): {e}")
            return {"error": str(e)}

    def get_usage(self) -> Dict[str, Any]:
        """Check 21st.dev account tier and remaining daily quota."""
        res = self._call_mcp("tools/call", {"name": "get_usage", "arguments": {}})
        result_data = res.get("result", {})
        structured = result_data.get("structuredContent", {})
        text_content = ""
        for c in result_data.get("content", []):
            if c.get("type") == "text":
                text_content += c.get("text", "") + "\n"

        return {
            "status": "success",
            "tier": structured.get("tier", "free"),
            "free_retrievals_remaining_today": structured.get("freeRetrievalsRemaining", 2),
            "free_retrievals_limit_per_day": structured.get("freeRetrievalsPerDay", 2),
            "summary": text_content.strip(),
        }

    def search_components(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search 21st.dev marketplace for components (Unlimited quota)."""
        local_matches = self._search_local_vault(query)

        mcp_res = self._call_mcp("tools/call", {
            "name": "search",
            "arguments": {"query": query}
        })
        remote_items = []
        if "result" in mcp_res:
            content = mcp_res["result"].get("content", [])
            for item in content:
                if item.get("type") == "text":
                    try:
                        parsed = json.loads(item.get("text", "{}"))
                        if isinstance(parsed, list):
                            remote_items.extend(parsed)
                        elif isinstance(parsed, dict):
                            remote_items.append(parsed)
                    except Exception:
                        remote_items.append({"raw_info": item.get("text")})

        return {
            "status": "success",
            "query": query,
            "local_vault_cached_count": len(local_matches),
            "local_cached_matches": local_matches,
            "remote_results": remote_items[:limit] if remote_items else mcp_res.get("result", {}),
        }

    def get_component_code(self, component_id_or_slug: Any) -> Dict[str, Any]:
        """Retrieve full source code. Checks local vault first to save quota!"""
        str_id = str(component_id_or_slug).strip()
        local = self._get_from_local_vault(str_id)
        if local:
            logger.info(f"Local Component Vault HIT for '{str_id}' (0 API quota used).")
            return {
                "status": "success",
                "source": "local_vault",
                "component_id": local["id"],
                "name": local["name"],
                "slug": local["slug"],
                "category": local["category"],
                "source_code": local["source_code"],
                "file_path": local["file_path"],
                "message": f"Retrieved '{local['name']}' from local vault without using daily API quota.",
            }

        # Format arguments for 21st.dev MCP get_component
        arg_val: Any = int(str_id) if str_id.isdigit() else str_id
        logger.info(f"Local vault miss for '{str_id}'. Fetching from 21st.dev...")
        res = self._call_mcp("tools/call", {
            "name": "get_component",
            "arguments": {"id": arg_val}
        })

        if "error" in res:
            return {"status": "error", "message": str(res["error"])}

        result_obj = res.get("result", {})
        raw_text = ""
        for block in result_obj.get("content", []):
            if block.get("type") == "text":
                raw_text += block.get("text", "")

        if not raw_text:
            return {"status": "error", "message": f"No content returned for '{str_id}'."}

        sanitized_slug = f"component_{str_id}".replace("/", "_").replace(":", "_")
        dest_file = _COMPONENTS_DIR / f"{sanitized_slug}.tsx"
        dest_file.write_text(raw_text, encoding="utf-8")

        self._save_to_local_vault(
            comp_id=str_id,
            name=f"21st.dev Component #{str_id}",
            slug=sanitized_slug,
            category="ui",
            author="21st.dev",
            description=f"Vaulted from 21st.dev catalog (ID: {str_id})",
            tags="react,tailwind,motion,header,hero",
            source_code=raw_text,
            file_path=str(dest_file),
        )

        return {
            "status": "success",
            "source": "21st_dev_download",
            "component_id": str_id,
            "source_code": raw_text,
            "vaulted_file": str(dest_file),
            "message": f"Successfully downloaded and vaulted '{str_id}' into local Component Vault.",
        }

    def list_vaulted_components(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all permanently cached components in the local vault."""
        with sqlite3.connect(str(_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, slug, category, author, description, file_path, cached_at FROM vaulted_components ORDER BY cached_at DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "slug": r[2],
                    "category": r[3],
                    "author": r[4],
                    "description": r[5],
                    "file_path": r[6],
                    "cached_at": r[7],
                }
                for r in rows
            ]

    def _get_from_local_vault(self, identifier: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(str(_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, slug, category, author, description, source_code, file_path FROM vaulted_components WHERE id = ? OR slug = ?",
                (identifier, identifier),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "slug": row[2],
                    "category": row[3],
                    "author": row[4],
                    "description": row[5],
                    "source_code": row[6],
                    "file_path": row[7],
                }
        return None

    def _search_local_vault(self, query: str) -> List[Dict[str, Any]]:
        q = f"%{query}%"
        with sqlite3.connect(str(_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, slug, category, description FROM vaulted_components WHERE name LIKE ? OR description LIKE ? OR tags LIKE ?",
                (q, q, q),
            )
            rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "slug": r[2], "category": r[3], "description": r[4]} for r in rows]

    def _save_to_local_vault(
        self,
        comp_id: str,
        name: str,
        slug: str,
        category: str,
        author: str,
        description: str,
        tags: str,
        source_code: str,
        file_path: str,
    ) -> None:
        with sqlite3.connect(str(_DB_PATH)) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO vaulted_components
                (id, name, slug, category, author, description, tags, source_code, file_path, cached_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (comp_id, name, slug, category, author, description, tags, source_code, file_path, time.time()),
            )
            conn.commit()


_twenty_first_vault: Optional[TwentyFirstVaultService] = None


def get_twenty_first_vault() -> TwentyFirstVaultService:
    global _twenty_first_vault
    if _twenty_first_vault is None:
        _twenty_first_vault = TwentyFirstVaultService()
    return _twenty_first_vault
