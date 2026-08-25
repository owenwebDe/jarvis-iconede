"""Intelligent AI WhatsApp Agent Service for IconEdge Technology.

Provides dynamic, LLM-powered conversational intelligence for WhatsApp messaging.
Unlike hardcoded bot responses, this agent understands context, handles objections,
presents case studies, estimates project scopes, and closes discovery calls.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("whatsapp_ai_agent")

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jarvis.db"
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _init_db():
    """Ensure whatsapp conversation history table exists."""
    with sqlite3.connect(str(_DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                sender TEXT NOT NULL, -- 'customer' or 'agent'
                message TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)
        conn.commit()


_init_db()


def _get_openrouter_api_key() -> str:
    """Retrieve active OpenRouter API key from env or secrets file."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key and not key.startswith("BOOTSTRAP"):
        return key

    secrets_file = Path(__file__).resolve().parent.parent / "fastagent.secrets.yaml"
    if secrets_file.exists():
        import yaml
        try:
            data = yaml.safe_load(secrets_file.read_text(encoding="utf-8")) or {}
            key = data.get("openrouter", {}).get("api_key", "")
            if key and not key.startswith("BOOTSTRAP"):
                return key
        except Exception:
            pass
    return ""


class WhatsAppAIAgent:
    """Dynamic LLM-powered WhatsApp representative for IconEdge Technology."""

    SYSTEM_PROMPT = """\
You are the Executive WhatsApp AI Representative for IconEdge Technology, a leading software & mobile app development firm based in Abuja, Nigeria.

YOUR GOAL:
Engage prospects warmly, answer questions intelligently, address concerns, explain our development capabilities, and guide them toward scheduling a discovery call or receiving a tailored proposal.

KEY KNOWLEDGE BASE:
• Company: IconEdge Technology (Abuja, Nigeria).
• Services: Custom web applications, e-commerce stores, mobile apps (iOS & Android), business automation systems, restaurant ordering apps, inventory/booking systems, payment integration (Paystack/Flutterwave).
• Typical Turnaround: Fast 3 to 14-day turnaround for SMB websites and web apps.
• Local Proof Points / Case Studies:
  - Abuja Fashion Hub: Built an online catalog & automated checkout (+150% order increase).
  - Dine Abuja: Built a QR table ordering & takeout system (-40% wait times).
  - Fit Nigeria: Custom membership & class booking portal (+50% new member sign-ups).
• Tone: Professional, warm, confident, consultative, Nigerian-business friendly. Keep messages punchy and easy to read on WhatsApp (use bullet points and emojis tastefully).

RULES:
1. NEVER give robotic or hardcoded replies. Always address the user's specific question directly with genuine expertise.
2. If they ask about pricing, give a friendly estimate range based on scope and propose a quick 5-minute WhatsApp call or demo to give an exact quote.
3. Keep responses under 120 words so they read naturally like a real human executive on WhatsApp.
"""

    def __init__(self):
        _init_db()

    def get_conversation_history(self, phone_number: str, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieve recent conversation history with a specific contact."""
        with sqlite3.connect(str(_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sender, message FROM whatsapp_conversations WHERE phone_number = ? ORDER BY id DESC LIMIT ?",
                (phone_number, limit),
            )
            rows = cursor.fetchall()
            return [{"role": "user" if r[0] == "customer" else "assistant", "content": r[1]} for r in reversed(rows)]

    def record_message(self, phone_number: str, sender: str, message: str) -> None:
        """Store incoming or outgoing message in durable SQLite memory."""
        with sqlite3.connect(str(_DB_PATH)) as conn:
            conn.execute(
                "INSERT INTO whatsapp_conversations (phone_number, sender, message, timestamp) VALUES (?, ?, ?, ?)",
                (phone_number, sender, message, time.time()),
            )
            conn.commit()

    async def generate_ai_reply(
        self,
        phone_number: str,
        incoming_message: str,
        contact_name: str = "Client",
    ) -> Dict[str, Any]:
        """Generate a dynamic, intelligent LLM response for an incoming WhatsApp message."""
        # 1. Record incoming customer message
        self.record_message(phone_number, "customer", incoming_message)

        # 2. Fetch history
        history = self.get_conversation_history(phone_number, limit=6)

        try:
            from services.llm_router import get_router
            router = get_router()

            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})

            res = await router.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=300,
            )

            reply_content = res.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not reply_content:
                raise ValueError("Empty response from LLM router")

            # Record outgoing AI reply
            self.record_message(phone_number, "agent", reply_content)

            return {
                "status": "success",
                "phone_number": phone_number,
                "incoming_message": incoming_message,
                "ai_reply": reply_content,
                "reply": reply_content,
            }
        except Exception as e:
            logger.warning(f"LLM generation failed, using intelligent fallback: {e}")
            fallback = (
                f"Hi {contact_name}! 👋 Thanks for reaching out to IconEdge Technology in Abuja. "
                "We build high-performance web & mobile apps tailored for local businesses with fast turnaround. "
                "Could you tell me a little more about what you're looking to create so I can share relevant demos and an estimate?"
            )
            self.record_message(phone_number, "agent", fallback)
            return {
                "status": "fallback",
                "phone_number": phone_number,
                "incoming_message": incoming_message,
                "ai_reply": fallback,
                "reply": fallback,
                "error": str(e),
            }


_whatsapp_ai_agent: Optional[WhatsAppAIAgent] = None


def get_whatsapp_ai_agent() -> WhatsAppAIAgent:
    global _whatsapp_ai_agent
    if _whatsapp_ai_agent is None:
        _whatsapp_ai_agent = WhatsAppAIAgent()
    return _whatsapp_ai_agent
