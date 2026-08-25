"""FastAPI routes for Shared Memory (Prospects, Creatives, Campaigns, Board Meetings)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.auth import verify_api_key
from services import shared_memory

router = APIRouter(prefix="/api/shared-memory", tags=["Shared Memory"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class UpsertProspectRequest(BaseModel):
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    country: str = "Global"
    city: Optional[str] = None
    industry: Optional[str] = None
    source_agent: str = "LeadResearchAgent"
    status: str = "new"
    lead_score: int = 50
    notes: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None


class UpsertCreativeRequest(BaseModel):
    title: str
    headline: str
    body_copy: str
    call_to_action: str = "Learn More"
    hook_type: str = "direct_offer"
    target_audience: Optional[str] = None
    image_prompt: Optional[str] = None
    image_url: Optional[str] = None
    status: str = "draft"
    variations: Optional[List[Dict[str, str]]] = None


class SaveCampaignRequest(BaseModel):
    name: str
    objective: str = "OUTCOME_LEADS"
    status: str = "PAUSED"
    daily_budget: float = 0.0
    targeting: Optional[Dict[str, Any]] = None
    creative_ids: Optional[List[int]] = None
    meta_campaign_id: Optional[str] = None
    insights: Optional[Dict[str, Any]] = None


class StartMeetingRequest(BaseModel):
    meeting_id: str
    title: str
    agenda: str
    participants: List[str]


class SpeakMeetingRequest(BaseModel):
    speaker: str
    message: str


class ConcludeMeetingRequest(BaseModel):
    action_plan: str


# ── Prospects Endpoints ──────────────────────────────────────────────────────


@router.get("/prospects")
async def get_prospects(
    query: Optional[str] = None,
    status: Optional[str] = None,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    _auth=Depends(verify_api_key),
):
    results = shared_memory.search_prospects(
        query=query,
        status=status,
        country=country,
        industry=industry,
        limit=limit,
    )
    return {"prospects": results, "count": len(results)}


@router.post("/prospects")
async def create_or_update_prospect(req: UpsertProspectRequest, _auth=Depends(verify_api_key)):
    return shared_memory.upsert_prospect(**req.model_dump())


# ── Creatives Endpoints ──────────────────────────────────────────────────────


@router.get("/creatives")
async def get_creatives(
    status: Optional[str] = None,
    target_audience: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    _auth=Depends(verify_api_key),
):
    results = shared_memory.list_ad_creatives(
        status=status,
        target_audience=target_audience,
        limit=limit,
    )
    return {"creatives": results, "count": len(results)}


@router.post("/creatives")
async def create_creative(req: UpsertCreativeRequest, _auth=Depends(verify_api_key)):
    return shared_memory.upsert_ad_creative(**req.model_dump())


# ── Campaigns Endpoints ──────────────────────────────────────────────────────


@router.get("/campaigns")
async def get_campaigns(
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    _auth=Depends(verify_api_key),
):
    results = shared_memory.list_campaigns(status=status, limit=limit)
    return {"campaigns": results, "count": len(results)}


@router.post("/campaigns")
async def save_campaign(req: SaveCampaignRequest, _auth=Depends(verify_api_key)):
    return shared_memory.create_or_update_campaign(**req.model_dump())


# ── Board Meetings Endpoints ─────────────────────────────────────────────────


@router.post("/meetings")
async def start_meeting(req: StartMeetingRequest, _auth=Depends(verify_api_key)):
    return shared_memory.start_board_meeting(**req.model_dump())


@router.post("/meetings/{meeting_id}/speak")
async def speak_in_meeting(meeting_id: str, req: SpeakMeetingRequest, _auth=Depends(verify_api_key)):
    return shared_memory.add_board_meeting_transcript(
        meeting_id=meeting_id,
        speaker=req.speaker,
        message=req.message,
    )


@router.post("/meetings/{meeting_id}/conclude")
async def conclude_meeting(meeting_id: str, req: ConcludeMeetingRequest, _auth=Depends(verify_api_key)):
    try:
        return shared_memory.conclude_board_meeting(
            meeting_id=meeting_id,
            action_plan=req.action_plan,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: str, _auth=Depends(verify_api_key)):
    meeting = shared_memory.get_board_meeting_details(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting '{meeting_id}' not found")
    return meeting
