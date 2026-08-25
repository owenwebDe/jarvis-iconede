"""Self-Evolution FastMCP Server.

Exposes tools for Jarvis to autonomously propose code modifications, create new
MCP tools, run AST/pytest validations, and safely apply changes with explicit
human authorization and git checkpoints.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Allow imports from backend/
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from services.self_evolution import get_evolution_service  # noqa: E402

logger = logging.getLogger("self_evolution_server")
mcp = FastMCP("SelfEvolutionService")


@mcp.tool()
def self_update_propose(
    target_file: str,
    instruction: str,
    new_code: str,
    reason: str,
) -> str:
    """Propose an update to an existing file in the Jarvis codebase.

    Generates a unified diff, performs AST syntax validation, and creates a
    pending proposal. Does NOT modify the file until human confirmation is granted.

    Args:
        target_file: Path to the target file (relative to workspace or absolute).
        instruction: Short description of the change (e.g. "Add caching to scraping").
        new_code: Full new content of the file.
        reason: Justification explaining why this update enhances Jarvis capabilities.
    """
    service = get_evolution_service()
    proposal = service.create_proposal(
        target_file=target_file,
        instruction=instruction,
        new_content=new_code,
        reason=reason,
    )

    return json.dumps({
        "status": "proposal_created",
        "proposal_id": proposal.proposal_id,
        "target_file": proposal.relative_path,
        "validation_status": proposal.validation_status,
        "validation_error": proposal.validation_error,
        "diff": proposal.diff,
        "next_step": (
            "Present this diff and reason to the user for explicit approval. "
            f"Once approved, call self_update_apply(proposal_id='{proposal.proposal_id}', user_confirmation=True)."
        ),
    }, indent=2)


@mcp.tool()
def self_update_apply(proposal_id: str, user_confirmation: bool = False) -> str:
    """Apply an approved self-update proposal to the codebase.

    CRITICAL SAFETY REQUIREMENT: You MUST pass user_confirmation=True ONLY after
    the user has explicitly agreed to the change.

    Args:
        proposal_id: The ID of the proposal created by self_update_propose.
        user_confirmation: Must be True if the human user gave explicit consent.
    """
    service = get_evolution_service()
    res = service.apply_proposal(proposal_id=proposal_id, user_confirmation=user_confirmation)
    return json.dumps(res, indent=2)


@mcp.tool()
def self_update_rollback(proposal_id: str) -> str:
    """Instantly roll back a previously applied self-update to its prior state.

    Args:
        proposal_id: The ID of the applied proposal to revert.
    """
    service = get_evolution_service()
    res = service.rollback_proposal(proposal_id=proposal_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def self_update_create_tool(
    tool_name: str,
    tool_code: str,
    description: str,
    reason: str,
) -> str:
    """Propose creating a brand-new MCP tool in backend/tools/.

    Generates a proposal for a new tool file with pre-flight AST validation.

    Args:
        tool_name: Name of the tool (e.g. 'whatsapp_automation' or 'pdf_invoice_generator').
        tool_code: Full Python source code implementing the FastMCP tool server.
        description: Short summary of what the new tool accomplishes.
        reason: Why this new tool is needed to expand Jarvis capabilities.
    """
    service = get_evolution_service()
    proposal = service.create_custom_tool(
        tool_name=tool_name,
        tool_code=tool_code,
        description=description,
        reason=reason,
    )
    return json.dumps({
        "status": "proposal_created",
        "proposal_id": proposal.proposal_id,
        "target_file": proposal.relative_path,
        "validation_status": proposal.validation_status,
        "validation_error": proposal.validation_error,
        "diff": proposal.diff,
        "next_step": (
            f"Ask user for approval to create new tool '{tool_name}'. "
            f"Upon approval, call self_update_apply(proposal_id='{proposal.proposal_id}', user_confirmation=True)."
        ),
    }, indent=2)


@mcp.tool()
def self_update_list_proposals() -> str:
    """List all past self-evolution proposals and their current status."""
    service = get_evolution_service()
    summaries = [
        {
            "proposal_id": p.proposal_id,
            "target_file": p.relative_path,
            "status": p.status,
            "instruction": p.instruction,
            "validation_status": p.validation_status,
            "created_at": p.created_at,
            "applied_at": p.applied_at,
        }
        for p in service.proposals.values()
    ]
    return json.dumps({"count": len(summaries), "proposals": summaries}, indent=2)


if __name__ == "__main__":
    mcp.run()
