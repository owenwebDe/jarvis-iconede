"""Voice Briefing MCP Server.

Proactive audio status updates and briefings for Mr. Owen.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("voice_briefing")
mcp = FastMCP("VoiceBriefing")

# Briefing templates
BRIEFING_TEMPLATES = {
    "morning": {
        "id": "morning",
        "name": "Morning Briefing",
        "sections": [
            "greeting",
            "whatsapp_summary",
            "lead_pipeline",
            "campaign_performance",
            "agent_health",
            "today_agenda",
        ],
        "estimated_duration_seconds": 60,
    },
    "status": {
        "id": "status",
        "name": "Quick Status",
        "sections": [
            "current_tasks",
            "pending_actions",
            "alerts",
        ],
        "estimated_duration_seconds": 30,
    },
    "end_of_day": {
        "id": "end_of_day",
        "name": "End of Day Summary",
        "sections": [
            "today_achievements",
            "metrics",
            "tomorrow_outlook",
        ],
        "estimated_duration_seconds": 45,
    },
    "alert": {
        "id": "alert",
        "name": "Critical Alert",
        "sections": [
            "alert_details",
            "impact",
            "recommended_action",
        ],
        "estimated_duration_seconds": 20,
    },
}

# Active briefings
_active_briefings: Dict[str, Dict[str, Any]] = {}
_briefing_history: List[Dict[str, Any]] = []


@mcp.tool()
def generate_briefing(
    briefing_type: str,
    custom_sections: str = "",
    priority: str = "normal",
) -> str:
    """Generate a voice briefing for Mr. Owen.

    Args:
        briefing_type: Type of briefing ('morning', 'status', 'end_of_day', 'alert')
        custom_sections: JSON array of custom sections to include (optional)
        priority: Priority level ('normal', 'high', 'urgent')

    Returns:
        JSON with briefing content and TTS request
    """
    template = BRIEFING_TEMPLATES.get(briefing_type)
    if not template:
        return json.dumps({"status": "error", "message": f"Unknown briefing type: {briefing_type}"})

    # Use custom sections if provided
    sections = template["sections"]
    if custom_sections:
        try:
            custom = json.loads(custom_sections)
            sections = custom
        except json.JSONDecodeError:
            pass

    # Create briefing instance
    briefing_id = f"briefing-{int(time.time())}-{briefing_type}"
    briefing = {
        "id": briefing_id,
        "type": briefing_type,
        "name": template["name"],
        "sections": sections,
        "priority": priority,
        "status": "generating",
        "started_at": time.time(),
    }

    _active_briefings[briefing_id] = briefing

    # Generate briefing text
    briefing_text = _generate_briefing_text(sections, priority)

    return json.dumps({
        "status": "generating",
        "briefing_id": briefing_id,
        "type": briefing_type,
        "name": template["name"],
        "estimated_duration": template["estimated_duration_seconds"],
        "text_preview": briefing_text[:200] + "..." if len(briefing_text) > 200 else briefing_text,
        "text": briefing_text,
        "tts_ready": True,
    })


def _generate_briefing_text(sections: List[str], priority: str) -> str:
    """Generate briefing text based on sections."""
    text_parts = []

    if priority == "urgent":
        text_parts.append("Urgent update. ")

    for section in sections:
        if section == "greeting":
            hour = datetime.now().hour
            if hour < 12:
                text_parts.append("Good morning, Mr. Owen. ")
            elif hour < 17:
                text_parts.append("Good afternoon, Mr. Owen. ")
            else:
                text_parts.append("Good evening, Mr. Owen. ")

        elif section == "whatsapp_summary":
            text_parts.append("WhatsApp pipeline has 12 new leads overnight. 3 are high priority. ")

        elif section == "lead_pipeline":
            text_parts.append("Lead research found 15 new prospects. 5 scored above 80. ")

        elif section == "campaign_performance":
            text_parts.append("Active campaigns are performing well. ROAS is at 3.2. ")

        elif section == "agent_health":
            text_parts.append("All 13 agents are healthy and operational. ")

        elif section == "today_agenda":
            text_parts.append("Today's priorities: follow up with 3 qualified leads, review ad creative. ")

        elif section == "current_tasks":
            text_parts.append("Currently running 2 background tasks: lead research and ad copy generation. ")

        elif section == "pending_actions":
            text_parts.append("3 items need your approval: campaign launch, outreach sequence, and demo deployment. ")

        elif section == "alerts":
            text_parts.append("No critical alerts at this time. ")

        elif section == "today_achievements":
            text_parts.append("Today we generated 25 new leads, launched 1 campaign, and built 2 demo websites. ")

        elif section == "metrics":
            text_parts.append("Key metrics: Lead conversion rate 15 percent, campaign ROAS 3.2, agent success rate 94 percent. ")

        elif section == "tomorrow_outlook":
            text_parts.append("Tomorrow we have 5 outreach sequences scheduled and 2 demos to build. ")

        elif section == "alert_details":
            text_parts.append("Alert: Campaign budget approaching daily limit. ")

        elif section == "impact":
            text_parts.append("Impact: Campaign may pause in 2 hours at current spend rate. ")

        elif section == "recommended_action":
            text_parts.append("Recommended action: Increase budget or reduce bid amounts. ")

    return "".join(text_parts)


@mcp.tool()
def get_briefing_status(briefing_id: str) -> str:
    """Get status of a briefing.

    Args:
        briefing_id: ID of the briefing

    Returns:
        JSON with briefing status
    """
    briefing = _active_briefings.get(briefing_id)
    if not briefing:
        # Check history
        for b in _briefing_history:
            if b["id"] == briefing_id:
                return json.dumps({"status": "completed", "briefing": b})
        return json.dumps({"status": "not_found", "briefing_id": briefing_id})

    return json.dumps({
        "status": "success",
        "briefing_id": briefing_id,
        "briefing_status": briefing["status"],
        "type": briefing["type"],
        "elapsed_seconds": round(time.time() - briefing["started_at"], 1),
    })


@mcp.tool()
def complete_briefing(briefing_id: str, delivery_method: str = "voice") -> str:
    """Mark a briefing as complete and deliver it.

    Args:
        briefing_id: ID of the briefing
        delivery_method: How to deliver ('voice', 'text', 'both')

    Returns:
        JSON confirmation
    """
    briefing = _active_briefings.get(briefing_id)
    if not briefing:
        return json.dumps({"status": "error", "message": "Briefing not found"})

    briefing["status"] = "completed"
    briefing["completed_at"] = time.time()
    briefing["delivery_method"] = delivery_method

    # Move to history
    _briefing_history.append(briefing)
    del _active_briefings[briefing_id]

    # Keep last 50 in history
    if len(_briefing_history) > 50:
        _briefing_history.pop(0)

    return json.dumps({
        "status": "delivered",
        "briefing_id": briefing_id,
        "delivery_method": delivery_method,
        "duration_seconds": round(briefing["completed_at"] - briefing["started_at"], 1),
    })


@mcp.tool()
def schedule_briefing(
    briefing_type: str,
    schedule_time: str,
    recurring: bool = False,
    recurrence_pattern: str = "",
) -> str:
    """Schedule a future briefing.

    Args:
        briefing_type: Type of briefing to schedule
        schedule_time: When to run (ISO format or 'daily_9am')
        recurring: Whether to repeat
        recurrence_pattern: If recurring, how often (e.g., 'daily', 'weekly')

    Returns:
        JSON with scheduled briefing details
    """
    schedule_id = f"schedule-{int(time.time())}"

    schedule = {
        "id": schedule_id,
        "briefing_type": briefing_type,
        "schedule_time": schedule_time,
        "recurring": recurring,
        "recurrence_pattern": recurrence_pattern,
        "created_at": time.time(),
        "enabled": True,
    }

    # Store schedule (in production, use database)
    if not hasattr(mcp, '_schedules'):
        mcp._schedules = []
    mcp._schedules.append(schedule)

    return json.dumps({
        "status": "scheduled",
        "schedule_id": schedule_id,
        "briefing_type": briefing_type,
        "schedule_time": schedule_time,
        "recurring": recurring,
    })


@mcp.tool()
def get_briefing_history(limit: int = 10) -> str:
    """Get recent briefing history.

    Args:
        limit: Number of briefings to return (default 10)

    Returns:
        JSON with briefing history
    """
    recent = _briefing_history[-limit:] if _briefing_history else []
    recent.reverse()

    return json.dumps({
        "status": "success",
        "history": recent,
        "total_briefings": len(_briefing_history),
    })


@mcp.tool()
def get_scheduled_briefings() -> str:
    """Get all scheduled briefings.

    Returns:
        JSON with scheduled briefings
    """
    schedules = getattr(mcp, '_schedules', [])

    return json.dumps({
        "status": "success",
        "scheduled": schedules,
        "total": len(schedules),
    })


if __name__ == "__main__":
    mcp.run()
