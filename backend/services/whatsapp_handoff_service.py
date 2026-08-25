"""AI to Human Handoff & Sentiment Escalation Service for Jarvis.

Monitors WhatsApp conversation sentiment and escalates leads to Mr. Owen
when complex negotiations, explicit human requests, or disputes arise.
"""

from __future__ import annotations

import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("whatsapp_handoff")

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jarvis.db"

ESCALATION_TRIGGERS = [
    r"speak to (a )?human",
    r"talk to (a )?person",
    r"speak with (the )?(owner|founder|ceo|director|manager|owen)",
    r"talk with (the )?(owner|founder|ceo|director|manager|owen)",
    r"custom contract",
    r"sign (an )?nda",
    r"lawyer|legal team|attorney",
    r"refund|chargeback|fraud|police",
    r"call me (now|immediately)",
    r"falar com (um )?humano",
    r"falar com o dono",
]


def _init_handoff_db():
    with sqlite3.connect(str(_DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                trigger_reason TEXT NOT NULL,
                last_message TEXT NOT NULL,
                status TEXT DEFAULT 'pending', -- 'pending', 'resolved', 'dismissed'
                created_at REAL NOT NULL
            )
        """)
        conn.commit()


_init_handoff_db()


class WhatsAppHandoffService:
    """Detects escalation criteria and manages human takeover transitions."""

    def __init__(self):
        _init_handoff_db()

    def check_escalation_triggers(self, incoming_text: str) -> Tuple[bool, Optional[str]]:
        """Check if message matches human escalation rules."""
        clean = incoming_text.lower().strip()
        for pattern in ESCALATION_TRIGGERS:
            if re.search(pattern, clean):
                return True, f"Matched trigger rule: '{pattern}'"
        return False, None

    def escalate_to_human(
        self,
        phone_number: str,
        reason: str,
        last_message: str,
    ) -> Dict[str, Any]:
        """Record escalation and generate alert payload for Mr. Owen."""
        with sqlite3.connect(str(_DB_PATH)) as conn:
            conn.execute(
                "INSERT INTO whatsapp_escalations (phone_number, trigger_reason, last_message, created_at) VALUES (?, ?, ?, ?)",
                (phone_number, reason, last_message, time.time()),
            )
            conn.commit()

        logger.info(f"Escalated WhatsApp chat {phone_number} to human ({reason})")
        return {
            "escalated": True,
            "phone_number": phone_number,
            "reason": reason,
            "alert_message": f"🚨 *WhatsApp Escalation Alert*\n\nProspect: {phone_number}\nReason: {reason}\nLast Text: \"{last_message}\"\nAction Required: Manual takeover requested.",
        }

    def get_pending_escalations(self) -> list[Dict[str, Any]]:
        """Retrieve all active escalations awaiting Mr. Owen's response."""
        with sqlite3.connect(str(_DB_PATH)) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, phone_number, trigger_reason, last_message, created_at FROM whatsapp_escalations WHERE status = 'pending' ORDER BY id DESC")
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "phone_number": r[1],
                    "reason": r[2],
                    "last_message": r[3],
                    "created_at": r[4],
                }
                for r in rows
            ]


_HANDOFF_INSTANCE: Optional[WhatsAppHandoffService] = None


def get_whatsapp_handoff_service() -> WhatsAppHandoffService:
    global _HANDOFF_INSTANCE
    if _HANDOFF_INSTANCE is None:
        _HANDOFF_INSTANCE = WhatsAppHandoffService()
    return _HANDOFF_INSTANCE
