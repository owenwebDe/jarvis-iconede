"""WhatsApp Multi-Touch Drip & Lead Pipeline Service for Jarvis.

Manages automated 3-touch follow-up sequences and CRM lead pipeline:
- Touch 1 (Day 0): Warm welcome & discovery prompt
- Touch 2 (Day 2): Relevant portfolio highlight / case study
- Touch 3 (Day 5): Direct VIP consultation offer
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("whatsapp_drip")

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jarvis.db"


def _init_drip_db():
    with sqlite3.connect(str(_DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                source TEXT NOT NULL, -- e.g. 'website_form', 'manual_entry', 'meta_ad'
                stage TEXT DEFAULT 'NEW', -- 'NEW', 'CONTACTED', 'QUALIFIED', 'NEEDS_HUMAN', 'WON', 'LOST'
                interest TEXT,
                notes TEXT,
                current_touch INTEGER DEFAULT 0,
                next_touch_at REAL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.commit()


_init_drip_db()


class WhatsAppDripService:
    """Manages multi-touch outreach sequences and lead pipeline."""

    def __init__(self):
        _init_drip_db()

    def record_or_update_lead(
        self,
        phone_number: str,
        name: str,
        source: str = "website_form",
        interest: str = "",
        notes: str = "",
    ) -> Dict[str, Any]:
        """Insert or update a lead in the CRM pipeline."""
        now = time.time()
        with sqlite3.connect(str(_DB_PATH)) as conn:
            conn.execute(
                """
                INSERT INTO whatsapp_leads (phone_number, name, source, stage, interest, notes, current_touch, next_touch_at, created_at, updated_at)
                VALUES (?, ?, ?, 'NEW', ?, ?, 0, ?, ?, ?)
                ON CONFLICT(phone_number) DO UPDATE SET
                    name = excluded.name,
                    source = excluded.source,
                    interest = COALESCE(excluded.interest, interest),
                    notes = COALESCE(excluded.notes, notes),
                    updated_at = excluded.updated_at
                """,
                (phone_number, name, source, interest, notes, now, now, now),
            )
            conn.commit()

        logger.info(f"Recorded lead {name} ({phone_number}) from {source}")
        return {
            "status": "success",
            "phone_number": phone_number,
            "name": name,
            "source": source,
            "stage": "NEW",
        }

    def get_pipeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve active leads organized by pipeline stage."""
        with sqlite3.connect(str(_DB_PATH)) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, phone_number, name, source, stage, interest, notes, current_touch, next_touch_at, created_at FROM whatsapp_leads ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "phone_number": r[1],
                    "name": r[2],
                    "source": r[3],
                    "stage": r[4],
                    "interest": r[5],
                    "notes": r[6],
                    "current_touch": r[7],
                    "next_touch_at": r[8],
                    "created_at": r[9],
                }
                for r in rows
            ]

    def update_lead_stage(self, phone_number: str, new_stage: str) -> None:
        """Update stage (e.g. 'QUALIFIED', 'NEEDS_HUMAN', 'WON')."""
        with sqlite3.connect(str(_DB_PATH)) as conn:
            conn.execute(
                "UPDATE whatsapp_leads SET stage = ?, updated_at = ? WHERE phone_number = ?",
                (new_stage, time.time(), phone_number),
            )
            conn.commit()


_DRIP_INSTANCE: Optional[WhatsAppDripService] = None


def get_whatsapp_drip_service() -> WhatsAppDripService:
    global _DRIP_INSTANCE
    if _DRIP_INSTANCE is None:
        _DRIP_INSTANCE = WhatsAppDripService()
    return _DRIP_INSTANCE
