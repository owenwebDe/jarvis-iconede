"""LangGraph FastAPI Router for Jarvis OS.

Exposes REST endpoints to trigger, inspect, and resume stateful LangGraph workflows
including Cyclical Website Generation and Human-in-the-Loop WhatsApp Outreach.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from services.langgraph_engine import get_langgraph_engine

logger = logging.getLogger("langgraph_router")

router = APIRouter(prefix="/api/v1/graphs", tags=["langgraph"])


class WebsiteBuilderRequest(BaseModel):
    business_name: str
    industry: str = "Technology"
    archetype: str = "luxury"


class LeadOutreachRequest(BaseModel):
    target_district: str = "Wuse 2, Abuja"


class ResumeGraphRequest(BaseModel):
    thread_id: str
    approved: bool = True
    feedback: Optional[str] = None


@router.post("/website-builder")
async def run_website_builder(req: WebsiteBuilderRequest):
    """Trigger the Cyclical Website Builder LangGraph workflow."""
    engine = get_langgraph_engine()
    if not engine.website_builder_graph:
        raise HTTPException(status_code=503, detail="LangGraph engine not initialized.")

    try:
        result = await engine.run_website_builder(
            business_name=req.business_name,
            industry=req.industry,
            archetype=req.archetype,
        )
        return {
            "status": "success",
            "workflow": "website_builder",
            "run_id": result.get("run_id"),
            "qa_passed": result.get("qa_passed"),
            "qa_retries": result.get("qa_retry_count"),
            "preview_url": result.get("preview_url"),
            "output": result.get("final_output"),
        }
    except Exception as e:
        logger.error(f"Website builder graph execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lead-outreach")
async def run_lead_outreach(req: LeadOutreachRequest):
    """Trigger the Lead Harvest & Outreach LangGraph workflow (pauses at HITL gate)."""
    engine = get_langgraph_engine()
    if not engine.lead_outreach_graph:
        raise HTTPException(status_code=503, detail="LangGraph engine not initialized.")

    try:
        result = await engine.run_lead_outreach(target_district=req.target_district)
        return {
            "status": "paused_at_hitl_gate",
            "workflow": "lead_outreach",
            "run_id": result.get("run_id"),
            "interrupt_reason": result.get("interrupt_reason"),
            "leads_count": len(result.get("verified_leads", [])),
            "pitches_preview": result.get("pitches"),
            "action_required": "Review pitches and call POST /api/v1/graphs/resume with thread_id to dispatch.",
        }
    except Exception as e:
        logger.error(f"Lead outreach graph execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume")
async def resume_graph(req: ResumeGraphRequest):
    """Approve or reject an interrupted LangGraph workflow."""
    engine = get_langgraph_engine()
    try:
        result = await engine.resume_lead_outreach(thread_id=req.thread_id, approved=req.approved)
        return {
            "status": "completed" if req.approved else "cancelled",
            "thread_id": req.thread_id,
            "result": result.get("final_output"),
            "outreach_results": result.get("outreach_results"),
        }
    except Exception as e:
        logger.error(f"Failed to resume LangGraph execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))
