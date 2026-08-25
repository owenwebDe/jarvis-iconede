"""Inbound Lead Ingestion Router for Client Websites.

Captures leads from forms on deployed client websites (e.g. Ordanic Homes,
Owen's Portfolio, Restaurant Demos), records them in the CRM pipeline,
and triggers warm initial WhatsApp outreach.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel
from services.waha_service import get_waha_service
from services.whatsapp_drip_service import get_whatsapp_drip_service
from services.whatsapp_pacing_service import get_whatsapp_pacing_service

logger = logging.getLogger("lead_ingestion")

router = APIRouter(prefix="/api/v1/webhooks/leads", tags=["lead_ingestion"])


class LeadPayload(BaseModel):
    name: str
    phone: str
    source: Optional[str] = "website_inquiry"
    interest: Optional[str] = "General Consultation"
    notes: Optional[str] = ""
    auto_contact: Optional[bool] = True


async def _process_new_lead(lead: LeadPayload):
    """Log lead and dispatch Touch 1 greeting via WhatsApp."""
    drip_service = get_whatsapp_drip_service()
    pacing_service = get_whatsapp_pacing_service()
    waha_service = get_waha_service()

    # 1. Record Lead
    drip_service.record_or_update_lead(
        phone_number=lead.phone,
        name=lead.name,
        source=lead.source or "website_inquiry",
        interest=lead.interest or "General Consultation",
        notes=lead.notes or "",
    )

    if not lead.auto_contact:
        return

    # 2. Check Pacing & Opt-Out
    can_send, reason = pacing_service.validate_outreach(lead.phone, "touch1", enforce_hours=False)
    if not can_send:
        logger.warning(f"Skipping auto-contact for {lead.phone}: {reason}")
        return

    # 3. Formulate Warm Welcome Message
    first_name = lead.name.split()[0] if lead.name else "there"
    welcome_text = (
        f"Hello {first_name}, thank you for reaching out regarding *{lead.interest}*.\n\n"
        f"I have received your parameters and will prepare the relevant details for you. "
        f"Would you prefer a brief call or should I send the overview directly here on WhatsApp?"
    )

    # 4. Anti-Ban Jitter Simulation
    delay = pacing_service.calculate_typing_delay(welcome_text)
    await asyncio.sleep(delay)

    # 5. Dispatch Message
    res = waha_service.send_message(phone_number=lead.phone, text=welcome_text)
    if res.get("status") == "success":
        drip_service.update_lead_stage(lead.phone, "CONTACTED")
        logger.info(f"Touch 1 outreach sent to {lead.phone}")


@router.post("")
async def capture_website_lead(lead: LeadPayload, background_tasks: BackgroundTasks):
    """Endpoint for landing pages and web apps to submit leads directly."""
    try:
        background_tasks.add_task(_process_new_lead, lead)
        return {
            "status": "success",
            "message": f"Lead '{lead.name}' successfully captured.",
        }
    except Exception as e:
        logger.error(f"Failed to ingest lead: {e}")
        return {"status": "error", "message": str(e)}
