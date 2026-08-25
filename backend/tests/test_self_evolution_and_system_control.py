"""Unit tests for Self-Evolution & System Control Services."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Insert backend directory
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from services.self_evolution import SelfEvolutionService
from services.system_control import SystemControlService


def test_self_evolution_proposal_and_permission():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        service = SelfEvolutionService(workspace_root=tmp_root)

        test_file = tmp_root / "test_module.py"
        test_file.write_text("def hello():\n    return 'old'\n", encoding="utf-8")

        # 1. Create proposal
        proposal = service.create_proposal(
            target_file=str(test_file),
            instruction="Update return string to 'new'",
            new_content="def hello():\n    return 'new'\n",
            reason="Improve return value",
        )

        assert proposal.validation_status == "passed"
        assert "-    return 'old'" in proposal.diff
        assert "+    return 'new'" in proposal.diff
        assert proposal.status == "pending_review"

        # 2. Attempt apply WITHOUT user confirmation -> BLOCKED
        res_denied = service.apply_proposal(proposal.proposal_id, user_confirmation=False)
        assert res_denied["status"] == "permission_denied"
        assert test_file.read_text(encoding="utf-8") == "def hello():\n    return 'old'\n"

        # 3. Apply WITH user confirmation -> SUCCESS
        res_ok = service.apply_proposal(proposal.proposal_id, user_confirmation=True)
        assert res_ok["status"] == "success"
        assert test_file.read_text(encoding="utf-8") == "def hello():\n    return 'new'\n"

        # 4. Test Rollback
        res_rollback = service.rollback_proposal(proposal.proposal_id)
        assert res_rollback["status"] == "success"
        assert test_file.read_text(encoding="utf-8") == "def hello():\n    return 'old'\n"


def test_self_evolution_syntax_validation_failure():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        service = SelfEvolutionService(workspace_root=tmp_root)

        test_file = tmp_root / "broken_module.py"

        # Invalid Python syntax
        proposal = service.create_proposal(
            target_file=str(test_file),
            instruction="Broken code",
            new_content="def invalid syntax here (:",
            reason="Test syntax failure",
        )

        assert proposal.validation_status == "failed"
        assert "SyntaxError" in proposal.validation_error

        # Attempt to apply invalid proposal -> blocked
        res = service.apply_proposal(proposal.proposal_id, user_confirmation=True)
        assert res["status"] == "error"
        assert "validation failure" in res["message"]


def test_system_control_telemetry_and_safe_reads():
    service = SystemControlService()

    # 1. Telemetry
    telem = service.get_telemetry()
    assert "os" in telem
    assert "user_home" in telem
    assert len(telem["drives"]) > 0

    # 2. Process list
    procs = service.list_processes(max_count=10)
    assert isinstance(procs, list)

    # 3. Read current script
    read_res = service.read_file(__file__)
    assert read_res["status"] == "success"
    assert "test_system_control" in read_res["content"]


def test_system_control_modifying_permission_gating():
    service = SystemControlService()

    with tempfile.TemporaryDirectory() as tmpdir:
        target_file = Path(tmpdir) / "output.txt"

        # 1. Write without confirmation -> BLOCKED
        res_write_denied = service.write_file(str(target_file), "hello", user_confirmation=False)
        assert res_write_denied["status"] == "permission_denied"
        assert not target_file.exists()

        # 2. Write with confirmation -> SUCCESS
        res_write_ok = service.write_file(str(target_file), "hello", user_confirmation=True)
        assert res_write_ok["status"] == "success"
        assert target_file.read_text(encoding="utf-8") == "hello"

        # 3. Destructive command without confirmation -> BLOCKED
        res_cmd_denied = service.execute_command("del output.txt", working_dir=tmpdir, user_confirmation=False)
        assert res_cmd_denied["status"] == "permission_denied"

        # 4. Safe read-only command (e.g. echo or dir) -> ALLOWED
        res_safe_cmd = service.execute_command("echo 'jarvis safe check'", working_dir=tmpdir, user_confirmation=False)
        assert res_safe_cmd["status"] == "completed"
        assert "jarvis safe check" in res_safe_cmd["stdout"]
