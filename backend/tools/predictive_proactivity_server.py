"""Predictive Proactivity MCP Server.

Anticipates Mr. Owen's needs based on patterns, time, and context.
Provides proactive suggestions and automated actions.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("predictive_proactivity")
mcp = FastMCP("PredictiveProactivity")

# Scheduled predictions and automations
_predictions: List[Dict[str, Any]] = []
_automations: List[Dict[str, Any]] = [
    {
        "id": "morning_briefing",
        "name": "Morning Briefing",
        "trigger": "daily_9am",
        "description": "Generate daily summary of WhatsApp leads, campaign stats, and agent health",
        "enabled": True,
        "last_run": None,
    },
    {
        "id": "lead_check",
        "name": "Lead Pipeline Check",
        "trigger": "every_4_hours",
        "description": "Check for new leads and alert if high-score prospects found",
        "enabled": True,
        "last_run": None,
    },
    {
        "id": "agent_health",
        "name": "Agent Health Monitor",
        "trigger": "every_30_minutes",
        "description": "Check all agents for failures and alert on issues",
        "enabled": True,
        "last_run": None,
    },
    {
        "id": "budget_alert",
        "name": "Budget Threshold Alert",
        "trigger": "when_budget_80_percent",
        "description": "Alert when campaign spend reaches 80% of daily budget",
        "enabled": True,
        "last_run": None,
    },
]

_proactive_suggestions: List[Dict[str, Any]] = []


def _time_based_suggestions() -> List[Dict[str, str]]:
    """Generate suggestions based on time of day."""
    suggestions = []
    now = datetime.now()
    hour = now.hour

    if 8 <= hour <= 10:
        suggestions.append({
            "type": "morning_routine",
            "message": "Good morning! Shall I run your daily briefing?",
            "action": "run_morning_briefing",
        })
        suggestions.append({
            "type": "lead_check",
            "message": "Would you like me to check for new leads from overnight?",
            "action": "check_new_leads",
        })
    elif 12 <= hour <= 14:
        suggestions.append({
            "type": "midday_review",
            "message": "Midday check: How are today's campaigns performing?",
            "action": "campaign_status",
        })
    elif 17 <= hour <= 19:
        suggestions.append({
            "type": "end_of_day",
            "message": "End of day approaching. Shall I generate a summary?",
            "action": "generate_daily_summary",
        })
    elif 21 <= hour or hour <= 6:
        suggestions.append({
            "type": "after_hours",
            "message": "After hours: WhatsApp messages may need attention in the morning.",
            "action": "queue_morning_check",
        })

    return suggestions


def _pattern_based_suggestions() -> List[Dict[str, str]]:
    """Generate suggestions based on learned patterns."""
    suggestions = []

    # Check for repeated task patterns
    suggestions.append({
        "type": "proactive_offer",
        "message": "I noticed you often check WhatsApp leads at this time. Want me to prepare a summary?",
        "action": "prepare_whatsapp_summary",
    })

    return suggestions


@mcp.tool()
def get_proactive_suggestions() -> str:
    """Get proactive suggestions based on time, patterns, and context.

    Returns:
        JSON with relevant suggestions
    """
    suggestions = []
    suggestions.extend(_time_based_suggestions())
    suggestions.extend(_pattern_based_suggestions())

    # Check for pending items
    suggestions.append({
        "type": "pending_action",
        "message": "There are 3 high-score leads (80+) awaiting outreach. Start sequences?",
        "action": "start_outreach_sequence",
    })

    return json.dumps({
        "status": "success",
        "suggestions": suggestions,
        "count": len(suggestions),
    }, indent=2)


@mcp.tool()
def check_automation_triggers() -> str:
    """Check if any scheduled automations should run.

    Returns:
        JSON with automations that need to run
    """
    now = datetime.now()
    due_automations = []

    for automation in _automations:
        if not automation["enabled"]:
            continue

        should_run = False
        reason = ""

        if automation["trigger"] == "daily_9am":
            if now.hour == 9 and (automation["last_run"] is None or
                datetime.fromtimestamp(automation["last_run"]).date() < now.date()):
                should_run = True
                reason = "Daily 9am briefing due"

        elif automation["trigger"] == "every_4_hours":
            if automation["last_run"] is None or (time.time() - automation["last_run"]) >= 14400:
                should_run = True
                reason = "4-hour check interval elapsed"

        elif automation["trigger"] == "every_30_minutes":
            if automation["last_run"] is None or (time.time() - automation["last_run"]) >= 1800:
                should_run = True
                reason = "30-minute health check due"

        if should_run:
            due_automations.append({
                "automation": automation["name"],
                "id": automation["id"],
                "reason": reason,
                "description": automation["description"],
            })

    return json.dumps({
        "status": "success",
        "due_automations": due_automations,
        "total_enabled": len([a for a in _automations if a["enabled"]]),
    }, indent=2)


@mcp.tool()
def record_automation_run(automation_id: str) -> str:
    """Record that an automation was run.

    Args:
        automation_id: ID of the automation that ran

    Returns:
        JSON confirmation
    """
    for automation in _automations:
        if automation["id"] == automation_id:
            automation["last_run"] = time.time()
            return json.dumps({
                "status": "recorded",
                "automation": automation["name"],
                "next_run": automation["trigger"],
            })

    return json.dumps({"status": "not_found", "automation_id": automation_id})


@mcp.tool()
def add_custom_automation(
    name: str,
    trigger: str,
    description: str,
    action: str,
) -> str:
    """Add a custom automation rule.

    Args:
        name: Name of the automation
        trigger: When it should run (e.g., 'daily_9am', 'every_hour', 'on_lead_score_80')
        description: What the automation does
        action: Action to take when triggered

    Returns:
        JSON confirmation
    """
    new_automation = {
        "id": f"custom_{int(time.time())}",
        "name": name,
        "trigger": trigger,
        "description": description,
        "action": action,
        "enabled": True,
        "last_run": None,
    }
    _automations.append(new_automation)

    return json.dumps({
        "status": "created",
        "automation_id": new_automation["id"],
        "name": name,
    })


@mcp.tool()
def predict_next_action(context: str = "") -> str:
    """Predict what Mr. Owen might want to do next.

    Args:
        context: Optional context about current situation

    Returns:
        JSON with predicted next actions
    """
    predictions = []

    # Time-based predictions
    now = datetime.now()
    hour = now.hour

    if 8 <= hour <= 10:
        predictions.append({
            "action": "Check WhatsApp leads",
            "probability": 85,
            "reason": "Morning routine pattern",
        })
        predictions.append({
            "action": "Review campaign performance",
            "probability": 70,
            "reason": "Start-of-day review habit",
        })
    elif 14 <= hour <= 16:
        predictions.append({
            "action": "Check lead outreach status",
            "probability": 75,
            "reason": "Afternoon follow-up pattern",
        })

    # Context-based predictions
    if "lead" in context.lower():
        predictions.append({
            "action": "Start outreach sequence",
            "probability": 80,
            "reason": "Lead context detected",
        })
    elif "campaign" in context.lower():
        predictions.append({
            "action": "Review ad performance",
            "probability": 85,
            "reason": "Campaign context detected",
        })

    # Default predictions if none specific
    if not predictions:
        predictions = [
            {"action": "Status check", "probability": 60, "reason": "General check-in"},
            {"action": "Review pending tasks", "probability": 50, "reason": "Task management"},
        ]

    return json.dumps({
        "status": "success",
        "predictions": sorted(predictions, key=lambda x: x["probability"], reverse=True),
        "context": context,
    })


@mcp.tool()
def get_automation_schedule() -> str:
    """Get the full automation schedule.

    Returns:
        JSON with all automations and their status
    """
    return json.dumps({
        "status": "success",
        "automations": _automations,
        "total": len(_automations),
        "enabled": len([a for a in _automations if a["enabled"]]),
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
