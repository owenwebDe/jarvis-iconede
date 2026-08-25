"""WAHA (WhatsApp HTTP API) Client Service for Jarvis.

Communicates with the headless WAHA daemon (devlikeapro/waha via Docker or VPS)
to provide 24/7 background session management, QR code pairing,
autonomous message sending, and media dispatch.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("waha_service")

_DEFAULT_WAHA_URL = os.environ.get("WAHA_BASE_URL", "http://127.0.0.1:3005")
_DEFAULT_API_KEY = os.environ.get("WAHA_API_KEY", "")


class WahaService:
    """Client for WAHA (WhatsApp HTTP API) session and messaging management."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or _DEFAULT_WAHA_URL).rstrip("/")
        self.api_key = api_key or _DEFAULT_API_KEY

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers

    def get_session_status(self, session_name: str = "default") -> Dict[str, Any]:
        """Check status of a WAHA WhatsApp session."""
        try:
            url = f"{self.base_url}/api/sessions/{urllib.parse.quote(session_name)}"
            req = urllib.request.Request(url, headers=self._headers())
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode("utf-8"))
                return {
                    "status": "online",
                    "session": session_name,
                    "state": data.get("status", "UNKNOWN"),
                    "me": data.get("me"),
                }
        except Exception as e:
            return {
                "status": "offline",
                "session": session_name,
                "state": "DISCONNECTED",
                "message": f"WAHA daemon not reachable at {self.base_url}. ({e})",
            }

    def start_session(self, session_name: str = "default") -> Dict[str, Any]:
        """Start or create a WhatsApp session and return QR code."""
        # 1. Try create
        try:
            url = f"{self.base_url}/api/sessions"
            payload = json.dumps({"name": session_name, "config": {}}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass  # Session might already exist

        # 2. Start
        try:
            url = f"{self.base_url}/api/sessions/{urllib.parse.quote(session_name)}/start"
            payload = json.dumps({}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")
            with urllib.request.urlopen(req, timeout=8) as res:
                data = json.loads(res.read().decode("utf-8"))
                return {
                    "status": "success",
                    "session": session_name,
                    "state": data.get("status"),
                    "qr": data.get("qr"),
                }
        except Exception as e:
            return {
                "status": "error",
                "session": session_name,
                "message": f"Failed to start WAHA session: {e}",
            }

    def get_qr_code(self, session_name: str = "default") -> Dict[str, Any]:
        """Retrieve live QR code string or image URL for pairing."""
        try:
            url = f"{self.base_url}/api/sessions/{urllib.parse.quote(session_name)}"
            req = urllib.request.Request(url, headers=self._headers())
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode("utf-8"))
                return {
                    "status": "success",
                    "session": session_name,
                    "qr": data.get("qr"),
                    "state": data.get("status"),
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def send_message(
        self,
        phone_number: str,
        text: str,
        session_name: str = "default",
    ) -> Dict[str, Any]:
        """Send background WhatsApp text message via WAHA."""
        clean_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
        chat_id = f"{clean_phone}@c.us"

        try:
            url = f"{self.base_url}/api/sendText"
            payload = json.dumps({
                "session": session_name,
                "chatId": chat_id,
                "text": text,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode("utf-8"))
                return {
                    "status": "success",
                    "channel": "waha_daemon",
                    "phone_number": phone_number,
                    "message_id": data.get("id"),
                    "message": f"Message sent autonomously to {phone_number}",
                }
        except Exception as e:
            logger.warning(f"WAHA sendText failed: {e}. Falling back to click-to-chat URL.")
            encoded = urllib.parse.quote(text)
            return {
                "status": "fallback_link",
                "channel": "click_to_chat",
                "phone_number": phone_number,
                "web_link": f"https://wa.me/{clean_phone}?text={encoded}",
                "desktop_protocol": f"whatsapp://send?phone={clean_phone}&text={encoded}",
                "message": f"WAHA daemon offline. Generated direct WhatsApp link for {phone_number}.",
            }

    def send_media(
        self,
        phone_number: str,
        file_url: str,
        caption: str = "",
        session_name: str = "default",
    ) -> Dict[str, Any]:
        """Send media (image, PDF brochure) via WAHA."""
        clean_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
        chat_id = f"{clean_phone}@c.us"

        try:
            url = f"{self.base_url}/api/sendImage"
            payload = json.dumps({
                "session": session_name,
                "chatId": chat_id,
                "file": {"url": file_url},
                "caption": caption,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")
            with urllib.request.urlopen(req, timeout=15) as res:
                data = json.loads(res.read().decode("utf-8"))
                return {
                    "status": "success",
                    "channel": "waha_daemon",
                    "phone_number": phone_number,
                    "message_id": data.get("id"),
                }
        except Exception as e:
            return {"status": "error", "message": f"WAHA sendMedia failed: {e}"}


_WAHA_INSTANCE: Optional[WahaService] = None


def get_waha_service() -> WahaService:
    global _WAHA_INSTANCE
    if _WAHA_INSTANCE is None:
        _WAHA_INSTANCE = WahaService()
    return _WAHA_INSTANCE
