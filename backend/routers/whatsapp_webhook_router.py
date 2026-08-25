"""WhatsApp Inbound Webhook Router for WAHA Integration.

Receives real-time incoming WhatsApp messages from WAHA daemon,
evaluates opt-outs & escalation triggers, invokes LLM brain,
and replies autonomously with anti-ban typing delay jitter.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Request
from services.waha_service import get_waha_service
from services.whatsapp_ai_agent import get_whatsapp_ai_agent
from services.whatsapp_handoff_service import get_whatsapp_handoff_service
from services.whatsapp_pacing_service import get_whatsapp_pacing_service

logger = logging.getLogger("whatsapp_webhook")

router = APIRouter(prefix="/api/v1/webhooks/whatsapp", tags=["whatsapp_webhook"])


async def _process_incoming_message(payload: Dict[str, Any]):
    """Background processor for incoming WhatsApp message."""
    event = payload.get("event")
    data = payload.get("payload", {})
    if not data or event not in ("message", "message.any", "message.upsert"):
        return

    # Ignore messages sent by ourselves
    if data.get("fromMe") is True:
        return

    body = data.get("body", "").strip()
    from_jid = data.get("from", "")
    phone_number = from_jid.split("@")[0] if "@" in from_jid else from_jid

    if not body or not phone_number:
        return

    logger.info(f"Incoming WhatsApp message from {phone_number}: '{body}'")

    pacing_service = get_whatsapp_pacing_service()
    handoff_service = get_whatsapp_handoff_service()
    ai_agent = get_whatsapp_ai_agent()
    waha_service = get_waha_service()

    # 1. Check for Opt-Out Keywords (STOP, UNSUBSCRIBE)
    if pacing_service.check_for_opt_out_keywords(body):
        pacing_service.record_opt_out(phone_number, reason=f"Texted: {body}")
        await asyncio.sleep(1.5)
        waha_service.send_message(
            phone_number=phone_number,
            text="You have been unsubscribed and will no longer receive automated messages from us. Reply START anytime to re-enable.",
        )
        return

    # 2. Check for Human Escalation Triggers
    is_escalation, reason = handoff_service.check_escalation_triggers(body)
    if is_escalation:
        alert = handoff_service.escalate_to_human(phone_number, reason, body)
        # Send gentle holding message
        await asyncio.sleep(2.0)
        waha_service.send_message(
            phone_number=phone_number,
            text="Thank you. I have connected our executive desk and notified Mr. Owen directly. An advisor will reach out to you shortly.",
        )
        return

    # 3. Generate Intelligent LLM Reply
    reply_data = await ai_agent.generate_ai_reply(
        phone_number=phone_number,
        incoming_message=body,
        contact_name=data.get("pushName", "Client"),
    )
    reply_text = reply_data.get("ai_reply") or reply_data.get("reply", "")
    if not reply_text:
        logger.warning(f"No reply generated for {phone_number}")
        return

    # 4. Apply Anti-Ban Typing Jitter Delay
    typing_delay = pacing_service.calculate_typing_delay(reply_text)
    logger.info(f"Simulating human typing jitter ({typing_delay}s) for {phone_number}")
    await asyncio.sleep(typing_delay)

    # 5. Dispatch Autonomous Reply via WAHA
    waha_service.send_message(phone_number=phone_number, text=reply_text)


@router.post("")
async def receive_waha_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive live webhook event from WAHA daemon."""
    try:
        payload = await request.json()
        background_tasks.add_task(_process_incoming_message, payload)
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Error parsing WAHA webhook: {e}")
        return {"status": "error", "message": str(e)}
