"""Advanced Workflow Engine MCP Server.

Conditional logic, parallel execution, approval gates, and rollback.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional
from enum import Enum

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("advanced_workflow")
mcp = FastMCP("AdvancedWorkflow")


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


# Active workflows
_workflows: Dict[str, Dict[str, Any]] = {}
_workflow_history: List[Dict[str, Any]] = []
_approval_requests: List[Dict[str, Any]] = []


@mcp.tool()
def create_workflow(
    name: str,
    steps: str,
    description: str = "",
    auto_advance: bool = True,
) -> str:
    """Create a new advanced workflow with conditional logic.

    Args:
        name: Workflow name
        steps: JSON array of step definitions
        description: Workflow description
        auto_advance: Auto-advance when steps complete

    Returns:
        JSON with workflow details
    """
    workflow_id = f"wf-{uuid.uuid4().hex[:8]}"

    try:
        steps_list = json.loads(steps) if isinstance(steps, str) else steps
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid steps JSON"})

    workflow = {
        "id": workflow_id,
        "name": name,
        "description": description,
        "steps": steps_list,
        "current_step": 0,
        "status": "created",
        "auto_advance": auto_advance,
        "created_at": time.time(),
        "context": {},
        "step_results": [],
    }

    _workflows[workflow_id] = workflow

    return json.dumps({
        "status": "created",
        "workflow_id": workflow_id,
        "name": name,
        "total_steps": len(steps_list),
    })


@mcp.tool()
def start_workflow(workflow_id: str, context: str = "") -> str:
    """Start a workflow.

    Args:
        workflow_id: Workflow ID
        context: Initial context as JSON

    Returns:
        JSON confirmation
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    workflow["status"] = "running"
    workflow["started_at"] = time.time()

    if context:
        try:
            workflow["context"] = json.loads(context)
        except json.JSONDecodeError:
            workflow["context"] = {"raw": context}

    # Get first step
    first_step = workflow["steps"][0] if workflow["steps"] else None

    return json.dumps({
        "status": "started",
        "workflow_id": workflow_id,
        "first_step": first_step,
    })


@mcp.tool()
def advance_workflow(
    workflow_id: str,
    result: str = "success",
    output: str = "",
) -> str:
    """Advance workflow to next step.

    Args:
        workflow_id: Workflow ID
        result: Step result ('success', 'failed', 'skipped')
        output: Step output data

    Returns:
        JSON with next step or completion
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    current_idx = workflow["current_step"]
    steps = workflow["steps"]

    # Record step result
    workflow["step_results"].append({
        "step_index": current_idx,
        "result": result,
        "output": output,
        "timestamp": time.time(),
    })

    # Update context with output
    if output:
        try:
            output_data = json.loads(output)
            workflow["context"].update(output_data)
        except json.JSONDecodeError:
            workflow["context"][f"step_{current_idx}_output"] = output

    # Check for failure
    if result == "failed":
        workflow["status"] = "failed"
        workflow["failed_at"] = time.time()
        _workflow_history.append(workflow.copy())
        return json.dumps({
            "status": "failed",
            "workflow_id": workflow_id,
            "failed_step": current_idx,
        })

    # Move to next step
    workflow["current_step"] += 1

    # Check if complete
    if workflow["current_step"] >= len(steps):
        workflow["status"] = "completed"
        workflow["completed_at"] = time.time()
        _workflow_history.append(workflow.copy())
        return json.dumps({
            "status": "completed",
            "workflow_id": workflow_id,
            "duration_seconds": round(workflow["completed_at"] - workflow["started_at"], 1),
        })

    # Get next step
    next_step = steps[workflow["current_step"]]

    # Check for conditional logic
    if "condition" in next_step:
        condition = next_step["condition"]
        if not _evaluate_condition(condition, workflow["context"]):
            # Skip this step
            workflow["step_results"].append({
                "step_index": workflow["current_step"],
                "result": "skipped",
                "output": "Condition not met",
                "timestamp": time.time(),
            })
            workflow["current_step"] += 1

            # Check if we need to jump
            if "false_next" in next_step:
                # Find the step with that label
                for i, s in enumerate(steps):
                    if s.get("label") == next_step["false_next"]:
                        workflow["current_step"] = i
                        break

            next_step = steps[workflow["current_step"]] if workflow["current_step"] < len(steps) else None

    # Check for approval gate
    if next_step and next_step.get("type") == "approval":
        workflow["status"] = "waiting_approval"
        _approval_requests.append({
            "workflow_id": workflow_id,
            "step": next_step,
            "requested_at": time.time(),
        })
        return json.dumps({
            "status": "waiting_approval",
            "workflow_id": workflow_id,
            "approval_needed": next_step.get("description", ""),
        })

    # Check for parallel execution
    if next_step and next_step.get("type") == "parallel":
        return json.dumps({
            "status": "parallel_step",
            "workflow_id": workflow_id,
            "parallel_tasks": next_step.get("tasks", []),
        })

    return json.dumps({
        "status": "advanced",
        "workflow_id": workflow_id,
        "current_step": workflow["current_step"],
        "total_steps": len(steps),
        "next_step": next_step,
        "progress": f"{(workflow['current_step'] / len(steps) * 100):.0f}%",
    })


@mcp.tool()
def approve_workflow_step(workflow_id: str, approved: bool = True, notes: str = "") -> str:
    """Approve or reject a workflow step.

    Args:
        workflow_id: Workflow ID
        approved: Whether approved
        notes: Approval notes

    Returns:
        JSON confirmation
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    # Remove from approval queue
    global _approval_requests
    _approval_requests = [r for r in _approval_requests if r["workflow_id"] != workflow_id]

    if not approved:
        workflow["status"] = "failed"
        workflow["failed_at"] = time.time()
        return json.dumps({
            "status": "rejected",
            "workflow_id": workflow_id,
            "notes": notes,
        })

    # Resume workflow
    workflow["status"] = "running"
    workflow["context"]["approval_notes"] = notes

    return json.dumps({
        "status": "approved",
        "workflow_id": workflow_id,
    })


@mcp.tool()
def rollback_workflow(workflow_id: str, to_step: int = 0) -> str:
    """Rollback workflow to a previous step.

    Args:
        workflow_id: Workflow ID
        to_step: Step index to rollback to

    Returns:
        JSON confirmation
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    # Mark rolled back steps
    for i in range(to_step, workflow["current_step"]):
        if i < len(workflow["step_results"]):
            workflow["step_results"][i]["result"] = "rolled_back"

    workflow["current_step"] = to_step
    workflow["status"] = "running"

    return json.dumps({
        "status": "rolled_back",
        "workflow_id": workflow_id,
        "rolled_back_to": to_step,
    })


@mcp.tool()
def pause_workflow(workflow_id: str) -> str:
    """Pause a running workflow.

    Args:
        workflow_id: Workflow ID

    Returns:
        JSON confirmation
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    workflow["status"] = "paused"
    workflow["paused_at"] = time.time()

    return json.dumps({"status": "paused", "workflow_id": workflow_id})


@mcp.tool()
def resume_workflow(workflow_id: str) -> str:
    """Resume a paused workflow.

    Args:
        workflow_id: Workflow ID

    Returns:
        JSON confirmation
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    workflow["status"] = "running"
    if "paused_at" in workflow:
        del workflow["paused_at"]

    return json.dumps({"status": "resumed", "workflow_id": workflow_id})


@mcp.tool()
def get_workflow_status(workflow_id: str) -> str:
    """Get workflow status.

    Args:
        workflow_id: Workflow ID

    Returns:
        JSON with workflow status
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return json.dumps({"status": "error", "message": "Workflow not found"})

    progress = (workflow["current_step"] / len(workflow["steps"]) * 100) if workflow["steps"] else 0

    return json.dumps({
        "status": "success",
        "workflow_id": workflow_id,
        "name": workflow["name"],
        "workflow_status": workflow["status"],
        "current_step": workflow["current_step"],
        "total_steps": len(workflow["steps"]),
        "progress": f"{progress:.0f}%",
        "step_results": workflow["step_results"],
        "context": workflow["context"],
    }, indent=2)


@mcp.tool()
def get_pending_approvals() -> str:
    """Get all pending approval requests.

    Returns:
        JSON with pending approvals
    """
    return json.dumps({
        "status": "success",
        "pending": _approval_requests,
        "total": len(_approval_requests),
    })


@mcp.tool()
def list_active_workflows() -> str:
    """List all active workflows.

    Returns:
        JSON with active workflows
    """
    active = []
    for wf_id, wf in _workflows.items():
        if wf["status"] in ["running", "paused", "waiting_approval"]:
            active.append({
                "id": wf_id,
                "name": wf["name"],
                "status": wf["status"],
                "current_step": wf["current_step"],
                "total_steps": len(wf["steps"]),
            })

    return json.dumps({
        "status": "success",
        "active_workflows": active,
        "total": len(active),
    })


def _evaluate_condition(condition: str, context: Dict[str, Any]) -> bool:
    """Evaluate a condition against context."""
    # Simple condition evaluation
    # In production, use a proper expression parser
    try:
        # Handle simple comparisons
        if ">" in condition:
            parts = condition.split(">")
            key = parts[0].strip()
            value = float(parts[1].strip())
            return context.get(key, 0) > value
        elif "<" in condition:
            parts = condition.split("<")
            key = parts[0].strip()
            value = float(parts[1].strip())
            return context.get(key, 0) < value
        elif "==" in condition:
            parts = condition.split("==")
            key = parts[0].strip()
            value = parts[1].strip().strip('"').strip("'")
            return str(context.get(key, "")) == value
        elif "contains" in condition:
            parts = condition.split("contains")
            key = parts[0].strip()
            value = parts[1].strip().strip('"').strip("'")
            return value in str(context.get(key, ""))
    except Exception:
        pass

    return True  # Default to true if can't evaluate


if __name__ == "__main__":
    mcp.run()
