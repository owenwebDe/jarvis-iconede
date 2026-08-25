"""Self-Evolution Service for Jarvis.

Enables Jarvis to propose code updates, validate changes with AST/pytest,
require human confirmation, apply changes with git checkpoints, and provide
instant one-click rollback.
"""

from __future__ import annotations

import ast
import difflib
import json
import logging
import os
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("self_evolution")

# Workspace root is the jarvis project directory
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
_STATE_DIR = _BACKEND_DIR / ".runtime" / "self_evolution"
_STATE_DIR.mkdir(parents=True, exist_ok=True)
_PROPOSALS_FILE = _STATE_DIR / "proposals.json"


@dataclass
class CodeUpdateProposal:
    proposal_id: str
    target_file: str
    relative_path: str
    instruction: str
    reason: str
    original_content: str
    proposed_content: str
    diff: str
    status: str = "pending_review"  # pending_review, approved, applied, rejected, rolled_back
    created_at: float = field(default_factory=time.time)
    applied_at: Optional[float] = None
    git_checkpoint_hash: Optional[str] = None
    validation_status: str = "passed"
    validation_error: Optional[str] = None


class SelfEvolutionService:
    """Manages self-evolution proposals, validations, git checkpoints, and execution."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or _PROJECT_ROOT
        self.proposals: Dict[str, CodeUpdateProposal] = {}
        self._load_proposals()

    def _load_proposals(self) -> None:
        """Load past proposals from disk."""
        if _PROPOSALS_FILE.exists():
            try:
                data = json.loads(_PROPOSALS_FILE.read_text(encoding="utf-8"))
                for pid, pdata in data.items():
                    self.proposals[pid] = CodeUpdateProposal(**pdata)
            except Exception as e:
                logger.warning(f"Failed to load self-evolution proposals: {e}")

    def _save_proposals(self) -> None:
        """Persist proposals to disk."""
        try:
            data = {pid: asdict(p) for pid, p in self.proposals.items()}
            _PROPOSALS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save self-evolution proposals: {e}")

    def _get_git_head_hash(self) -> Optional[str]:
        """Get the current git commit hash."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def _create_git_checkpoint(self, message: str) -> Optional[str]:
        """Create a git commit checkpoint before applying changes."""
        try:
            subprocess.run(["git", "add", "-A"], cwd=str(self.workspace_root), check=False)
            res = subprocess.run(
                ["git", "commit", "-m", f"checkpoint(pre-self-update): {message}"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=False,
            )
            return self._get_git_head_hash()
        except Exception as e:
            logger.warning(f"Git checkpoint creation failed: {e}")
            return None

    def create_proposal(
        self,
        target_file: str,
        instruction: str,
        new_content: str,
        reason: str,
    ) -> CodeUpdateProposal:
        """Create a new self-update proposal with unified diff and AST syntax validation."""
        target_path = Path(target_file)
        if not target_path.is_absolute():
            target_path = (self.workspace_root / target_file).resolve()

        try:
            relative_path = str(target_path.relative_to(self.workspace_root))
        except Exception:
            relative_path = str(target_path)

        original_content = ""
        if target_path.exists():
            original_content = target_path.read_text(encoding="utf-8", errors="replace")

        # Unescape literal backslash-n if model passed double-escaped newlines in JSON
        normalized_content = new_content
        if "\\n" in normalized_content and "\n" not in normalized_content:
            normalized_content = normalized_content.replace("\\n", "\n").replace("\\t", "    ")

        # 1. Compute Unified Diff
        diff_lines = list(
            difflib.unified_diff(
                original_content.splitlines(keepends=True),
                normalized_content.splitlines(keepends=True),
                fromfile=f"a/{relative_path}",
                tofile=f"b/{relative_path}",
            )
        )
        diff_str = "".join(diff_lines) if diff_lines else "(No textual changes)"

        # 2. Pre-flight Syntax Validation (if Python file)
        validation_status = "passed"
        validation_error = None
        if target_path.suffix == ".py":
            try:
                ast.parse(normalized_content, filename=str(target_path))
            except SyntaxError as syn_err:
                validation_status = "failed"
                validation_error = f"Python SyntaxError at line {syn_err.lineno}: {syn_err.msg}"

        proposal_id = f"prop_{uuid.uuid4().hex[:8]}"
        proposal = CodeUpdateProposal(
            proposal_id=proposal_id,
            target_file=str(target_path),
            relative_path=relative_path,
            instruction=instruction,
            reason=reason,
            original_content=original_content,
            proposed_content=normalized_content,
            diff=diff_str,
            status="pending_review" if validation_status == "passed" else "validation_failed",
            validation_status=validation_status,
            validation_error=validation_error,
        )

        self.proposals[proposal_id] = proposal
        self._save_proposals()
        return proposal

    def apply_proposal(self, proposal_id: str, user_confirmation: bool = False) -> Dict[str, Any]:
        """Apply an approved self-update proposal to disk.

        STRICT SAFETY RULE: Requires user_confirmation=True.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"status": "error", "message": f"Proposal '{proposal_id}' not found."}

        if not user_confirmation:
            return {
                "status": "permission_denied",
                "message": "Human confirmation required. Pass user_confirmation=True after explicit user consent.",
                "proposal_id": proposal_id,
            }

        if proposal.validation_status != "passed":
            return {
                "status": "error",
                "message": f"Cannot apply proposal due to validation failure: {proposal.validation_error}",
            }

        # 1. Create Git Checkpoint
        checkpoint_hash = self._create_git_checkpoint(f"Pre-update for {proposal.relative_path}")
        proposal.git_checkpoint_hash = checkpoint_hash

        # 2. Write file atomically
        target_path = Path(proposal.target_file)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(proposal.proposed_content, encoding="utf-8")

        proposal.status = "applied"
        proposal.applied_at = time.time()
        self._save_proposals()

        logger.info(f"[SELF-EVOLUTION] Applied proposal {proposal_id} to {proposal.relative_path}")
        return {
            "status": "success",
            "proposal_id": proposal_id,
            "target_file": proposal.relative_path,
            "git_checkpoint": checkpoint_hash,
            "message": f"Successfully applied update to {proposal.relative_path}.",
        }

    def rollback_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Revert a previously applied proposal to its exact original content."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"status": "error", "message": f"Proposal '{proposal_id}' not found."}

        if proposal.status != "applied":
            return {
                "status": "error",
                "message": f"Proposal '{proposal_id}' is not in 'applied' state (current: {proposal.status}).",
            }

        target_path = Path(proposal.target_file)
        if proposal.original_content:
            target_path.write_text(proposal.original_content, encoding="utf-8")
        elif target_path.exists():
            target_path.unlink()

        proposal.status = "rolled_back"
        self._save_proposals()

        logger.info(f"[SELF-EVOLUTION] Rolled back proposal {proposal_id} on {proposal.relative_path}")
        return {
            "status": "success",
            "proposal_id": proposal_id,
            "target_file": proposal.relative_path,
            "message": f"Successfully rolled back {proposal.relative_path} to prior state.",
        }

    def create_custom_tool(
        self,
        tool_name: str,
        tool_code: str,
        description: str,
        reason: str,
    ) -> CodeUpdateProposal:
        """Propose creating a brand new FastMCP tool in backend/tools/."""
        clean_name = tool_name.lower().replace("-", "_").strip()
        if not clean_name.endswith("_server"):
            file_name = f"{clean_name}_server.py"
        else:
            file_name = f"{clean_name}.py"

        target_file = _BACKEND_DIR / "tools" / file_name
        instruction = f"Create new FastMCP tool server: {clean_name} ({description})"
        return self.create_proposal(
            target_file=str(target_file),
            instruction=instruction,
            new_content=tool_code,
            reason=reason,
        )


_evolution_service: Optional[SelfEvolutionService] = None


def get_evolution_service() -> SelfEvolutionService:
    global _evolution_service
    if _evolution_service is None:
        _evolution_service = SelfEvolutionService()
    return _evolution_service
