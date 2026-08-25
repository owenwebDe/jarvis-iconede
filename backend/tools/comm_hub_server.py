"""Unified Communication Hub MCP Server.

Single inbox across WhatsApp, Email, LinkedIn, Instagram, and more.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional
from enum import Enum

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("comm_hub")
mcp = FastMCP("CommHub")


class Channel(Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    WEBSITE = "website"
    SLACK = "slack"
    TELEGRAM = "telegram"


class MessageStatus(Enum):
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"
    ESCALATED = "escalated"


# Message storage
_inbox: List[Dict[str, Any]] = []
_conversations: Dict[str, List[Dict[str, Any]]] = {}
_contact_index: Dict[str, Dict[str, Any]] = {}


def _add_message(
    channel: str,
    sender: str,
    sender_name: str,
    content: str,
    metadata: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Add a message to the unified inbox."""
    message_id = f"msg-{int(time.time())}-{len(_inbox)}"

    message = {
        "id": message_id,
        "channel": channel,
        "sender": sender,
        "sender_name": sender_name,
        "content": content,
        "status": MessageStatus.UNREAD.value,
        "timestamp": time.time(),
        "metadata": metadata or {},
    }

    _inbox.append(message)

    # Add to conversation thread
    conversation_key = f"{channel}:{sender}"
    if conversation_key not in _conversations:
        _conversations[conversation_key] = []
    _conversations[conversation_key].append(message)

    # Index contact
    if sender not in _contact_index:
        _contact_index[sender] = {
            "name": sender_name,
            "channels": [],
            "last_contact": time.time(),
            "message_count": 0,
        }
    _contact_index[sender]["last_contact"] = time.time()
    _contact_index[sender]["message_count"] += 1
    if channel not in _contact_index[sender]["channels"]:
        _contact_index[sender]["channels"].append(channel)

    return message


@mcp.tool()
def receive_message(
    channel: str,
    sender: str,
    sender_name: str,
    content: str,
    subject: str = "",
    metadata: str = "",
) -> str:
    """Receive a message from any channel into unified inbox.

    Args:
        channel: Source channel ('whatsapp', 'email', 'linkedin', etc.)
        sender: Sender identifier (phone, email, username)
        sender_name: Sender display name
        content: Message content
        subject: Email subject (optional)
        metadata: Additional metadata as JSON string

    Returns:
        JSON with message details
    """
    meta = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError:
            meta = {"raw": metadata}

    if subject:
        meta["subject"] = subject

    message = _add_message(channel, sender, sender_name, content, meta)

    return json.dumps({
        "status": "received",
        "message_id": message["id"],
        "channel": channel,
        "sender": sender_name,
        "conversation_count": len(_conversations.get(f"{channel}:{sender}", [])),
    })


@mcp.tool()
def get_unified_inbox(
    status: str = "",
    channel: str = "",
    limit: int = 20,
) -> str:
    """Get messages from unified inbox.

    Args:
        status: Filter by status ('unread', 'read', 'replied', 'archived')
        channel: Filter by channel
        limit: Max messages to return (default 20)

    Returns:
        JSON with inbox messages
    """
    messages = _inbox

    if status:
        messages = [m for m in messages if m["status"] == status]
    if channel:
        messages = [m for m in messages if m["channel"] == channel]

    # Get most recent
    messages = messages[-limit:]
    messages.reverse()

    # Count unread
    unread_count = len([m for m in _inbox if m["status"] == MessageStatus.UNREAD.value])

    return json.dumps({
        "status": "success",
        "messages": messages,
        "total": len(_inbox),
        "unread_count": unread_count,
        "showing": len(messages),
    })


@mcp.tool()
def get_conversation(channel: str, sender: str, limit: int = 50) -> str:
    """Get conversation thread with a specific contact.

    Args:
        channel: Channel name
        sender: Sender identifier
        limit: Max messages (default 50)

    Returns:
        JSON with conversation history
    """
    conversation_key = f"{channel}:{sender}"
    messages = _conversations.get(conversation_key, [])

    # Get most recent
    messages = messages[-limit:]
    messages.reverse()

    contact = _contact_index.get(sender, {})

    return json.dumps({
        "status": "success",
        "channel": channel,
        "sender": sender,
        "sender_name": contact.get("name", ""),
        "messages": messages,
        "total_messages": len(_conversations.get(conversation_key, [])),
    })


@mcp.tool()
def mark_message_read(message_id: str) -> str:
    """Mark a message as read.

    Args:
        message_id: ID of the message

    Returns:
        JSON confirmation
    """
    for msg in _inbox:
        if msg["id"] == message_id:
            msg["status"] = MessageStatus.READ.value
            return json.dumps({"status": "updated", "message_id": message_id, "new_status": "read"})

    return json.dumps({"status": "error", "message": "Message not found"})


@mcp.tool()
def mark_message_replied(message_id: str) -> str:
    """Mark a message as replied.

    Args:
        message_id: ID of the message

    Returns:
        JSON confirmation
    """
    for msg in _inbox:
        if msg["id"] == message_id:
            msg["status"] = MessageStatus.REPLIED.value
            return json.dumps({"status": "updated", "message_id": message_id, "new_status": "replied"})

    return json.dumps({"status": "error", "message": "Message not found"})


@mcp.tool()
def escalate_message(message_id: str, reason: str = "") -> str:
    """Escalate a message to Mr. Owen.

    Args:
        message_id: ID of the message
        reason: Reason for escalation

    Returns:
        JSON confirmation
    """
    for msg in _inbox:
        if msg["id"] == message_id:
            msg["status"] = MessageStatus.ESCALATED.value
            msg["metadata"]["escalation_reason"] = reason
            msg["metadata"]["escalated_at"] = time.time()
            return json.dumps({
                "status": "escalated",
                "message_id": message_id,
                "sender": msg["sender_name"],
                "channel": msg["channel"],
            })

    return json.dumps({"status": "error", "message": "Message not found"})


@mcp.tool()
def get_contact_index() -> str:
    """Get index of all contacts.

    Returns:
        JSON with contact index
    """
    contacts = []
    for sender, info in _contact_index.items():
        contacts.append({
            "sender": sender,
            "name": info["name"],
            "channels": info["channels"],
            "message_count": info["message_count"],
            "last_contact": info["last_contact"],
        })

    # Sort by last contact
    contacts.sort(key=lambda x: x["last_contact"], reverse=True)

    return json.dumps({
        "status": "success",
        "contacts": contacts,
        "total": len(contacts),
    })


@mcp.tool()
def search_messages(query: str, channel: str = "", limit: int = 20) -> str:
    """Search messages across all channels.

    Args:
        query: Search query
        channel: Filter by channel (optional)
        limit: Max results (default 20)

    Returns:
        JSON with matching messages
    """
    results = []
    query_lower = query.lower()

    for msg in _inbox:
        if channel and msg["channel"] != channel:
            continue
        if query_lower in msg["content"].lower() or query_lower in msg["sender_name"].lower():
            results.append(msg)

    results = results[-limit:]
    results.reverse()

    return json.dumps({
        "status": "success",
        "query": query,
        "results": results,
        "total_matches": len(results),
    })


@mcp.tool()
def get_channel_stats() -> str:
    """Get statistics for each channel.

    Returns:
        JSON with channel statistics
    """
    stats = {}
    for channel in Channel:
        channel_msgs = [m for m in _inbox if m["channel"] == channel.value]
        stats[channel.value] = {
            "total": len(channel_msgs),
            "unread": len([m for m in channel_msgs if m["status"] == "unread"]),
            "replied": len([m for m in channel_msgs if m["status"] == "replied"]),
            "escalated": len([m for m in channel_msgs if m["status"] == "escalated"]),
        }

    return json.dumps({
        "status": "success",
        "channel_stats": stats,
        "total_messages": len(_inbox),
        "total_unread": len([m for m in _inbox if m["status"] == "unread"]),
    })


@mcp.tool()
def get_priority_messages() -> str:
    """Get high-priority messages that need attention.

    Returns:
        JSON with priority messages
    """
    priority = []

    for msg in _inbox:
        if msg["status"] == MessageStatus.ESCALATED.value:
            priority.append({**msg, "priority": "high"})
        elif msg["status"] == MessageStatus.UNREAD.value:
            # Check if message is urgent based on content
            content_lower = msg["content"].lower()
            if any(word in content_lower for word in ["urgent", "asap", "immediately", "emergency"]):
                priority.append({**msg, "priority": "high"})
            else:
                priority.append({**msg, "priority": "normal"})

    # Sort by priority then timestamp
    priority.sort(key=lambda x: (0 if x["priority"] == "high" else 1, x["timestamp"]), reverse=True)

    return json.dumps({
        "status": "success",
        "priority_messages": priority[:10],
        "high_priority_count": len([m for m in priority if m["priority"] == "high"]),
    })


if __name__ == "__main__":
    mcp.run()
