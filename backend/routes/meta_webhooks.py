"""FastAPI routes for Meta Webhooks, Inbound Messenger DMs, and Social Engagement."""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel

from core.auth import verify_api_key
from services import meta_messenger

router = APIRouter(prefix="/api/meta", tags=["Meta Graph & Messenger"])


class PublishPostRequest(BaseModel):
    page_id: str
    message: str
    link_url: Optional[str] = None
    image_url: Optional[str] = None


class SimulateInboundRequest(BaseModel):
    sender_id: str
    message_text: str
    comment_id: Optional[str] = None
    commenter_name: Optional[str] = None


# ── Webhook Verification Handshake ───────────────────────────────────────────


@router.get("/webhook")
async def meta_webhook_verification(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """Handles the Meta Webhook Verification handshake."""
    challenge = meta_messenger.verify_webhook(
        mode=hub_mode,
        token=hub_verify_token,
        challenge=hub_challenge,
    )
    if challenge is not None:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Webhook verification failed")


# ── Webhook Inbound Ingestion ────────────────────────────────────────────────


@router.post("/webhook")
async def meta_webhook_events(request: Request):
    """Receives inbound webhook notifications from Meta (Messenger DMs, Feed Comments)."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    result = meta_messenger.process_webhook_payload(payload)
    return {"status": "EVENT_RECEIVED", "summary": result}


# ── Social Publishing & Simulations ──────────────────────────────────────────


@router.post("/posts")
async def publish_post(req: PublishPostRequest, _auth=Depends(verify_api_key)):
    """Publish a post to a Meta Facebook Page."""
    return meta_messenger.publish_page_post(
        page_id=req.page_id,
        message=req.message,
        link_url=req.link_url,
        image_url=req.image_url,
    )


@router.post("/simulate-inbound")
async def simulate_inbound_event(req: SimulateInboundRequest, _auth=Depends(verify_api_key)):
    """Simulation gateway for testing inbound DMs and post comments."""
    if req.comment_id:
        return meta_messenger.handle_post_comment(
            comment_id=req.comment_id,
            post_id="sample_post_123",
            commenter_id=req.sender_id,
            commenter_name=req.commenter_name or f"User {req.sender_id}",
            comment_text=req.message_text,
        )
    return meta_messenger.handle_inbound_dm(
        sender_id=req.sender_id,
        message_text=req.message_text,
    )
