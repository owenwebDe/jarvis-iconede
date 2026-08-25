"""Git Versioning & Rollback Service for Jarvis Web Architect.

Maintains an autonomous Git commit history and version snapshot system
inside each project to allow zero-risk surgical editing and 1-click rollback:
- git_init_project(project_dir)
- git_checkpoint(project_dir, message)
- git_rollback(project_dir, target_checkpoint="HEAD~1")
- git_history(project_dir)
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("git_version_service")


class GitVersionService:
    """Manages Git version checkpoints and rollback for generated projects."""

    def init_project(self, project_dir: Path) -> Dict[str, Any]:
        """Initialize Git repository for project if not already initialized."""
        try:
            if not (project_dir / ".git").exists():
                subprocess.run(["git", "init"], cwd=str(project_dir), check=True, capture_output=True)
                # Create .gitignore
                gitignore = project_dir / ".gitignore"
                if not gitignore.exists():
                    gitignore.write_text("node_modules\n.env\ndist\n", encoding="utf-8")
                self.checkpoint(project_dir, "Initial project scaffold")
            return {"status": "success", "message": "Git repository initialized."}
        except Exception as e:
            logger.warning(f"Git init failed: {e}")
            return {"status": "warning", "message": str(e)}

    def checkpoint(self, project_dir: Path, message: str) -> Dict[str, Any]:
        """Create a Git commit checkpoint before/after an agent modification."""
        try:
            subprocess.run(["git", "add", "."], cwd=str(project_dir), check=True, capture_output=True)
            res = subprocess.run(
                ["git", "commit", "-m", f"jarvis: {message}"],
                cwd=str(project_dir),
                check=False,
                capture_output=True,
                text=True,
            )
            # Record in .jarvis/versions/
            ver_dir = project_dir / ".jarvis" / "versions"
            ver_dir.mkdir(parents=True, exist_ok=True)
            v_entry = {
                "timestamp": time.time(),
                "message": message,
                "output": res.stdout.strip() or res.stderr.strip(),
            }
            log_file = ver_dir / "checkpoints.json"
            history = []
            if log_file.exists():
                try:
                    history = json.loads(log_file.read_text(encoding="utf-8"))
                except Exception:
                    history = []
            history.append(v_entry)
            log_file.write_text(json.dumps(history, indent=2), encoding="utf-8")

            return {"status": "success", "message": f"Checkpoint created: '{message}'"}
        except Exception as e:
            logger.warning(f"Git checkpoint failed: {e}")
            return {"status": "warning", "message": str(e)}

    def rollback(self, project_dir: Path, target: str = "HEAD~1") -> Dict[str, Any]:
        """Roll back the project to the previous checkpoint if QA or Critic fails."""
        try:
            subprocess.run(["git", "reset", "--hard", target], cwd=str(project_dir), check=True, capture_output=True)
            subprocess.run(["git", "clean", "-fd"], cwd=str(project_dir), check=True, capture_output=True)
            logger.info(f"Project '{project_dir.name}' rolled back to {target}")
            return {"status": "success", "message": f"Rolled back to {target}"}
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {"status": "error", "message": f"Rollback failed: {str(e)}"}

    def get_history(self, project_dir: Path) -> List[Dict[str, Any]]:
        """Retrieve recent Git commit history."""
        try:
            res = subprocess.run(
                ["git", "log", "-n", "10", "--pretty=format:%h|%an|%ar|%s"],
                cwd=str(project_dir),
                check=True,
                capture_output=True,
                text=True,
            )
            commits = []
            for line in res.stdout.strip().split("\n"):
                if line and "|" in line:
                    parts = line.split("|")
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "relative_time": parts[2],
                        "subject": parts[3],
                    })
            return commits
        except Exception:
            return []


_GIT_VERSION_INSTANCE: Optional[GitVersionService] = None


def get_git_version_service() -> GitVersionService:
    global _GIT_VERSION_INSTANCE
    if _GIT_VERSION_INSTANCE is None:
        _GIT_VERSION_INSTANCE = GitVersionService()
    return _GIT_VERSION_INSTANCE
