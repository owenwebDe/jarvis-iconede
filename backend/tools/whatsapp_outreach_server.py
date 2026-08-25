"""WhatsApp Outreach & Autonomous WAHA Daemon FastMCP Server.

Enables WhatsAppAgent, OutreachAgent, and Jarvis to:
- Connect to 24/7 WAHA WhatsApp Daemon & scan live QR codes
- Dispatch autonomous WhatsApp messages with anti-ban pacing & typing jitter
- Capture website leads and schedule multi-touch follow-up sequences
- Monitor CRM lead pipeline stages and pending human escalations
- Generate click-to-chat links & Windows Desktop protocol URLs
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import urllib.parse
from pathlib import Path
from mcp.server.fastmcp import FastMCP

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from services.waha_service import get_waha_service
from services.whatsapp_pacing_service import get_whatsapp_pacing_service
from services.whatsapp_handoff_service import get_whatsapp_handoff_service
from services.whatsapp_drip_service import get_whatsapp_drip_service
from services.whatsapp_ai_agent import get_whatsapp_ai_agent

logger = logging.getLogger("whatsapp_outreach")
mcp = FastMCP("WhatsAppOutreach")


def _sanitize_phone(phone: str) -> str:
    """Format phone number into international standard without symbols."""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("0") and len(digits) == 11:
        digits = "234" + digits[1:]
    return digits


@mcp.tool()
def whatsapp_get_waha_status(session_name: str = "default") -> str:
    """Check connection status of the WAHA 24/7 WhatsApp background daemon.

    Args:
        session_name: Name of the session to check (default: 'default').
    """
    waha = get_waha_service()
    status = waha.get_session_status(session_name=session_name)
    return json.dumps(status, indent=2)


@mcp.tool()
def whatsapp_start_waha_session(session_name: str = "default") -> str:
    """Initialize or start a WAHA WhatsApp session and return QR code for pairing.

    Args:
        session_name: Name of the session (default: 'default').
    """
    waha = get_waha_service()
    res = waha.start_session(session_name=session_name)
    return json.dumps(res, indent=2)


@mcp.tool()
def whatsapp_get_waha_qr(session_name: str = "default") -> str:
    """Retrieve active pairing QR code for scanning in WhatsApp Mobile app.

    Args:
        session_name: Name of the session.
    """
    waha = get_waha_service()
    res = waha.get_qr_code(session_name=session_name)
    return json.dumps(res, indent=2)


@mcp.tool()
def whatsapp_send_autonomous_message(
    phone_number: str,
    message: str,
    session_name: str = "default",
    enforce_pacing: bool = True,
) -> str:
    """Send an autonomous WhatsApp message via WAHA daemon with anti-ban validation.

    Args:
        phone_number: Recipient's phone number.
        message: Message text to dispatch.
        session_name: Active WAHA session name.
        enforce_pacing: Apply anti-ban hours and opt-out checks.
    """
    clean_phone = _sanitize_phone(phone_number)
    pacing = get_whatsapp_pacing_service()

    if enforce_pacing:
        valid, reason = pacing.validate_outreach(clean_phone, message)
        if not valid:
            return json.dumps({
                "status": "blocked_by_guardrails",
                "phone_number": clean_phone,
                "reason": reason,
            }, indent=2)

    waha = get_waha_service()
    res = waha.send_message(phone_number=clean_phone, text=message, session_name=session_name)
    return json.dumps(res, indent=2)


@mcp.tool()
def whatsapp_get_lead_pipeline(limit: int = 50) -> str:
    """Retrieve active CRM leads organized by pipeline stage (NEW, CONTACTED, QUALIFIED, WON, etc.).

    Args:
        limit: Max number of leads to fetch.
    """
    drip = get_whatsapp_drip_service()
    leads = drip.get_pipeline(limit=limit)
    return json.dumps({
        "status": "success",
        "total_leads": len(leads),
        "pipeline": leads,
    }, indent=2)


@mcp.tool()
def whatsapp_get_pending_escalations() -> str:
    """Retrieve all WhatsApp conversations requiring human takeover from Mr. Owen."""
    handoff = get_whatsapp_handoff_service()
    escalations = handoff.get_pending_escalations()
    return json.dumps({
        "status": "success",
        "pending_count": len(escalations),
        "escalations": escalations,
    }, indent=2)


@mcp.tool()
def whatsapp_record_opt_out(phone_number: str, reason: str = "manual_request") -> str:
    """Record an opt-out to immediately halt all automated messaging for a number.

    Args:
        phone_number: Recipient's phone number.
        reason: Reason for opting out.
    """
    clean_phone = _sanitize_phone(phone_number)
    pacing = get_whatsapp_pacing_service()
    pacing.record_opt_out(clean_phone, reason=reason)
    return json.dumps({
        "status": "success",
        "message": f"Successfully opted out {clean_phone}.",
    }, indent=2)


@mcp.tool()
def whatsapp_generate_chat_link(phone_number: str, message: str) -> str:
    """Generate a direct WhatsApp click-to-chat web/mobile link.

    Args:
        phone_number: Target phone number (e.g. '08012345678' or '+2348012345678').
        message: Pre-filled message text.
    """
    clean_phone = _sanitize_phone(phone_number)
    encoded_msg = urllib.parse.quote(message)
    link = f"https://wa.me/{clean_phone}?text={encoded_msg}"
    return json.dumps({
        "status": "success",
        "phone_number": clean_phone,
        "wa_link": link,
        "desktop_protocol": f"whatsapp://send?phone={clean_phone}&text={encoded_msg}",
    }, indent=2)


@mcp.tool()
def whatsapp_open_chat(
    phone_number: str,
    message: str,
    user_confirmation: bool = False,
) -> str:
    """Open WhatsApp Desktop on Windows with the client's number and pre-filled pitch.

    Args:
        phone_number: Target phone number.
        message: Pitch message text to pre-fill.
        user_confirmation: Set to True after obtaining user consent.
    """
    if not user_confirmation:
        return json.dumps({
            "status": "permission_denied",
            "message": f"Opening WhatsApp chat for {phone_number} requires user confirmation. Set user_confirmation=True after asking the user.",
        })

    clean_phone = _sanitize_phone(phone_number)
    encoded_msg = urllib.parse.quote(message)
    uri = f"whatsapp://send?phone={clean_phone}&text={encoded_msg}"

    try:
        cmd = ["powershell", "-NoProfile", "-Command", f"Start-Process '{uri}'"]
        subprocess.Popen(cmd, shell=True)
        return json.dumps({
            "status": "success",
            "phone_number": clean_phone,
            "message": f"Opened WhatsApp chat window for {clean_phone}.",
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to open WhatsApp: {e}"})


@mcp.tool()
def whatsapp_create_custom_pitch(
    business_name: str,
    business_category: str,
    contact_name: str = "Manager",
    offer_type: str = "website_audit",
) -> str:
    """Generate a high-converting localized pitch template for an Abuja business."""
    if business_category.lower() == "restaurant":
        pitch = (
            f"Hello {contact_name}, hope your week is off to a great start! 🍲\n\n"
            f"I came across {business_name} here in Abuja and love your menu. "
            f"We noticed you're handling most orders over WhatsApp/IG DM.\n\n"
            f"At IconEdge Technology, we recently built an online ordering & table reservation system for 'Dine Abuja' "
            f"that reduced order wait times by 40% and boosted takeout sales.\n\n"
            f"We'd love to build a quick, modern mobile menu for {business_name} with instant Paystack/WhatsApp checkout. "
            f"Can I send over a quick 2-minute mockup demo?"
        )
    elif business_category.lower() == "fashion":
        pitch = (
            f"Hi {contact_name}, greetings from IconEdge Technology in Abuja! ✨\n\n"
            f"We love the collection at {business_name}. "
            f"We help Abuja fashion brands convert their Instagram traffic into automated sales with custom mobile catalogs "
            f"(like our recent project with Abuja Fashion Hub which increased online orders by 150%).\n\n"
            f"Would you be open to seeing a quick preview of how a seamless store would look for {business_name}?"
        )
    else:
        pitch = (
            f"Hello {contact_name}, greetings from IconEdge Technology! 🚀\n\n"
            f"We specialize in building high-speed, modern web and mobile applications for leading businesses in Abuja.\n\n"
            f"We'd love to help {business_name} establish a dominant online presence that drives direct customer inquiries and sales.\n\n"
            f"Are you available for a brief 5-minute chat this afternoon?"
        )

    return json.dumps({
        "business_name": business_name,
        "business_category": business_category,
        "pitch_message": pitch,
    }, indent=2)


@mcp.tool()
async def whatsapp_generate_ai_reply(
    phone_number: str,
    incoming_message: str,
    contact_name: str = "Client",
) -> str:
    """Generate an intelligent, contextual AI response to an incoming WhatsApp customer message."""
    agent = get_whatsapp_ai_agent()
    res = await agent.generate_ai_reply(
        phone_number=phone_number,
        incoming_message=incoming_message,
        contact_name=contact_name,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def whatsapp_get_chat_history(phone_number: str, limit: int = 10) -> str:
    """Retrieve full conversation history with a WhatsApp prospect."""
    agent = get_whatsapp_ai_agent()
    history = agent.get_conversation_history(phone_number=phone_number, limit=limit)
    return json.dumps({
        "phone_number": phone_number,
        "count": len(history),
        "messages": history,
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
