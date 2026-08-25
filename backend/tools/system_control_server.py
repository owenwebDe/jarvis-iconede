"""System Control FastMCP Server.

Exposes tools for Jarvis to access and interact with the full Windows computer:
- Reading any file or browsing directories (Safe reads)
- Inspecting system specs, disk drives, and running processes
- Executing PowerShell commands (Permission-gated for modifying/privileged operations)
- Writing or creating files anywhere on the system (Permission-gated)
- Launching desktop applications (Permission-gated)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Allow imports from backend/
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from services.system_control import get_system_control_service  # noqa: E402

logger = logging.getLogger("system_control_server")
mcp = FastMCP("SystemControlService")


@mcp.tool()
def system_get_telemetry() -> str:
    """Get full Windows system telemetry (OS, CPU, RAM, disk drives, home directories)."""
    service = get_system_control_service()
    data = service.get_telemetry()
    return json.dumps(data, indent=2)


@mcp.tool()
def system_list_processes(max_count: int = 40) -> str:
    """List currently running Windows processes with PID and memory consumption."""
    service = get_system_control_service()
    processes = service.list_processes(max_count=max_count)
    return json.dumps({"count": len(processes), "processes": processes}, indent=2)


@mcp.tool()
def system_read_file(file_path: str, max_bytes: int = 50000) -> str:
    """Read contents of any file on the PC (e.g. Desktop, Documents, C:\\...).

    Safe read-only operation.

    Args:
        file_path: Path to the target file.
        max_bytes: Maximum number of characters/bytes to return (default 50,000).
    """
    service = get_system_control_service()
    res = service.read_file(file_path=file_path, max_bytes=max_bytes)
    return json.dumps(res, indent=2)


@mcp.tool()
def system_list_directory(dir_path: str, include_hidden: bool = False) -> str:
    """List files, folders, and sizes in any directory on the PC.

    Safe read-only operation.

    Args:
        dir_path: Path to the directory (e.g. 'C:\\Users\\Admin\\Desktop').
        include_hidden: Whether to include hidden files (default False).
    """
    service = get_system_control_service()
    res = service.list_directory(dir_path=dir_path, include_hidden=include_hidden)
    return json.dumps(res, indent=2)


@mcp.tool()
def system_write_file(
    file_path: str,
    content: str,
    reason: str,
    user_confirmation: bool = False,
) -> str:
    """Write or overwrite a file anywhere on the PC.

    CRITICAL SAFETY REQUIREMENT: You MUST obtain user confirmation and pass
    user_confirmation=True before modifying any file on their computer.

    Args:
        file_path: Path where the file should be saved.
        content: The text/code content to write.
        reason: Explanation of what this file is for.
        user_confirmation: Set to True ONLY after explicit user consent.
    """
    service = get_system_control_service()
    res = service.write_file(
        file_path=file_path,
        content=content,
        user_confirmation=user_confirmation,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def system_execute_command(
    command: str,
    reason: str,
    working_dir: str = "",
    user_confirmation: bool = False,
) -> str:
    """Execute a PowerShell command on the Windows PC.

    CRITICAL SAFETY REQUIREMENT: Modifying or destructive commands (file deletion,
    process termination, system setting changes) require user_confirmation=True.

    Args:
        command: The PowerShell command to run.
        reason: Clear explanation of what this command does and why it is needed.
        working_dir: Working directory (defaults to user home directory if blank).
        user_confirmation: Must be True if this is a modifying command with human approval.
    """
    service = get_system_control_service()
    res = service.execute_command(
        command=command,
        working_dir=working_dir or None,
        user_confirmation=user_confirmation,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def system_launch_app(
    app_name_or_path: str,
    reason: str,
    user_confirmation: bool = False,
) -> str:
    """Launch a desktop application on Windows.

    Args:
        app_name_or_path: Name of the application (e.g. 'notepad', 'chrome', 'code') or full exe path.
        reason: Why the application is being opened.
        user_confirmation: Set to True after obtaining user consent.
    """
    service = get_system_control_service()
    res = service.launch_app(
        app_name_or_path=app_name_or_path,
        user_confirmation=user_confirmation,
    )
    return json.dumps(res, indent=2)


if __name__ == "__main__":
    mcp.run()
