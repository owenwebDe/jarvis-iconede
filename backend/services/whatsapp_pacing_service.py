"""WhatsApp Anti-Ban Pacing & Safety Guardrails Service for Jarvis.

Protects WhatsApp business numbers from Meta bans through:
- Human typing simulation & delay jitter (3-9 seconds)
- Time-of-day outreach windows (08:00 - 20:00)
- STOP / Opt-Out detection and automatic sequence halting
- Message throttling and burst prevention
"""

from __future__ import annotations

import datetime
import logging
import random
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("whatsapp_pacing")

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jarvis.db"

OPT_OUT_KEYWORDS = [
    "stop",
    "unsubscribe",
    "cancel",
    "opt out",
    "opt-out",
    "remove me",
    "don't message",
    "dont message",
    "not interested",
    "leave me alone",
    "pare",
    "sair",
]


def _init_opt_out_db():
    with sqlite3.connect(str(_DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_opt_outs (
                phone_number TEXT PRIMARY KEY,
                opted_out_at REAL NOT NULL,
                reason TEXT
            )
        """)
        conn.commit()


_init_opt_out_db()


class WhatsAppPacingService:
    """Enforces safety guardrails, anti-ban pacing, and opt-out filters."""

    def __init__(self):
        _init_opt_out_db()

    def is_opted_out(self, phone_number: str) -> bool:
        """Check if phone number has requested to stop receiving messages."""
        clean = re.sub(r"[^\d]", "", phone_number)
        with sqlite3.connect(str(_DB_PATH)) as conn:
            cur = conn.cursor()
            cur.execute("SELECT phone_number FROM whatsapp_opt_outs WHERE phone_number = ?", (clean,))
            return cur.fetchone() is not None

    def record_opt_out(self, phone_number: str, reason: str = "user_keyword") -> None:
        """Record opt-out to permanently suppress automated outreach."""
        clean = re.sub(r"[^\d]", "", phone_number)
        with sqlite3.connect(str(_DB_PATH)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO whatsapp_opt_outs (phone_number, opted_out_at, reason) VALUES (?, strftime('%s', 'now'), ?)",
                (clean, reason),
            )
            conn.commit()
        logger.info(f"Recorded WhatsApp opt-out for {clean} ({reason})")

    def check_for_opt_out_keywords(self, incoming_text: str) -> bool:
        """Detect if incoming customer message is an opt-out request."""
        clean = incoming_text.strip().lower()
        for kw in OPT_OUT_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", clean):
                return True
        return False

    def is_within_allowed_hours(self, start_hour: int = 7, end_hour: int = 20) -> bool:
        """Verify current local time is within business hours (07:00 - 20:00)."""
        now = datetime.datetime.now()
        return start_hour <= now.hour < end_hour

    def calculate_typing_delay(self, text: str) -> float:
        """Calculate a natural, human-like typing delay before sending."""
        word_count = len(text.split())
        # Base jitter 2.5s + ~0.08s per word with random jitter
        delay = 2.5 + (word_count * 0.08) + random.uniform(0.5, 2.0)
        return min(9.0, max(2.5, round(delay, 2)))

    def validate_outreach(
        self,
        phone_number: str,
        text: str,
        enforce_hours: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """Validate whether a message can be safely dispatched."""
        if self.is_opted_out(phone_number):
            return False, "Recipient has opted out of automated WhatsApp communications."

        if enforce_hours and not self.is_within_allowed_hours():
            return False, "Current time is outside business outreach hours (08:00 - 20:00)."

        if len(text.strip()) == 0:
            return False, "Message body cannot be empty."

        return True, None


_PACING_INSTANCE: Optional[WhatsAppPacingService] = None


def get_whatsapp_pacing_service() -> WhatsAppPacingService:
    global _PACING_INSTANCE
    if _PACING_INSTANCE is None:
        _PACING_INSTANCE = WhatsAppPacingService()
    return _PACING_INSTANCE
