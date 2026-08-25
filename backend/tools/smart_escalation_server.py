"""Smart Escalation Intelligence MCP Server.

Intelligent error handling with different responses based on severity,
auto-retry logic, and smart batching of minor issues.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional
from enum import Enum

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("smart_escalation")
mcp = FastMCP("SmartEscalation")


class SeverityLevel(Enum):
    LOW = "low"           # Auto-retry, batch into reports
    MEDIUM = "medium"     # Auto-retry once, then escalate
    HIGH = "high"         # Immediate escalation
    CRITICAL = "critical" # Immediate escalation + alert


# Escalation rules
ESCALATION_RULES = {
    # Agent failures
    "agent_timeout": {"severity": "medium", "auto_retry": True, "max_retries": 2},
    "agent_crash": {"severity": "high", "auto_retry": True, "max_retries": 1},
    "agent_stuck": {"severity": "medium", "auto_retry": True, "max_retries": 1},
    "agent_rate_limit": {"severity": "low", "auto_retry": True, "max_retries": 3},

    # MCP server failures
    "mcp_handshake_fail": {"severity": "medium", "auto_retry": True, "max_retries": 2},
    "mcp_tool_error": {"severity": "low", "auto_retry": True, "max_retries": 2},
    "mcp_connection_lost": {"severity": "medium", "auto_retry": True, "max_retries": 3},

    # Business logic
    "lead_save_failed": {"severity": "medium", "auto_retry": True, "max_retries": 1},
    "outreach_send_failed": {"severity": "high", "auto_retry": False, "max_retries": 0},
    "payment_error": {"severity": "critical", "auto_retry": False, "max_retries": 0},

    # System
    "database_error": {"severity": "critical", "auto_retry": False, "max_retries": 0},
    "memory_exceeded": {"severity": "critical", "auto_retry": False, "max_retries": 0},
    "disk_full": {"severity": "critical", "auto_retry": False, "max_retries": 0},
}

# Track escalation history
_escalation_history: List[Dict[str, Any]] = []
_retry_tracker: Dict[str, int] = {}  # error_key -> retry_count
_pending_escalations: List[Dict[str, Any]] = []
_batched_issues: List[Dict[str, Any]] = []


def _get_severity(error_type: str) -> SeverityLevel:
    """Get severity level for an error type."""
    rule = ESCALATION_RULES.get(error_type, {"severity": "medium"})
    return SeverityLevel(rule["severity"])


def _should_auto_retry(error_type: str) -> bool:
    """Check if we should auto-retry this error."""
    rule = ESCALATION_RULES.get(error_type, {"auto_retry": True})
    retry_count = _retry_tracker.get(error_type, 0)
    return rule["auto_retry"] and retry_count < rule["max_retries"]


@mcp.tool()
def handle_error(
    error_type: str,
    error_message: str,
    context: str = "",
    agent_name: str = "",
) -> str:
    """Handle an error with smart escalation logic.

    Automatically determines severity, retries if appropriate, and
    escalates to Mr. Owen only when necessary.

    Args:
        error_type: Type of error (e.g., 'agent_timeout', 'mcp_tool_error')
        error_message: Detailed error message
        context: Additional context about what was happening
        agent_name: Name of agent that encountered the error (optional)

    Returns:
        JSON with handling decision
    """
    severity = _get_severity(error_type)
    should_retry = _should_auto_retry(error_type)
    retry_count = _retry_tracker.get(error_type, 0)

    # Record the error
    error_record = {
        "error_type": error_type,
        "message": error_message,
        "context": context,
        "agent": agent_name,
        "severity": severity.value,
        "timestamp": time.time(),
        "retry_count": retry_count,
    }
    _escalation_history.append(error_record)

    # Decision logic
    decision = ""
    action_taken = ""

    if should_retry:
        _retry_tracker[error_type] = retry_count + 1
        decision = "auto_retry"
        action_taken = f"Retrying (attempt {retry_count + 1}/{ESCALATION_RULES.get(error_type, {}).get('max_retries', 2)})"
    elif severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
        decision = "escalate_immediately"
        _pending_escalations.append(error_record)
        action_taken = "Escalating to Mr. Owen immediately"
    elif severity == SeverityLevel.MEDIUM:
        decision = "escalate_once"
        _pending_escalations.append(error_record)
        action_taken = "Adding to next status report"
    else:
        decision = "batch"
        _batched_issues.append(error_record)
        action_taken = "Batching into periodic report"

    # Auto-recovery suggestions
    recovery_suggestions = _get_recovery_suggestions(error_type)

    return json.dumps({
        "status": "handled",
        "severity": severity.value,
        "decision": decision,
        "action_taken": action_taken,
        "retry_count": _retry_tracker.get(error_type, 0),
        "recovery_suggestions": recovery_suggestions,
    })


@mcp.tool()
def get_pending_escalations() -> str:
    """Get all pending issues that need escalation to Mr. Owen.

    Returns:
        JSON with pending escalations grouped by severity
    """
    # Group by severity
    by_severity = {"critical": [], "high": [], "medium": [], "low": []}
    for issue in _pending_escalations:
        severity = issue.get("severity", "medium")
        if severity in by_severity:
            by_severity[severity].append(issue)

    return json.dumps({
        "status": "success",
        "total_pending": len(_pending_escalations),
        "by_severity": {
            k: {"count": len(v), "issues": v[:3]}  # Limit to 3 per severity
            for k, v in by_severity.items()
        },
        "should_alert_now": len(by_severity["critical"]) > 0 or len(by_severity["high"]) > 0,
    }, indent=2)


@mcp.tool()
def get_batched_issues_report() -> str:
    """Get a batched report of minor issues for periodic review.

    Returns:
        JSON with grouped minor issues
    """
    # Group by error type
    by_type = {}
    for issue in _batched_issues:
        error_type = issue.get("error_type", "unknown")
        if error_type not in by_type:
            by_type[error_type] = {"count": 0, "last_occurrence": None, "samples": []}
        by_type[error_type]["count"] += 1
        by_type[error_type]["last_occurrence"] = issue["timestamp"]
        if len(by_type[error_type]["samples"]) < 2:
            by_type[error_type]["samples"].append(issue)

    return json.dumps({
        "status": "success",
        "total_batched": len(_batched_issues),
        "by_type": by_type,
        "report_generated": time.time(),
    }, indent=2)


@mcp.tool()
def clear_escalation_queue() -> str:
    """Clear the escalation queue after issues have been addressed.

    Returns:
        JSON confirmation
    """
    cleared_count = len(_pending_escalations)
    _pending_escalations.clear()
    _batched_issues.clear()
    _retry_tracker.clear()

    return json.dumps({
        "status": "cleared",
        "escalations_cleared": cleared_count,
    })


@mcp.tool()
def get_escalation_stats() -> str:
    """Get escalation statistics and trends.

    Returns:
        JSON with escalation metrics
    """
    # Calculate stats
    total_errors = len(_escalation_history)
    by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    by_agent = {}
    by_type = {}

    for record in _escalation_history:
        by_severity[record.get("severity", "medium")] = by_severity.get(record.get("severity", "medium"), 0) + 1

        agent = record.get("agent", "unknown")
        by_agent[agent] = by_agent.get(agent, 0) + 1

        error_type = record.get("error_type", "unknown")
        by_type[error_type] = by_type.get(error_type, 0) + 1

    # Most problematic agents
    top_agents = sorted(by_agent.items(), key=lambda x: x[1], reverse=True)[:5]

    # Most common errors
    top_errors = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]

    return json.dumps({
        "status": "success",
        "total_errors": total_errors,
        "by_severity": by_severity,
        "top_problem_agents": [{"agent": a, "errors": c} for a, c in top_agents],
        "most_common_errors": [{"error": e, "count": c} for e, c in top_errors],
        "pending_escalations": len(_pending_escalations),
        "batched_issues": len(_batched_issues),
    }, indent=2)


def _get_recovery_suggestions(error_type: str) -> List[str]:
    """Get recovery suggestions for an error type."""
    suggestions = {
        "agent_timeout": [
            "Check if agent's MCP servers are responsive",
            "Verify network connectivity",
            "Consider increasing timeout in fastagent.config.yaml",
        ],
        "agent_crash": [
            "Check agent logs for detailed error",
            "Verify agent dependencies are installed",
            "Restart the agent process",
        ],
        "mcp_tool_error": [
            "Check MCP server logs",
            "Verify API keys and credentials",
            "Test the specific tool manually",
        ],
        "rate_limit": [
            "Implement exponential backoff",
            "Reduce request frequency",
            "Consider upgrading API plan",
        ],
    }

    return suggestions.get(error_type, [
        "Check logs for detailed error information",
        "Verify system resources are adequate",
        "Contact support if issue persists",
    ])


if __name__ == "__main__":
    mcp.run()
