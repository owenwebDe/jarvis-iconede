"""IconEdge Shared Memory Service.

Centralized persistence layer for all specialist agents (Lead Research, Creative,
Ads, Outreach, and Jarvis Orchestrator). Operates directly over SQLite (`jarvis.db`)
to ensure durability across model switches and system restarts.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

from core.database import (
    AdCampaignModel,
    AdCreativeModel,
    BoardMeetingModel,
    BoardMeetingTranscriptModel,
    ProspectModel,
    get_db_session,
)

logger = logging.getLogger("shared_memory")


# ── Prospects & Leads Operations ─────────────────────────────────────────────


def upsert_prospect(
    company_name: str,
    contact_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    website: Optional[str] = None,
    country: str = "Global",
    city: Optional[str] = None,
    industry: Optional[str] = None,
    source_agent: str = "LeadResearchAgent",
    status: str = "new",
    lead_score: int = 50,
    notes: Optional[str] = None,
    custom_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Insert or update a prospect in shared memory."""
    db = get_db_session()
    try:
        # Search by email or company_name
        prospect = None
        if email:
            prospect = db.query(ProspectModel).filter(ProspectModel.email == email).first()
        if not prospect:
            prospect = db.query(ProspectModel).filter(ProspectModel.company_name == company_name).first()

        custom_json = json.dumps(custom_data) if custom_data else None

        if prospect:
            prospect.company_name = company_name
            if contact_name:
                prospect.contact_name = contact_name
            if email:
                prospect.email = email
            if phone:
                prospect.phone = phone
            if website:
                prospect.website = website
            if country:
                prospect.country = country
            if city:
                prospect.city = city
            if industry:
                prospect.industry = industry
            prospect.source_agent = source_agent
            prospect.status = status
            prospect.lead_score = lead_score
            if notes:
                prospect.notes = f"{prospect.notes or ''}\n{notes}".strip()
            if custom_json:
                prospect.custom_data_json = custom_json
            prospect.updated_at = time.time()
        else:
            prospect = ProspectModel(
                company_name=company_name,
                contact_name=contact_name,
                email=email,
                phone=phone,
                website=website,
                country=country,
                city=city,
                industry=industry,
                source_agent=source_agent,
                status=status,
                lead_score=lead_score,
                notes=notes,
                custom_data_json=custom_json,
                created_at=time.time(),
                updated_at=time.time(),
            )
            db.add(prospect)

        db.commit()
        db.refresh(prospect)
        logger.info("[SHARED_MEMORY] Upserted prospect: %s (id=%d)", prospect.company_name, prospect.id)
        return {
            "id": prospect.id,
            "company_name": prospect.company_name,
            "contact_name": prospect.contact_name,
            "email": prospect.email,
            "phone": prospect.phone,
            "website": prospect.website,
            "country": prospect.country,
            "city": prospect.city,
            "industry": prospect.industry,
            "status": prospect.status,
            "lead_score": prospect.lead_score,
            "notes": prospect.notes,
        }
    finally:
        db.close()


def search_prospects(
    query: Optional[str] = None,
    status: Optional[str] = None,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Search and filter prospects in shared memory."""
    db = get_db_session()
    try:
        q = db.query(ProspectModel)
        if status:
            q = q.filter(ProspectModel.status == status)
        if country and country.lower() != "all":
            q = q.filter(ProspectModel.country.ilike(f"%{country}%"))
        if industry:
            q = q.filter(ProspectModel.industry.ilike(f"%{industry}%"))
        if query:
            pattern = f"%{query}%"
            q = q.filter(
                (ProspectModel.company_name.ilike(pattern))
                | (ProspectModel.contact_name.ilike(pattern))
                | (ProspectModel.notes.ilike(pattern))
                | (ProspectModel.email.ilike(pattern))
            )
        prospects = q.order_by(ProspectModel.lead_score.desc(), ProspectModel.updated_at.desc()).limit(limit).all()
        return [
            {
                "id": p.id,
                "company_name": p.company_name,
                "contact_name": p.contact_name,
                "email": p.email,
                "phone": p.phone,
                "website": p.website,
                "country": p.country,
                "city": p.city,
                "industry": p.industry,
                "status": p.status,
                "lead_score": p.lead_score,
                "notes": p.notes,
            }
            for p in prospects
        ]
    finally:
        db.close()


def clear_all_prospects() -> int:
    """Clear all prospects/leads from shared memory upon Mr. Owen's command."""
    db = get_db_session()
    try:
        deleted = db.query(ProspectModel).delete()
        db.commit()
        logger.info("[SHARED_MEMORY] Cleared %d prospects from memory", deleted)
        return deleted
    finally:
        db.close()


def delete_prospect(prospect_id: int) -> bool:
    """Delete a specific prospect from shared memory by ID."""
    db = get_db_session()
    try:
        prospect = db.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
        if prospect:
            db.delete(prospect)
            db.commit()
            return True
        return False
    finally:
        db.close()


# ── Ad Creatives Operations ──────────────────────────────────────────────────


def upsert_ad_creative(
    title: str,
    headline: str,
    body_copy: str,
    call_to_action: str = "Learn More",
    hook_type: str = "direct_offer",
    target_audience: Optional[str] = None,
    image_prompt: Optional[str] = None,
    image_url: Optional[str] = None,
    status: str = "draft",
    variations: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Store an ad creative generated by Creative Agent."""
    db = get_db_session()
    try:
        creative = AdCreativeModel(
            title=title,
            headline=headline,
            body_copy=body_copy,
            call_to_action=call_to_action,
            hook_type=hook_type,
            target_audience=target_audience,
            image_prompt=image_prompt,
            image_url=image_url,
            status=status,
            variations_json=json.dumps(variations) if variations else None,
            created_at=time.time(),
            updated_at=time.time(),
        )
        db.add(creative)
        db.commit()
        db.refresh(creative)
        logger.info("[SHARED_MEMORY] Stored ad creative: %s (id=%d)", creative.title, creative.id)
        return {
            "id": creative.id,
            "title": creative.title,
            "headline": creative.headline,
            "body_copy": creative.body_copy,
            "call_to_action": creative.call_to_action,
            "hook_type": creative.hook_type,
            "target_audience": creative.target_audience,
            "image_prompt": creative.image_prompt,
            "status": creative.status,
        }
    finally:
        db.close()


def list_ad_creatives(
    status: Optional[str] = None,
    target_audience: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """List ad creatives stored in shared memory."""
    db = get_db_session()
    try:
        q = db.query(AdCreativeModel)
        if status:
            q = q.filter(AdCreativeModel.status == status)
        if target_audience:
            q = q.filter(AdCreativeModel.target_audience.ilike(f"%{target_audience}%"))
        creatives = q.order_by(AdCreativeModel.created_at.desc()).limit(limit).all()
        return [
            {
                "id": c.id,
                "title": c.title,
                "headline": c.headline,
                "body_copy": c.body_copy,
                "call_to_action": c.call_to_action,
                "hook_type": c.hook_type,
                "target_audience": c.target_audience,
                "image_prompt": c.image_prompt,
                "status": c.status,
                "variations": json.loads(c.variations_json) if c.variations_json else [],
            }
            for c in creatives
        ]
    finally:
        db.close()


# ── Ad Campaigns Operations ──────────────────────────────────────────────────


def create_or_update_campaign(
    name: str,
    objective: str = "OUTCOME_LEADS",
    status: str = "PAUSED",
    daily_budget: float = 0.0,
    targeting: Optional[Dict[str, Any]] = None,
    creative_ids: Optional[List[int]] = None,
    meta_campaign_id: Optional[str] = None,
    insights: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Store or update a Meta ad campaign draft or active campaign."""
    db = get_db_session()
    try:
        campaign = db.query(AdCampaignModel).filter(AdCampaignModel.name == name).first()
        if not campaign and meta_campaign_id:
            campaign = db.query(AdCampaignModel).filter(AdCampaignModel.meta_campaign_id == meta_campaign_id).first()

        targeting_str = json.dumps(targeting) if targeting else None
        creatives_str = json.dumps(creative_ids) if creative_ids else None
        insights_str = json.dumps(insights) if insights else None

        if campaign:
            campaign.objective = objective
            campaign.status = status
            campaign.daily_budget = daily_budget
            if meta_campaign_id:
                campaign.meta_campaign_id = meta_campaign_id
            if targeting_str:
                campaign.targeting_json = targeting_str
            if creatives_str:
                campaign.creative_ids_json = creatives_str
            if insights_str:
                campaign.insights_json = insights_str
            campaign.updated_at = time.time()
        else:
            campaign = AdCampaignModel(
                name=name,
                objective=objective,
                status=status,
                daily_budget=daily_budget,
                meta_campaign_id=meta_campaign_id,
                targeting_json=targeting_str,
                creative_ids_json=creatives_str,
                insights_json=insights_str,
                created_at=time.time(),
                updated_at=time.time(),
            )
            db.add(campaign)

        db.commit()
        db.refresh(campaign)
        logger.info("[SHARED_MEMORY] Saved campaign: %s (status=%s)", campaign.name, campaign.status)
        return {
            "id": campaign.id,
            "name": campaign.name,
            "objective": campaign.objective,
            "status": campaign.status,
            "daily_budget": campaign.daily_budget,
            "meta_campaign_id": campaign.meta_campaign_id,
        }
    finally:
        db.close()


def list_campaigns(status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """List all campaigns in shared memory."""
    db = get_db_session()
    try:
        q = db.query(AdCampaignModel)
        if status:
            q = q.filter(AdCampaignModel.status == status)
        campaigns = q.order_by(AdCampaignModel.created_at.desc()).limit(limit).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "objective": c.objective,
                "status": c.status,
                "daily_budget": c.daily_budget,
                "meta_campaign_id": c.meta_campaign_id,
                "targeting": json.loads(c.targeting_json) if c.targeting_json else {},
                "creative_ids": json.loads(c.creative_ids_json) if c.creative_ids_json else [],
                "insights": json.loads(c.insights_json) if c.insights_json else {},
            }
            for c in campaigns
        ]
    finally:
        db.close()


# ── Board Meeting Operations ─────────────────────────────────────────────────


def start_board_meeting(
    meeting_id: str,
    title: str,
    agenda: str,
    participants: List[str],
) -> Dict[str, Any]:
    """Start and register a multi-agent board meeting."""
    db = get_db_session()
    try:
        meeting = BoardMeetingModel(
            meeting_id=meeting_id,
            title=title,
            agenda=agenda,
            status="in_progress",
            participants_json=json.dumps(participants),
            created_at=time.time(),
        )
        db.add(meeting)
        db.commit()
        logger.info("[BOARD_MEETING] Started meeting: %s (%s)", title, meeting_id)
        return {
            "meeting_id": meeting_id,
            "title": title,
            "agenda": agenda,
            "status": "in_progress",
            "participants": participants,
        }
    finally:
        db.close()


def add_board_meeting_transcript(
    meeting_id: str,
    speaker: str,
    message: str,
) -> Dict[str, Any]:
    """Append a deliberation message from an agent to the meeting transcript."""
    db = get_db_session()
    try:
        count = db.query(BoardMeetingTranscriptModel).filter(BoardMeetingTranscriptModel.meeting_id == meeting_id).count()
        transcript = BoardMeetingTranscriptModel(
            meeting_id=meeting_id,
            speaker=speaker,
            message=message,
            turn_index=count + 1,
            timestamp=time.time(),
        )
        db.add(transcript)
        db.commit()
        return {
            "id": transcript.id,
            "meeting_id": meeting_id,
            "speaker": speaker,
            "message": message,
            "turn_index": transcript.turn_index,
        }
    finally:
        db.close()


def conclude_board_meeting(
    meeting_id: str,
    action_plan: str,
) -> Dict[str, Any]:
    """Conclude a board meeting and persist the finalized action plan."""
    db = get_db_session()
    try:
        meeting = db.query(BoardMeetingModel).filter(BoardMeetingModel.meeting_id == meeting_id).first()
        if not meeting:
            raise ValueError(f"Meeting '{meeting_id}' not found")
        meeting.status = "concluded"
        meeting.action_plan = action_plan
        meeting.concluded_at = time.time()
        db.commit()
        logger.info("[BOARD_MEETING] Concluded meeting: %s", meeting_id)
        return {
            "meeting_id": meeting_id,
            "title": meeting.title,
            "status": "concluded",
            "action_plan": action_plan,
        }
    finally:
        db.close()


def get_board_meeting_details(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve complete meeting state and chronological transcript."""
    db = get_db_session()
    try:
        meeting = db.query(BoardMeetingModel).filter(BoardMeetingModel.meeting_id == meeting_id).first()
        if not meeting:
            return None
        transcripts = (
            db.query(BoardMeetingTranscriptModel)
            .filter(BoardMeetingTranscriptModel.meeting_id == meeting_id)
            .order_by(BoardMeetingTranscriptModel.turn_index.asc())
            .all()
        )
        return {
            "meeting_id": meeting.meeting_id,
            "title": meeting.title,
            "agenda": meeting.agenda,
            "status": meeting.status,
            "participants": json.loads(meeting.participants_json),
            "action_plan": meeting.action_plan,
            "created_at": meeting.created_at,
            "concluded_at": meeting.concluded_at,
            "transcript": [
                {
                    "speaker": t.speaker,
                    "message": t.message,
                    "turn_index": t.turn_index,
                    "timestamp": t.timestamp,
                }
                for t in transcripts
            ],
        }
    finally:
        db.close()


def list_board_meetings(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List board meetings optionally filtered by status ('in_progress' or 'concluded')."""
    db = get_db_session()
    try:
        query = db.query(BoardMeetingModel)
        if status:
            query = query.filter(BoardMeetingModel.status == status)
        meetings = query.order_by(BoardMeetingModel.created_at.desc()).all()
        return [
            {
                "meeting_id": m.meeting_id,
                "title": m.title,
                "agenda": m.agenda,
                "status": m.status,
                "participants": json.loads(m.participants_json) if m.participants_json else [],
                "created_at": m.created_at,
                "concluded_at": m.concluded_at,
            }
            for m in meetings
        ]
    finally:
        db.close()


def conclude_all_active_board_meetings(action_plan: str = "Concluded all active meetings") -> Dict[str, Any]:
    """Conclude all in-progress board meetings at once."""
    db = get_db_session()
    try:
        active_meetings = db.query(BoardMeetingModel).filter(BoardMeetingModel.status == "in_progress").all()
        now = time.time()
        concluded_ids = []
        for m in active_meetings:
            m.status = "concluded"
            m.concluded_at = now
            m.action_plan = action_plan
            concluded_ids.append(m.meeting_id)
        db.commit()
        return {
            "concluded_count": len(concluded_ids),
            "concluded_meeting_ids": concluded_ids,
            "status": "success",
        }
    finally:
        db.close()

