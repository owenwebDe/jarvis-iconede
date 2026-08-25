"""Workflow Templates MCP Server.

Pre-built automation sequences for common business operations.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("workflow_templates")
mcp = FastMCP("WorkflowTemplates")

# Pre-built workflow templates
WORKFLOW_TEMPLATES = {
    "morning_briefing": {
        "id": "morning_briefing",
        "name": "Morning Briefing",
        "description": "Generate daily summary of WhatsApp leads, campaign stats, and agent health",
        "schedule": "daily_9am",
        "steps": [
            {"agent": "WhatsAppAgent", "task": "Check overnight WhatsApp messages and lead pipeline", "timeout": 60},
            {"agent": "AdsAgent", "task": "Get yesterday's campaign performance metrics", "timeout": 30},
            {"agent": "LeadResearchAgent", "task": "Check for new high-score leads from overnight research", "timeout": 45},
            {"action": "compile_report", "template": "morning_summary"},
        ],
        "estimated_duration": 3,
    },
    "lead_nurture": {
        "id": "lead_nurture",
        "name": "Lead Nurture Sequence",
        "description": "Automated sequence: Research → Qualify → Outreach → Follow-up",
        "steps": [
            {"agent": "LeadResearchAgent", "task": "Research and score prospects in target industry", "timeout": 120},
            {"condition": "score >= 70", "next_step": "qualify"},
            {"action": "end", "reason": "Lead score too low for outreach"},
            {"label": "qualify"},
            {"agent": "CreativeAgent", "task": "Create personalized outreach message for qualified leads", "timeout": 60},
            {"agent": "OutreachAgent", "task": "Send initial outreach sequence", "timeout": 45},
            {"action": "schedule_followup", "delay_hours": 72},
        ],
        "estimated_duration": 5,
    },
    "campaign_launch": {
        "id": "campaign_launch",
        "name": "Campaign Launch",
        "description": "Full campaign setup: Research → Creative → Ads → Monitor",
        "steps": [
            {"agent": "ResearchAgent", "task": "Research target audience and competitors", "timeout": 90},
            {"agent": "CreativeAgent", "task": "Create ad copy and visual prompts", "timeout": 60},
            {"agent": "AdsAgent", "task": "Set up Meta Ads campaign in PAUSED state", "timeout": 45},
            {"action": "wait_for_approval", "prompt": "Campaign ready. Review and confirm to activate."},
            {"agent": "AdsAgent", "task": "Activate campaign and set monitoring", "timeout": 30},
        ],
        "estimated_duration": 5,
    },
    "crisis_response": {
        "id": "crisis_response",
        "name": "Crisis Response",
        "description": "Detect issue → Diagnose → Fix → Report",
        "steps": [
            {"action": "diagnose", "task": "Identify the issue and affected systems"},
            {"agent": "appropriate_agent", "task": "Attempt automated fix", "timeout": 60},
            {"condition": "fixed", "next_step": "report_success"},
            {"action": "escalate", "prompt": "Automated fix failed. Escalating to Mr. Owen."},
            {"label": "report_success"},
            {"action": "compile_report", "template": "crisis_resolution"},
        ],
        "estimated_duration": 2,
    },
    "competitor_analysis": {
        "id": "competitor_analysis",
        "name": "Competitor Analysis",
        "description": "Research competitors and generate strategic report",
        "steps": [
            {"agent": "ResearchAgent", "task": "Research competitor landscape and market positioning", "timeout": 120},
            {"agent": "FinanceAgent", "task": "Analyze competitor financial signals and funding", "timeout": 60},
            {"agent": "CreativeAgent", "task": "Identify messaging gaps and opportunities", "timeout": 45},
            {"action": "compile_report", "template": "competitor_analysis"},
        ],
        "estimated_duration": 5,
    },
    "client_demo_prep": {
        "id": "client_demo_prep",
        "name": "Client Demo Preparation",
        "description": "Build and deploy a client demo website",
        "steps": [
            {"agent": "LeadResearchAgent", "task": "Research client's industry and competitors", "timeout": 60},
            {"agent": "CreativeAgent", "task": "Create design brief and content", "timeout": 45},
            {"agent": "DemoBuilderAgent", "task": "Build React demo website", "timeout": 180},
            {"action": "quality_check", "task": "Run Playwright tests and visual analysis"},
            {"action": "deploy", "task": "Deploy to Vercel and get live URL"},
        ],
        "estimated_duration": 8,
    },
}

# Active workflow instances
_active_workflows: Dict[str, Dict[str, Any]] = {}
_workflow_history: List[Dict[str, Any]] = []


@mcp.tool()
def get_workflow_templates() -> str:
    """Get all available workflow templates.

    Returns:
        JSON with all workflow templates
    """
    return json.dumps({
        "status": "success",
        "templates": list(WORKFLOW_TEMPLATES.values()),
        "total": len(WORKFLOW_TEMPLATES),
    }, indent=2)


@mcp.tool()
def get_workflow_template(template_id: str) -> str:
    """Get details of a specific workflow template.

    Args:
        template_id: ID of the workflow template

    Returns:
        JSON with workflow template details
    """
    template = WORKFLOW_TEMPLATES.get(template_id)
    if not template:
        return json.dumps({"status": "not_found", "template_id": template_id})

    return json.dumps({
        "status": "success",
        "template": template,
    }, indent=2)


@mcp.tool()
def start_workflow(
    template_id: str,
    parameters: str = "",
    context: str = "",
) -> str:
    """Start a workflow from a template.

    Args:
        template_id: ID of the workflow template to use
        parameters: JSON string of parameters to customize the workflow
        context: Additional context for the workflow

    Returns:
        JSON with workflow instance details
    """
    template = WORKFLOW_TEMPLATES.get(template_id)
    if not template:
        return json.dumps({"status": "error", "message": f"Template '{template_id}' not found"})

    # Parse parameters
    params = {}
    if parameters:
        try:
            params = json.loads(parameters)
        except json.JSONDecodeError:
            params = {"raw": parameters}

    # Create workflow instance
    workflow_id = f"wf-{int(time.time())}-{template_id}"
    instance = {
        "id": workflow_id,
        "template_id": template_id,
        "name": template["name"],
        "status": "started",
        "current_step": 0,
        "parameters": params,
        "context": context,
        "started_at": time.time(),
        "estimated_duration": template["estimated_duration"],
        "steps": template["steps"],
    }

    _active_workflows[workflow_id] = instance

    return json.dumps({
        "status": "started",
        "workflow_id": workflow_id,
        "name": template["name"],
        "estimated_minutes": template["estimated_duration"],
        "total_steps": len(template["steps"]),
        "first_step": template["steps"][0] if template["steps"] else None,
    })


@mcp.tool()
def get_workflow_status(workflow_id: str) -> str:
    """Get status of an active workflow.

    Args:
        workflow_id: ID of the workflow instance

    Returns:
        JSON with workflow status
    """
    instance = _active_workflows.get(workflow_id)
    if not instance:
        # Check history
        for wf in _workflow_history:
            if wf["id"] == workflow_id:
                return json.dumps({"status": "completed", "workflow": wf})
        return json.dumps({"status": "not_found", "workflow_id": workflow_id})

    # Calculate progress
    total_steps = len(instance["steps"])
    current_step = instance["current_step"]
    progress = (current_step / total_steps * 100) if total_steps > 0 else 0

    return json.dumps({
        "status": "success",
        "workflow_id": workflow_id,
        "name": instance["name"],
        "workflow_status": instance["status"],
        "progress": f"{progress:.0f}%",
        "current_step": current_step,
        "total_steps": total_steps,
        "elapsed_minutes": round((time.time() - instance["started_at"]) / 60, 1),
        "estimated_remaining": max(0, instance["estimated_duration"] - (time.time() - instance["started_at"]) / 60),
    }, indent=2)


@mcp.tool()
def advance_workflow(workflow_id: str, step_result: str = "success") -> str:
    """Advance a workflow to the next step.

    Args:
        workflow_id: ID of the workflow instance
        step_result: Result of the current step ('success', 'failed', 'skipped')

    Returns:
        JSON with next step or completion status
    """
    instance = _active_workflows.get(workflow_id)
    if not instance:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    current_step = instance["current_step"]
    steps = instance["steps"]

    if step_result == "failed":
        instance["status"] = "failed"
        instance["failed_at"] = time.time()
        _workflow_history.append(instance)
        del _active_workflows[workflow_id]
        return json.dumps({
            "status": "failed",
            "workflow_id": workflow_id,
            "failed_at_step": current_step,
        })

    # Move to next step
    instance["current_step"] += 1

    # Check if workflow is complete
    if instance["current_step"] >= len(steps):
        instance["status"] = "completed"
        instance["completed_at"] = time.time()
        _workflow_history.append(instance)
        del _active_workflows[workflow_id]
        return json.dumps({
            "status": "completed",
            "workflow_id": workflow_id,
            "total_duration_minutes": round((instance["completed_at"] - instance["started_at"]) / 60, 1),
        })

    # Get next step
    next_step = steps[instance["current_step"]]

    # Check for conditions
    if "condition" in next_step:
        # In real implementation, evaluate condition
        pass

    return json.dumps({
        "status": "advanced",
        "workflow_id": workflow_id,
        "current_step": instance["current_step"],
        "total_steps": len(steps),
        "next_step": next_step,
        "progress": f"{(instance['current_step'] / len(steps) * 100):.0f}%",
    })


@mcp.tool()
def pause_workflow(workflow_id: str) -> str:
    """Pause an active workflow.

    Args:
        workflow_id: ID of the workflow to pause

    Returns:
        JSON confirmation
    """
    instance = _active_workflows.get(workflow_id)
    if not instance:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    instance["status"] = "paused"
    instance["paused_at"] = time.time()

    return json.dumps({
        "status": "paused",
        "workflow_id": workflow_id,
        "paused_at_step": instance["current_step"],
    })


@mcp.tool()
def resume_workflow(workflow_id: str) -> str:
    """Resume a paused workflow.

    Args:
        workflow_id: ID of the workflow to resume

    Returns:
        JSON confirmation
    """
    instance = _active_workflows.get(workflow_id)
    if not instance:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    if instance["status"] != "paused":
        return json.dumps({"status": "error", "message": "Workflow is not paused"})

    instance["status"] = "running"
    if "paused_at" in instance:
        pause_duration = time.time() - instance["paused_at"]
        instance["started_at"] += pause_duration  # Adjust start time
        del instance["paused_at"]

    return json.dumps({
        "status": "resumed",
        "workflow_id": workflow_id,
        "current_step": instance["current_step"],
    })


@mcp.tool()
def cancel_workflow(workflow_id: str, reason: str = "") -> str:
    """Cancel an active workflow.

    Args:
        workflow_id: ID of the workflow to cancel
        reason: Reason for cancellation

    Returns:
        JSON confirmation
    """
    instance = _active_workflows.get(workflow_id)
    if not instance:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    instance["status"] = "cancelled"
    instance["cancelled_at"] = time.time()
    instance["cancel_reason"] = reason
    _workflow_history.append(instance)
    del _active_workflows[workflow_id]

    return json.dumps({
        "status": "cancelled",
        "workflow_id": workflow_id,
        "reason": reason,
    })


@mcp.tool()
def get_active_workflows() -> str:
    """Get all active workflows.

    Returns:
        JSON with all active workflows
    """
    active = []
    for wf_id, instance in _active_workflows.items():
        total_steps = len(instance["steps"])
        current_step = instance["current_step"]
        progress = (current_step / total_steps * 100) if total_steps > 0 else 0

        active.append({
            "id": wf_id,
            "name": instance["name"],
            "status": instance["status"],
            "progress": f"{progress:.0f}%",
            "current_step": current_step,
            "total_steps": total_steps,
            "elapsed_minutes": round((time.time() - instance["started_at"]) / 60, 1),
        })

    return json.dumps({
        "status": "success",
        "active_workflows": active,
        "total_active": len(active),
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
