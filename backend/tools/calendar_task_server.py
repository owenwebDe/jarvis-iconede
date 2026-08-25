"""Calendar & Task Management MCP Server.

Google Calendar integration, task management, reminders, and scheduling.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("calendar_task")
mcp = FastMCP("CalendarTask")


# Task storage
_tasks: List[Dict[str, Any]] = []
_events: List[Dict[str, Any]] = []
_reminders: List[Dict[str, Any]] = []


@mcp.tool()
def create_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: str = "",
    assignee: str = "Mr. Owen",
) -> str:
    """Create a new task.

    Args:
        title: Task title
        description: Task description
        priority: Priority ('low', 'medium', 'high', 'urgent')
        due_date: Due date (YYYY-MM-DD or 'tomorrow', 'next_week')
        assignee: Who is responsible

    Returns:
        JSON with task details
    """
    task = {
        "id": f"task-{int(time.time())}",
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending",
        "assignee": assignee,
        "created_at": time.time(),
        "due_date": _parse_date(due_date) if due_date else None,
    }
    _tasks.append(task)

    return json.dumps({
        "status": "created",
        "task": task,
    })


@mcp.tool()
def list_tasks(status: str = "", priority: str = "", limit: int = 20) -> str:
    """List tasks with optional filters.

    Args:
        status: Filter by status ('pending', 'in_progress', 'completed')
        priority: Filter by priority
        limit: Max tasks to return

    Returns:
        JSON with task list
    """
    tasks = _tasks
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    if priority:
        tasks = [t for t in tasks if t["priority"] == priority]

    # Sort by priority and due date
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    tasks.sort(key=lambda x: (priority_order.get(x["priority"], 4), x.get("due_date") or float("inf")))

    return json.dumps({
        "status": "success",
        "tasks": tasks[:limit],
        "total": len(tasks),
    })


@mcp.tool()
def complete_task(task_id: str) -> str:
    """Mark a task as completed.

    Args:
        task_id: Task ID

    Returns:
        JSON confirmation
    """
    for task in _tasks:
        if task["id"] == task_id:
            task["status"] = "completed"
            task["completed_at"] = time.time()
            return json.dumps({"status": "completed", "task_id": task_id})

    return json.dumps({"status": "error", "message": "Task not found"})


@mcp.tool()
def create_event(
    title: str,
    start_time: str,
    end_time: str = "",
    description: str = "",
    location: str = "",
    attendees: str = "",
) -> str:
    """Create a calendar event.

    Args:
        title: Event title
        start_time: Start time (ISO format or '2024-01-15 14:00')
        end_time: End time (optional, defaults to 1 hour)
        description: Event description
        location: Event location
        attendees: Comma-separated attendee emails

    Returns:
        JSON with event details
    """
    event = {
        "id": f"event-{int(time.time())}",
        "title": title,
        "start_time": start_time,
        "end_time": end_time or _add_hour(start_time),
        "description": description,
        "location": location,
        "attendees": [a.strip() for a in attendees.split(",") if a.strip()] if attendees else [],
        "created_at": time.time(),
    }
    _events.append(event)

    return json.dumps({
        "status": "created",
        "event": event,
    })


@mcp.tool()
def list_events(days: int = 7) -> str:
    """List upcoming events.

    Args:
        days: Number of days ahead to look

    Returns:
        JSON with event list
    """
    # For now, return all events (in production, filter by date)
    return json.dumps({
        "status": "success",
        "events": _events[-20:],
        "total": len(_events),
    })


@mcp.tool()
def set_reminder(
    title: str,
    remind_at: str,
    message: str = "",
) -> str:
    """Set a reminder.

    Args:
        title: Reminder title
        remind_at: When to remind (ISO format)
        message: Reminder message

    Returns:
        JSON confirmation
    """
    reminder = {
        "id": f"reminder-{int(time.time())}",
        "title": title,
        "remind_at": remind_at,
        "message": message,
        "created_at": time.time(),
        "triggered": False,
    }
    _reminders.append(reminder)

    return json.dumps({
        "status": "created",
        "reminder": reminder,
    })


@mcp.tool()
def get_upcoming_reminders() -> str:
    """Get upcoming reminders.

    Returns:
        JSON with reminders
    """
    untriggered = [r for r in _reminders if not r["triggered"]]
    return json.dumps({
        "status": "success",
        "reminders": untriggered,
        "total": len(untriggered),
    })


def _parse_date(date_str: str) -> str:
    """Parse relative date strings."""
    if date_str == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_str == "next_week":
        return (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
    return date_str


def _add_hour(time_str: str) -> str:
    """Add 1 hour to time string."""
    try:
        dt = datetime.fromisoformat(time_str.replace(" ", "T"))
        return (dt + timedelta(hours=1)).isoformat()
    except:
        return time_str


if __name__ == "__main__":
    mcp.run()
