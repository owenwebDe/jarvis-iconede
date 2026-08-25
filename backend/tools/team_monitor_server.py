"""Team Monitor MCP Server.

Provides real-time monitoring and health check tools for Jarvis
to proactively monitor agent status and report issues.
"""
from __future__ import annotations

import json
import logging
import time
from typing import List, Dict, Any, Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("team_monitor")
mcp = FastMCP("TeamMonitor")

# In-memory store for agent metrics (in production, use SQLite)
_agent_metrics: Dict[str, Dict[str, Any]] = {}
_task_history: List[Dict[str, Any]] = []


def _record_task(agent_name: str, task_id: str, status: str, duration: float = 0, error: str = ""):
    """Record task execution metrics."""
    if agent_name not in _agent_metrics:
        _agent_metrics[agent_name] = {
            "total_tasks": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration": 0,
            "last_task_time": 0,
            "consecutive_failures": 0,
        }

    metrics = _agent_metrics[agent_name]
    metrics["total_tasks"] += 1
    metrics["last_task_time"] = time.time()

    if status == "success":
        metrics["successful"] += 1
        metrics["consecutive_failures"] = 0
        # Update rolling average duration
        total = metrics["total_tasks"]
        metrics["avg_duration"] = ((metrics["avg_duration"] * (total - 1)) + duration) / total
    else:
        metrics["failed"] += 1
        metrics["consecutive_failures"] += 1

    _task_history.append({
        "agent": agent_name,
        "task_id": task_id,
        "status": status,
        "duration": duration,
        "error": error,
        "timestamp": time.time(),
    })


@mcp.tool()
def get_agent_health(agent_name: str) -> str:
    """Get health status and metrics for a specific agent.

    Args:
        agent_name: Name of the agent to check

    Returns:
        JSON with agent health metrics
    """
    metrics = _agent_metrics.get(agent_name, {
        "total_tasks": 0,
        "successful": 0,
        "failed": 0,
        "avg_duration": 0,
        "last_task_time": 0,
        "consecutive_failures": 0,
    })

    # Calculate health score (0-100)
    health_score = 100
    if metrics["total_tasks"] > 0:
        success_rate = metrics["successful"] / metrics["total_tasks"]
        health_score = int(success_rate * 100)

    # Determine health status
    if metrics["consecutive_failures"] >= 3:
        status = "critical"
        recommendation = "Agent has failed 3+ times consecutively. Consider restarting or checking configuration."
    elif metrics["consecutive_failures"] >= 2:
        status = "warning"
        recommendation = "Agent has failed 2+ times consecutively. Monitor closely."
    elif health_score < 70:
        status = "degraded"
        recommendation = "Agent success rate below 70%. May need attention."
    else:
        status = "healthy"
        recommendation = "Agent operating normally."

    # Check if agent has been inactive too long
    inactive_minutes = (time.time() - metrics["last_task_time"]) / 60 if metrics["last_task_time"] > 0 else None
    if inactive_minutes and inactive_minutes > 60:
        status = "idle"
        recommendation = f"Agent inactive for {int(inactive_minutes)} minutes."

    return json.dumps({
        "agent": agent_name,
        "health_score": health_score,
        "status": status,
        "recommendation": recommendation,
        "metrics": {
            "total_tasks": metrics["total_tasks"],
            "successful": metrics["successful"],
            "failed": metrics["failed"],
            "success_rate": f"{(metrics['successful'] / max(metrics['total_tasks'], 1)) * 100:.1f}%",
            "avg_duration_seconds": round(metrics["avg_duration"], 2),
            "consecutive_failures": metrics["consecutive_failures"],
            "inactive_minutes": round(inactive_minutes, 1) if inactive_minutes else None,
        },
    }, indent=2)


@mcp.tool()
def get_team_health_summary() -> str:
    """Get health summary for ALL agents in the team.

    Returns:
        JSON with team-wide health metrics and alerts
    """
    all_agents = [
        "LeadResearchAgent", "CreativeAgent", "OutreachAgent", "AdsAgent",
        "FinanceAgent", "ResearchAgent", "AudioReaderAgent", "CrawlStoriesAgent",
        "PersonalAgent", "IoTAgent", "MusicAgent", "WhatsAppAgent", "DemoBuilderAgent",
    ]

    agent_statuses = []
    alerts = []
    overall_score = 0

    for agent_name in all_agents:
        metrics = _agent_metrics.get(agent_name, {
            "total_tasks": 0, "successful": 0, "failed": 0,
            "consecutive_failures": 0, "last_task_time": 0,
        })

        # Calculate score
        score = 100
        if metrics["total_tasks"] > 0:
            score = int((metrics["successful"] / metrics["total_tasks"]) * 100)

        # Determine status
        if metrics["consecutive_failures"] >= 3:
            status = "critical"
            alerts.append(f"🚨 {agent_name}: {metrics['consecutive_failures']} consecutive failures!")
        elif metrics["consecutive_failures"] >= 2:
            status = "warning"
            alerts.append(f"⚠️ {agent_name}: {metrics['consecutive_failures']} consecutive failures")
        elif score < 70 and metrics["total_tasks"] > 5:
            status = "degraded"
        elif metrics["total_tasks"] == 0:
            status = "unused"
        else:
            status = "healthy"

        agent_statuses.append({
            "agent": agent_name,
            "status": status,
            "health_score": score,
            "total_tasks": metrics["total_tasks"],
        })

        overall_score += score

    # Calculate team average
    agents_with_data = len([a for a in agent_statuses if a["total_tasks"] > 0])
    team_avg = overall_score / max(len(all_agents), 1)

    return json.dumps({
        "team_health_score": round(team_avg, 1),
        "agents_total": len(all_agents),
        "agents_healthy": len([a for a in agent_statuses if a["status"] == "healthy"]),
        "agents_with_alerts": len(alerts),
        "alerts": alerts,
        "agent_details": agent_statuses,
    }, indent=2)


@mcp.tool()
def record_task_completion(
    agent_name: str,
    task_id: str,
    status: str,
    duration_seconds: float = 0,
    error_message: str = "",
) -> str:
    """Record task completion for metrics tracking.

    Args:
        agent_name: Name of the agent that completed the task
        task_id: Unique task identifier
        status: Task status ('success' or 'failed')
        duration_seconds: How long the task took (optional)
        error_message: Error details if failed (optional)

    Returns:
        JSON confirmation
    """
    _record_task(agent_name, task_id, status, duration_seconds, error_message)

    # Check if we need to raise an alert
    metrics = _agent_metrics.get(agent_name, {})
    if metrics.get("consecutive_failures", 0) >= 3:
        return json.dumps({
            "status": "recorded",
            "alert": True,
            "alert_message": f"🚨 CRITICAL: {agent_name} has failed {metrics['consecutive_failures']} times consecutively!",
            "recommendation": "Consider investigating the agent's configuration or dependencies.",
        })
    elif metrics.get("consecutive_failures", 0) >= 2:
        return json.dumps({
            "status": "recorded",
            "alert": True,
            "alert_message": f"⚠️ WARNING: {agent_name} has failed {metrics['consecutive_failures']} times consecutively.",
        })

    return json.dumps({"status": "recorded", "alert": False})


@mcp.tool()
def get_recent_task_history(limit: int = 20) -> str:
    """Get recent task execution history.

    Args:
        limit: Number of recent tasks to return (default 20)

    Returns:
        JSON with recent task history
    """
    recent = _task_history[-limit:] if _task_history else []
    recent.reverse()  # Most recent first

    return json.dumps({
        "total_tasks_recorded": len(_task_history),
        "showing": len(recent),
        "history": recent,
    }, indent=2)


@mcp.tool()
def check_system_resources() -> str:
    """Check system resources and health.

    Returns:
        JSON with system resource information
    """
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return json.dumps({
            "status": "success",
            "cpu_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": round(disk.percent, 1),
            },
            "alerts": _check_resource_alerts(cpu_percent, memory.percent, disk.percent),
        })
    except ImportError:
        return json.dumps({
            "status": "limited",
            "message": "psutil not installed - limited system info available",
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def _check_resource_alerts(cpu: float, memory: float, disk: float) -> List[str]:
    """Check for resource alerts."""
    alerts = []
    if cpu > 90:
        alerts.append(f"🚨 CRITICAL: CPU at {cpu}%!")
    elif cpu > 80:
        alerts.append(f"⚠️ WARNING: CPU at {cpu}%")

    if memory > 90:
        alerts.append(f"🚨 CRITICAL: Memory at {memory}%!")
    elif memory > 80:
        alerts.append(f"⚠️ WARNING: Memory at {memory}%")

    if disk > 90:
        alerts.append(f"🚨 CRITICAL: Disk at {disk}%!")
    elif disk > 80:
        alerts.append(f"⚠️ WARNING: Disk at {disk}%")

    return alerts


if __name__ == "__main__":
    mcp.run()
