"""IconEdge Meta Messenger & Graph API Engine.

Handles inbound Facebook/Instagram DMs, post comments, automated lead qualification,
instant conversational replies, comment-to-DM conversion, and Page publishing.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from core.database import (
    ProspectModel,
    get_db_session,
)
from services import shared_memory

logger = logging.getLogger("meta_messenger")

META_GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v21.0")
META_GRAPH_BASE_URL = f"https://graph.facebook.com/{META_GRAPH_VERSION}"
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "iconedge_meta_verify_token_2026")


def _get_page_access_token() -> str:
    """Retrieve Page Access Token from environment or secrets."""
    token = os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()
    if not token:
        token = os.getenv("META_ACCESS_TOKEN", "").strip()
    return token


# ── Webhook Handshake & Ingestion ────────────────────────────────────────────


def verify_webhook(mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Optional[str]:
    """Verify webhook subscription request from Meta Developer Dashboard."""
    if mode == "subscribe" and token == META_VERIFY_TOKEN:
        logger.info("[META_WEBHOOK] Verified subscription challenge successfully")
        return challenge
    logger.warning("[META_WEBHOOK] Verification failed. Expected token: %s, got: %s", META_VERIFY_TOKEN, token)
    return None


def process_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and dispatch inbound Meta webhook events (messages, post comments, delivery receipts)."""
    object_type = payload.get("object")
    entries = payload.get("entry", [])
    processed_events = []

    for entry in entries:
        page_id = entry.get("id")
        
        # 1. Messenger DMs
        for msg_event in entry.get("messaging", []):
            sender_id = msg_event.get("sender", {}).get("id")
            recipient_id = msg_event.get("recipient", {}).get("id")
            message = msg_event.get("message")
            if message and sender_id:
                text = message.get("text", "")
                result = handle_inbound_dm(
                    sender_id=sender_id,
                    message_text=text,
                    page_id=page_id,
                )
                processed_events.append({"type": "dm", "sender_id": sender_id, "result": result})

        # 2. Page Feed / Comments
        for change in entry.get("changes", []):
            field = change.get("field")
            value = change.get("value", {})
            if field == "feed" and value.get("item") == "comment" and value.get("verb") == "add":
                comment_id = value.get("comment_id")
                post_id = value.get("post_id")
                commenter_id = value.get("from", {}).get("id")
                commenter_name = value.get("from", {}).get("name", "Social Prospect")
                comment_text = value.get("message", "")
                result = handle_post_comment(
                    comment_id=comment_id,
                    post_id=post_id,
                    commenter_id=commenter_id,
                    commenter_name=commenter_name,
                    comment_text=comment_text,
                )
                processed_events.append({"type": "comment", "comment_id": comment_id, "result": result})

    return {"status": "success", "processed_events": processed_events, "count": len(processed_events)}


# ── Conversational Lead Qualification & DM Handling ──────────────────────────


def handle_inbound_dm(
    sender_id: str,
    message_text: str,
    page_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Process an inbound direct message, qualify lead intent, log to database, and draft reply."""
    logger.info("[META_DM] Received DM from %s: '%s'", sender_id, message_text)
    
    text_lower = message_text.lower()
    
    # Intent heuristics
    high_intent_keywords = ["price", "cost", "hire", "service", "start", "proposal", "audit", "scale", "quote"]
    is_high_intent = any(k in text_lower for k in high_intent_keywords)
    lead_score = 85 if is_high_intent else 60
    lead_status = "qualified" if is_high_intent else "new"

    # Save / update prospect record in SQLite shared memory
    db = get_db_session()
    try:
        prospect = db.query(ProspectModel).filter(ProspectModel.email == f"fb_{sender_id}@social.lead").first()
        if not prospect:
            prospect = db.query(ProspectModel).filter(ProspectModel.company_name == f"Meta Prospect {sender_id}").first()
        
        note_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Inbound DM: {message_text}"
        
        if prospect:
            prospect.notes = f"{prospect.notes or ''}\n{note_entry}".strip()
            if is_high_intent:
                prospect.lead_score = max(prospect.lead_score, lead_score)
                prospect.status = "qualified"
            prospect.updated_at = time.time()
        else:
            prospect = ProspectModel(
                company_name=f"Meta Prospect {sender_id}",
                contact_name=f"User {sender_id[:6]}",
                email=f"fb_{sender_id}@social.lead",
                source_agent="MetaMessengerAgent",
                status=lead_status,
                lead_score=lead_score,
                notes=note_entry,
                created_at=time.time(),
                updated_at=time.time(),
            )
            db.add(prospect)
        
        db.commit()
        db.refresh(prospect)
        prospect_id = prospect.id
    finally:
        db.close()

    # Generate smart conversational auto-reply
    if is_high_intent:
        auto_reply = (
            "Hi there! Thanks for reaching out to IconEdge Technologies. "
            "We'd love to help you scale. Would you like a complimentary audit of your current customer acquisition channels, "
            "or would you prefer to schedule a quick 15-min discovery call?"
        )
    else:
        auto_reply = (
            "Hello! Welcome to IconEdge Technologies. "
            "How can our growth systems help your business today? Feel free to tell us about your goals or ask any questions."
        )

    # Dispatch outbound message via Meta Send API if token available
    dispatch_result = send_messenger_message(recipient_id=sender_id, message_text=auto_reply)

    return {
        "sender_id": sender_id,
        "is_high_intent": is_high_intent,
        "lead_status": lead_status,
        "lead_score": lead_score,
        "prospect_id": prospect_id,
        "auto_reply_sent": auto_reply,
        "dispatch_status": dispatch_result.get("status", "dispatched"),
    }


def handle_post_comment(
    comment_id: str,
    post_id: str,
    commenter_id: str,
    commenter_name: str,
    comment_text: str,
) -> Dict[str, Any]:
    """Process a public comment on a page post, reply publicly, and initiate private DM."""
    logger.info("[META_COMMENT] New comment on post %s by %s: '%s'", post_id, commenter_name, comment_text)

    # Upsert prospect
    shared_memory.upsert_prospect(
        company_name=f"{commenter_name} (Social Lead)",
        contact_name=commenter_name,
        source_agent="MetaCommentAgent",
        status="new",
        lead_score=70,
        notes=f"Public comment on post {post_id}: '{comment_text}'",
    )

    public_reply = f"Thanks for checking this out @{commenter_name}! We just sent you a private message with the full details."
    private_dm = f"Hi {commenter_name}! Saw your comment on our post. Here is the direct breakdown of how IconEdge accelerates growth."

    reply_res = reply_to_comment(comment_id=comment_id, message_text=public_reply)
    dm_res = send_private_reply_to_comment(comment_id=comment_id, message_text=private_dm)

    return {
        "comment_id": comment_id,
        "commenter_name": commenter_name,
        "public_reply": public_reply,
        "private_dm": private_dm,
        "reply_status": reply_res.get("status", "sent"),
        "dm_status": dm_res.get("status", "sent"),
    }


# ── Meta Graph API Operations ────────────────────────────────────────────────


def send_messenger_message(recipient_id: str, message_text: str) -> Dict[str, Any]:
    """Send direct message via Meta Messenger Send API."""
    token = _get_page_access_token()
    if not token:
        return {
            "status": "simulation_sent",
            "recipient_id": recipient_id,
            "message": message_text,
            "timestamp": time.time(),
        }

    url = f"{META_GRAPH_BASE_URL}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "access_token": token,
    }
    try:
        resp = httpx.post(url, json=payload, timeout=15.0)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"Meta Send API error (HTTP {resp.status_code})", "details": resp.json()}
    except Exception as exc:
        return {"error": str(exc)}


def reply_to_comment(comment_id: str, message_text: str) -> Dict[str, Any]:
    """Reply publicly to a comment on a page post."""
    token = _get_page_access_token()
    if not token:
        return {"status": "simulation_comment_replied", "comment_id": comment_id, "reply": message_text}

    url = f"{META_GRAPH_BASE_URL}/{comment_id}/comments"
    payload = {"message": message_text, "access_token": token}
    try:
        resp = httpx.post(url, data=payload, timeout=15.0)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"Meta API error (HTTP {resp.status_code})", "details": resp.json()}
    except Exception as exc:
        return {"error": str(exc)}


def send_private_reply_to_comment(comment_id: str, message_text: str) -> Dict[str, Any]:
    """Send a private message to a commenter from a page post."""
    token = _get_page_access_token()
    if not token:
        return {"status": "simulation_private_dm_sent", "comment_id": comment_id, "dm": message_text}

    url = f"{META_GRAPH_BASE_URL}/me/messages"
    payload = {
        "recipient": {"comment_id": comment_id},
        "message": {"text": message_text},
        "access_token": token,
    }
    try:
        resp = httpx.post(url, json=payload, timeout=15.0)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"Meta Private Reply error (HTTP {resp.status_code})", "details": resp.json()}
    except Exception as exc:
        return {"error": str(exc)}


def publish_page_post(
    page_id: str,
    message: str,
    link_url: Optional[str] = None,
    image_url: Optional[str] = None,
    scheduled_publish_time: Optional[int] = None,
) -> Dict[str, Any]:
    """Publish or schedule a post on a Meta Facebook Page."""
    token = _get_page_access_token()
    if not token:
        return {
            "status": "simulation_post_created",
            "page_id": page_id,
            "post_id": f"{page_id}_post_{int(time.time())}",
            "message": message,
            "link": link_url,
            "scheduled": scheduled_publish_time is not None,
        }

    url = f"{META_GRAPH_BASE_URL}/{page_id}/feed"
    payload: Dict[str, Any] = {
        "message": message,
        "access_token": token,
    }
    if link_url:
        payload["link"] = link_url
    if scheduled_publish_time:
        payload["published"] = "false"
        payload["scheduled_publish_time"] = str(scheduled_publish_time)

    try:
        resp = httpx.post(url, data=payload, timeout=20.0)
        if resp.status_code in (200, 201):
            return resp.json()
        return {"error": f"Meta Graph API post error (HTTP {resp.status_code})", "details": resp.json()}
    except Exception as exc:
        return {"error": str(exc)}
