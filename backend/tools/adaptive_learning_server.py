"""Adaptive Learning MCP Server.

Tracks Mr. Owen's preferences, patterns, and behavior to enable
predictive proactivity and personalized responses.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("adaptive_learning")
mcp = FastMCP("AdaptiveLearning")

# In-memory preference store (in production, use SQLite)
_preferences: Dict[str, Any] = {
    "agent_preferences": defaultdict(lambda: {"uses": 0, "last_used": 0, "success_rate": 100}),
    "task_patterns": defaultdict(lambda: {"count": 0, "avg_time": 0, "preferred_time": ""}),
    "communication_style": {
        "preferred_length": "concise",  # concise, detailed, mixed
        "preferred_format": "bullet",  # bullet, paragraph, table
        "uses_emoji": False,
        "formality_level": "executive",  # casual, professional, executive
    },
    "active_hours": defaultdict(int),  # hour -> activity count
    "topic_interests": defaultdict(lambda: {"mentions": 0, "engagement": 0}),
    "rejection_history": [],  # Tasks user rejected/corrected
    "acceptance_history": [],  # Tasks user accepted/approved
}

_learning_events: List[Dict[str, Any]] = []


def _record_event(event_type: str, details: Dict[str, Any]):
    """Record a learning event."""
    _learning_events.append({
        "type": event_type,
        "details": details,
        "timestamp": time.time(),
    })
    # Keep last 1000 events
    if len(_learning_events) > 1000:
        _learning_events.pop(0)


@mcp.tool()
def track_preference(
    category: str,
    key: str,
    value: str,
    context: str = "",
) -> str:
    """Track a user preference or pattern.

    Args:
        category: Preference category (e.g., 'agent_preferences', 'communication_style')
        key: Specific preference key
        value: Preference value
        context: Optional context for when this preference was observed

    Returns:
        JSON confirmation
    """
    if category == "agent_preferences":
        _preferences["agent_preferences"][key]["uses"] += 1
        _preferences["agent_preferences"][key]["last_used"] = time.time()
    elif category == "communication_style":
        _preferences["communication_style"][key] = value
    elif category == "topic_interests":
        _preferences["topic_interests"][key]["mentions"] += 1
    else:
        if category not in _preferences:
            _preferences[category] = {}
        _preferences[category][key] = value

    _record_event("preference_tracked", {"category": category, "key": key, "value": value, "context": context})

    return json.dumps({
        "status": "recorded",
        "category": category,
        "key": key,
        "value": value,
    })


@mcp.tool()
def record_task_outcome(
    task_type: str,
    agent_used: str,
    outcome: str,
    user_feedback: str = "",
    duration_seconds: float = 0,
) -> str:
    """Record whether a task was accepted or rejected by the user.

    Args:
        task_type: Type of task (e.g., 'lead_research', 'ad_copy', 'website_build')
        agent_used: Which agent handled it
        outcome: 'accepted' or 'rejected'
        user_feedback: Optional user feedback
        duration_seconds: How long the task took

    Returns:
        JSON confirmation with learning insights
    """
    record = {
        "task_type": task_type,
        "agent": agent_used,
        "outcome": outcome,
        "feedback": user_feedback,
        "duration": duration_seconds,
        "timestamp": time.time(),
    }

    if outcome == "accepted":
        _preferences["acceptance_history"].append(record)
        _preferences["agent_preferences"][agent_used]["success_rate"] = min(
            100, _preferences["agent_preferences"][agent_used]["success_rate"] + 5
        )
    else:
        _preferences["rejection_history"].append(record)
        _preferences["agent_preferences"][agent_used]["success_rate"] = max(
            0, _preferences["agent_preferences"][agent_used]["success_rate"] - 10
        )

    # Track task patterns
    _preferences["task_patterns"][task_type]["count"] += 1
    if duration_seconds > 0:
        pattern = _preferences["task_patterns"][task_type]
        pattern["avg_time"] = ((pattern["avg_time"] * (pattern["count"] - 1)) + duration_seconds) / pattern["count"]

    _record_event("task_outcome", record)

    # Generate learning insight
    insight = ""
    if outcome == "rejected" and user_feedback:
        insight = f"Learned: User prefers different approach for {task_type}. Feedback: {user_feedback}"
    elif outcome == "accepted":
        insight = f"Confirmed: {agent_used} is effective for {task_type}"

    return json.dumps({
        "status": "recorded",
        "insight": insight,
        "agent_success_rate": _preferences["agent_preferences"][agent_used]["success_rate"],
    })


@mcp.tool()
def get_user_preferences() -> str:
    """Get Mr. Owen's learned preferences and patterns.

    Returns:
        JSON with comprehensive preference profile
    """
    # Calculate active hours pattern
    active_hours = _preferences.get("active_hours", {})
    peak_hours = sorted(active_hours.items(), key=lambda x: x[1], reverse=True)[:5]

    # Get top agent preferences
    agent_prefs = dict(_preferences["agent_preferences"])
    top_agents = sorted(agent_prefs.items(), key=lambda x: x[1]["uses"], reverse=True)[:5]

    # Get task patterns
    task_patterns = dict(_preferences["task_patterns"])
    frequent_tasks = sorted(task_patterns.items(), key=lambda x: x[1]["count"], reverse=True)[:5]

    return json.dumps({
        "communication_style": _preferences["communication_style"],
        "peak_active_hours": [{"hour": h, "activity_count": c} for h, c in peak_hours],
        "top_agents": [{"agent": a, "uses": d["uses"], "success_rate": d["success_rate"]} for a, d in top_agents],
        "frequent_tasks": [{"task": t, "count": d["count"], "avg_time": round(d["avg_time"], 1)} for t, d in frequent_tasks],
        "total_accepted": len(_preferences["acceptance_history"]),
        "total_rejected": len(_preferences["rejection_history"]),
        "acceptance_rate": f"{len(_preferences['acceptance_history']) / max(len(_preferences['acceptance_history']) + len(_preferences['rejection_history']), 1) * 100:.1f}%",
        "recent_rejections": _preferences["rejection_history"][-3:],
    }, indent=2)


@mcp.tool()
def get_recommended_agent(task_type: str) -> str:
    """Get the best agent recommendation for a task type based on learned preferences.

    Args:
        task_type: Type of task to get recommendation for

    Returns:
        JSON with agent recommendation and reasoning
    """
    # Default agent mapping
    default_agents = {
        "lead_research": "LeadResearchAgent",
        "ad_copy": "CreativeAgent",
        "outreach": "OutreachAgent",
        "ads": "AdsAgent",
        "finance": "FinanceAgent",
        "research": "ResearchAgent",
        "website": "DemoBuilderAgent",
        "whatsapp": "WhatsAppAgent",
        "calendar": "PersonalAgent",
        "iot": "IoTAgent",
        "music": "MusicAgent",
    }

    # Check if we have learned preference
    agent_scores = {}
    for agent_name, metrics in _preferences["agent_preferences"].items():
        if metrics["uses"] > 0:
            agent_scores[agent_name] = {
                "score": metrics["success_rate"],
                "uses": metrics["uses"],
            }

    # Get recommendation
    if agent_scores:
        best_agent = max(agent_scores.items(), key=lambda x: x[1]["score"])
        recommended = best_agent[0]
        confidence = best_agent[1]["score"]
        reasoning = f"Based on {best_agent[1]['uses']} previous uses with {confidence}% success rate"
    else:
        recommended = default_agents.get(task_type, "Jarvis")
        confidence = 50
        reasoning = "Using default mapping (no learning data yet)"

    return json.dumps({
        "task_type": task_type,
        "recommended_agent": recommended,
        "confidence": confidence,
        "reasoning": reasoning,
        "alternative_agents": [
            a for a in default_agents.values()
            if a != recommended
        ][:2],
    })


@mcp.tool()
def learn_from_correction(
    original_action: str,
    corrected_action: str,
    reason: str = "",
) -> str:
    """Learn from a user correction to improve future behavior.

    Args:
        original_action: What Jarvis originally did/suggested
        corrected_action: What the user wanted instead
        reason: Why the correction was needed

    Returns:
        JSON confirmation with learning applied
    """
    correction = {
        "original": original_action,
        "corrected": corrected_action,
        "reason": reason,
        "timestamp": time.time(),
    }

    _preferences["corrections"] = _preferences.get("corrections", [])
    _preferences["corrections"].append(correction)

    # Keep last 50 corrections
    if len(_preferences["corrections"]) > 50:
        _preferences["corrections"] = _preferences["corrections"][-50:]

    _record_event("correction", correction)

    return json.dumps({
        "status": "learned",
        "message": "I'll remember this correction for future similar situations.",
        "correction_logged": True,
        "total_corrections": len(_preferences["corrections"]),
    })


if __name__ == "__main__":
    mcp.run()
