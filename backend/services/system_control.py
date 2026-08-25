"""System Control Service for Windows.

Provides capabilities for Jarvis to interact with the entire PC:
- Running PowerShell and CMD commands
- Reading and writing files across all drives (Desktop, Documents, Downloads, etc.)
- Process inspection, system performance (CPU/RAM/Disk), and hardware telemetry
- Application launching and process management
- Security tiering with human permission verification for modifying actions
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("system_control")


@dataclass
class SystemTelemetry:
    os_name: str
    os_version: str
    node_name: str
    architecture: str
    processor: str
    python_version: str
    user_home: str
    current_time: str
    drives: List[Dict[str, Any]]


class SystemControlService:
    """Service providing full Windows system access with safe read & gated modifying operations."""

    def __init__(self):
        self.user_home = Path.home()

    def get_telemetry(self) -> Dict[str, Any]:
        """Collect high-level Windows system telemetry."""
        drives = []
        if platform.system() == "Windows":
            import string
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    try:
                        total, used, free = shutil.disk_usage(drive_path)
                        drives.append({
                            "drive": drive_path,
                            "total_gb": round(total / (1024**3), 2),
                            "used_gb": round(used / (1024**3), 2),
                            "free_gb": round(free / (1024**3), 2),
                        })
                    except Exception:
                        pass

        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "user_home": str(self.user_home),
            "desktop_dir": str(self.user_home / "Desktop"),
            "documents_dir": str(self.user_home / "Documents"),
            "downloads_dir": str(self.user_home / "Downloads"),
            "drives": drives,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def list_processes(self, max_count: int = 50) -> List[Dict[str, Any]]:
        """List running Windows processes using tasklist."""
        processes = []
        try:
            res = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                check=False,
            )
            for line in res.stdout.strip().splitlines()[:max_count]:
                parts = [p.strip(' "') for p in line.split('","')]
                if len(parts) >= 5:
                    processes.append({
                        "name": parts[0],
                        "pid": parts[1],
                        "session": parts[2],
                        "session_num": parts[3],
                        "mem_usage": parts[4],
                    })
        except Exception as e:
            logger.warning(f"Failed to list processes: {e}")
        return processes

    def read_file(self, file_path: str, max_bytes: int = 50000) -> Dict[str, Any]:
        """Read any file on the PC."""
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return {"status": "error", "message": f"File '{file_path}' does not exist."}
        if path.is_dir():
            return {"status": "error", "message": f"'{file_path}' is a directory, not a file."}

        try:
            size = path.stat().st_size
            content = path.read_text(encoding="utf-8", errors="replace")
            truncated = False
            if len(content) > max_bytes:
                content = content[:max_bytes]
                truncated = True
            return {
                "status": "success",
                "file_path": str(path),
                "size_bytes": size,
                "truncated": truncated,
                "content": content,
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to read '{file_path}': {e}"}

    def write_file(
        self,
        file_path: str,
        content: str,
        user_confirmation: bool = False,
    ) -> Dict[str, Any]:
        """Write content to any file on the PC.

        STRICT SAFETY: Requires user_confirmation=True for modifying files.
        """
        if not user_confirmation:
            return {
                "status": "permission_denied",
                "message": f"Modifying or creating '{file_path}' requires explicit user confirmation. Set user_confirmation=True after asking the user.",
            }

        path = Path(file_path).expanduser().resolve()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return {
                "status": "success",
                "file_path": str(path),
                "bytes_written": len(content.encode("utf-8")),
                "message": f"Successfully wrote file '{path}'.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to write '{file_path}': {e}"}

    def list_directory(
        self,
        dir_path: str,
        include_hidden: bool = False,
    ) -> Dict[str, Any]:
        """List files and folders in any directory on the PC."""
        path = Path(dir_path).expanduser().resolve()
        if not path.exists():
            return {"status": "error", "message": f"Directory '{dir_path}' does not exist."}
        if not path.is_dir():
            return {"status": "error", "message": f"'{dir_path}' is a file, not a directory."}

        try:
            items = []
            for item in path.iterdir():
                if not include_hidden and item.name.startswith("."):
                    continue
                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size_bytes": item.stat().st_size if item.is_file() else None,
                })
            return {
                "status": "success",
                "directory": str(path),
                "count": len(items),
                "items": sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower())),
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to list directory '{dir_path}': {e}"}

    def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout_seconds: int = 60,
        user_confirmation: bool = False,
    ) -> Dict[str, Any]:
        """Execute a PowerShell command on the Windows PC.

        STRICT SAFETY: Requires user_confirmation=True for modifying/system commands.
        """
        # Distinguish safe read-only commands vs modifying commands
        modifying_keywords = ["del", "rm", "remove", "kill", "stop-process", "set-", "new-item", "start-process", "format", "reg", "net"]
        is_potentially_destructive = any(kw in command.lower() for kw in modifying_keywords)

        if is_potentially_destructive and not user_confirmation:
            return {
                "status": "permission_denied",
                "message": f"Command '{command}' appears to be modifying or destructive. Explicit user approval is required before execution (pass user_confirmation=True).",
                "command": command,
            }

        cwd = working_dir or str(self.user_home)
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return {
                "status": "completed",
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "command": command,
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": f"Command timed out after {timeout_seconds}s."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to execute command: {e}"}

    def launch_app(
        self,
        app_name_or_path: str,
        args: Optional[List[str]] = None,
        user_confirmation: bool = False,
    ) -> Dict[str, Any]:
        """Launch a desktop application with user permission."""
        if not user_confirmation:
            return {
                "status": "permission_denied",
                "message": f"Launching application '{app_name_or_path}' requires user permission. Pass user_confirmation=True after asking the user.",
            }

        try:
            cmd = ["powershell", "-NoProfile", "-Command", f"Start-Process '{app_name_or_path}'"]
            if args:
                cmd[-1] += f" -ArgumentList '{' '.join(args)}'"
            subprocess.Popen(cmd, shell=True)
            return {
                "status": "success",
                "message": f"Application '{app_name_or_path}' launched successfully.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to launch '{app_name_or_path}': {e}"}


_system_control_service: Optional[SystemControlService] = None


def get_system_control_service() -> SystemControlService:
    global _system_control_service
    if _system_control_service is None:
        _system_control_service = SystemControlService()
    return _system_control_service
