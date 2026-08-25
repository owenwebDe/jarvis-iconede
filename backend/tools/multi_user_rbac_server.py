"""Multi-User RBAC MCP Server.

Role-based access control for team members with different permissions.
"""
from __future__ import annotations

import json
import logging
import time
import hashlib
import secrets
from typing import Dict, List, Any, Optional
from enum import Enum

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("multi_user_rbac")
mcp = FastMCP("MultiUserRBAC")


class Role(Enum):
    ADMIN = "admin"           # Full access
    MANAGER = "manager"       # Most access, no financial settings
    SALES = "sales"           # Leads and outreach only
    MARKETING = "marketing"   # Campaigns and creative only
    VIEWER = "viewer"         # Read-only access


# Permission matrix
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        "leads": ["read", "write", "delete"],
        "campaigns": ["read", "write", "delete"],
        "outreach": ["read", "write", "delete"],
        "finance": ["read", "write"],
        "settings": ["read", "write"],
        "users": ["read", "write", "delete"],
        "reports": ["read", "export"],
    },
    Role.MANAGER: {
        "leads": ["read", "write"],
        "campaigns": ["read", "write"],
        "outreach": ["read", "write"],
        "finance": ["read"],
        "settings": ["read"],
        "users": ["read"],
        "reports": ["read", "export"],
    },
    Role.SALES: {
        "leads": ["read", "write"],
        "campaigns": ["read"],
        "outreach": ["read", "write"],
        "finance": [],
        "settings": [],
        "users": [],
        "reports": ["read"],
    },
    Role.MARKETING: {
        "leads": ["read"],
        "campaigns": ["read", "write"],
        "outreach": ["read"],
        "finance": [],
        "settings": [],
        "users": [],
        "reports": ["read"],
    },
    Role.VIEWER: {
        "leads": ["read"],
        "campaigns": ["read"],
        "outreach": ["read"],
        "finance": [],
        "settings": [],
        "users": [],
        "reports": ["read"],
    },
}

# User storage (in production, use SQLite)
_users: Dict[str, Dict[str, Any]] = {
    "mr-owen": {
        "id": "mr-owen",
        "name": "Mr. Owen",
        "email": "owen@iconedge.com",
        "role": Role.ADMIN.value,
        "created_at": time.time(),
        "last_login": time.time(),
        "active": True,
    }
}

_sessions: Dict[str, Dict[str, Any]] = {}
_audit_log: List[Dict[str, Any]] = []


def _hash_password(password: str) -> str:
    """Hash password with salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash."""
    salt, hashed = stored.split(":")
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed


def _log_audit(user_id: str, action: str, resource: str, details: str = ""):
    """Log audit event."""
    _audit_log.append({
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "details": details,
        "timestamp": time.time(),
    })
    if len(_audit_log) > 10000:
        _audit_log.pop(0)


@mcp.tool()
def create_user(
    user_id: str,
    name: str,
    email: str,
    password: str,
    role: str,
) -> str:
    """Create a new user account.

    Args:
        user_id: Unique user identifier
        name: Full name
        email: Email address
        password: Password (will be hashed)
        role: User role ('admin', 'manager', 'sales', 'marketing', 'viewer')

    Returns:
        JSON confirmation
    """
    if user_id in _users:
        return json.dumps({"status": "error", "message": "User already exists"})

    if role not in [r.value for r in Role]:
        return json.dumps({"status": "error", "message": f"Invalid role: {role}"})

    _users[user_id] = {
        "id": user_id,
        "name": name,
        "email": email,
        "password": _hash_password(password),
        "role": role,
        "created_at": time.time(),
        "last_login": None,
        "active": True,
    }

    _log_audit("system", "user_created", "users", f"Created user {user_id} with role {role}")

    return json.dumps({
        "status": "created",
        "user_id": user_id,
        "role": role,
    })


@mcp.tool()
def authenticate_user(user_id: str, password: str) -> str:
    """Authenticate a user and create session.

    Args:
        user_id: User identifier
        password: Password

    Returns:
        JSON with session token
    """
    user = _users.get(user_id)
    if not user or not user.get("active"):
        return json.dumps({"status": "error", "message": "Invalid credentials"})

    if not _verify_password(password, user["password"]):
        return json.dumps({"status": "error", "message": "Invalid credentials"})

    # Create session
    session_token = secrets.token_hex(32)
    _sessions[session_token] = {
        "user_id": user_id,
        "role": user["role"],
        "created_at": time.time(),
        "expires_at": time.time() + 86400,  # 24 hours
    }

    user["last_login"] = time.time()
    _log_audit(user_id, "login", "session", "Successful login")

    return json.dumps({
        "status": "authenticated",
        "session_token": session_token,
        "user_id": user_id,
        "role": user["role"],
        "expires_in": 86400,
    })


@mcp.tool()
def check_permission(
    session_token: str,
    resource: str,
    action: str,
) -> str:
    """Check if user has permission for an action.

    Args:
        session_token: Active session token
        resource: Resource type ('leads', 'campaigns', etc.)
        action: Action type ('read', 'write', 'delete')

    Returns:
        JSON with permission check result
    """
    session = _sessions.get(session_token)
    if not session or time.time() > session["expires_at"]:
        return json.dumps({"status": "error", "message": "Invalid or expired session"})

    role = Role(session["role"])
    permissions = ROLE_PERMISSIONS.get(role, {})
    allowed = action in permissions.get(resource, [])

    return json.dumps({
        "status": "success",
        "allowed": allowed,
        "user_id": session["user_id"],
        "role": session["role"],
        "resource": resource,
        "action": action,
    })


@mcp.tool()
def get_user_profile(session_token: str) -> str:
    """Get user profile information.

    Args:
        session_token: Active session token

    Returns:
        JSON with user profile
    """
    session = _sessions.get(session_token)
    if not session or time.time() > session["expires_at"]:
        return json.dumps({"status": "error", "message": "Invalid or expired session"})

    user = _users.get(session["user_id"])
    if not user:
        return json.dumps({"status": "error", "message": "User not found"})

    return json.dumps({
        "status": "success",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "last_login": user["last_login"],
        },
        "permissions": ROLE_PERMISSIONS.get(Role(user["role"]), {}),
    })


@mcp.tool()
def list_users() -> str:
    """List all users (admin only).

    Returns:
        JSON with user list
    """
    users = []
    for uid, user in _users.items():
        users.append({
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "active": user["active"],
            "last_login": user["last_login"],
        })

    return json.dumps({
        "status": "success",
        "users": users,
        "total": len(users),
    })


@mcp.tool()
def update_user_role(
    user_id: str,
    new_role: str,
    updated_by: str,
) -> str:
    """Update a user's role (admin only).

    Args:
        user_id: User to update
        new_role: New role to assign
        updated_by: ID of admin making the change

    Returns:
        JSON confirmation
    """
    if user_id not in _users:
        return json.dumps({"status": "error", "message": "User not found"})

    if new_role not in [r.value for r in Role]:
        return json.dumps({"status": "error", "message": f"Invalid role: {new_role}"})

    old_role = _users[user_id]["role"]
    _users[user_id]["role"] = new_role

    _log_audit(updated_by, "role_changed", "users", f"Changed {user_id} from {old_role} to {new_role}")

    return json.dumps({
        "status": "updated",
        "user_id": user_id,
        "old_role": old_role,
        "new_role": new_role,
    })


@mcp.tool()
def deactivate_user(user_id: str, deactivated_by: str) -> str:
    """Deactivate a user account (admin only).

    Args:
        user_id: User to deactivate
        deactivated_by: ID of admin making the change

    Returns:
        JSON confirmation
    """
    if user_id not in _users:
        return json.dumps({"status": "error", "message": "User not found"})

    _users[user_id]["active"] = False
    _log_audit(deactivated_by, "user_deactivated", "users", f"Deactivated user {user_id}")

    return json.dumps({
        "status": "deactivated",
        "user_id": user_id,
    })


@mcp.tool()
def get_audit_log(limit: int = 50, user_id: str = "") -> str:
    """Get audit log entries.

    Args:
        limit: Number of entries to return (default 50)
        user_id: Filter by user ID (optional)

    Returns:
        JSON with audit log
    """
    logs = _audit_log
    if user_id:
        logs = [l for l in logs if l["user_id"] == user_id]

    logs = logs[-limit:]
    logs.reverse()

    return json.dumps({
        "status": "success",
        "entries": logs,
        "total": len(_audit_log),
    })


if __name__ == "__main__":
    mcp.run()
