"""IconEdge Meta Messenger & Social Engagement MCP Tool Server.

Exposes social engagement operations to FastAgent specialist agents:
- Outbound Messenger Direct Messages
- Facebook/Instagram Post Publishing
- Post Comment Public Replies
- Comment-to-Private-DM Lead Conversion
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import Context, FastMCP

sys.path.insert(0, str(Path(__file__).parent.parent))

from services import meta_messenger

logger = logging.getLogger("meta_messenger_server")
mcp = FastMCP("MetaMessengerMCP")


@mcp.tool()
def messenger_send(recipient_id: str, message_text: str) -> dict:
    """Send an outbound direct message to a prospect on Facebook/Instagram Messenger."""
    try:
        return meta_messenger.send_messenger_message(recipient_id=recipient_id, message_text=message_text)
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def page_post_publish(
    page_id: str,
    message: str,
    link_url: str = "",
    image_url: str = "",
) -> dict:
    """Publish a post or update to a Meta Page."""
    try:
        return meta_messenger.publish_page_post(
            page_id=page_id,
            message=message,
            link_url=link_url or None,
            image_url=image_url or None,
        )
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def comment_reply(comment_id: str, message_text: str) -> dict:
    """Post a public reply to a comment on a Meta Page post."""
    try:
        return meta_messenger.reply_to_comment(comment_id=comment_id, message_text=message_text)
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def comment_send_private_dm(comment_id: str, message_text: str) -> dict:
    """Send a private direct message to a user who commented on a Page post."""
    try:
        return meta_messenger.send_private_reply_to_comment(comment_id=comment_id, message_text=message_text)
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def messenger_process_inbound_dm(sender_id: str, message_text: str) -> dict:
    """Process an inbound direct message, qualify lead intent, log to database, and draft reply."""
    try:
        return meta_messenger.handle_inbound_dm(sender_id=sender_id, message_text=message_text)
    except Exception as exc:
        return {"error": str(exc)}


if __name__ == "__main__":
    mcp.run()
