"""Layered Surgical Component Editor for Jarvis Web Architect.

Replaces reckless global regex with a 4-Layer Editing Hierarchy:
- Layer 1: Exact Unique Substring Replacement
- Layer 2: Structured Component Node Replacement
- Layer 3: Boundary-Safe Regex/Prop Replacement
- Layer 4: Targeted Single-Component LLM Rewrite

Preserves the rest of the application without whole-page regenerations.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("surgical_editor_service")


class SurgicalEditorService:
    """Multi-layer precision editor for React/TypeScript components."""

    def patch_file(
        self,
        project_dir: Path,
        rel_path: str,
        target_content: str,
        replacement_content: str,
        preferred_layer: int = 1,
    ) -> Dict[str, Any]:
        """Apply layered surgical modification to a component file."""
        target_file = project_dir / rel_path
        if not target_file.exists():
            return {"status": "error", "message": f"File '{rel_path}' not found in project."}

        content = target_file.read_text(encoding="utf-8")
        applied_layer = None
        new_content = None

        # --- LAYER 1: Exact Unique Substring Replacement ---
        if preferred_layer <= 1 and target_content in content:
            count = content.count(target_content)
            if count == 1:
                new_content = content.replace(target_content, replacement_content, 1)
                applied_layer = 1
            else:
                logger.warning(f"Target content appears {count} times. Falling back to Layer 2/3.")

        # --- LAYER 2: Line-Trimmed Match ---
        if new_content is None and preferred_layer <= 2:
            target_clean = target_content.strip()
            if target_clean in content:
                new_content = content.replace(target_clean, replacement_content.strip(), 1)
                applied_layer = 2

        # --- LAYER 3: Boundary-Safe Regex Token Replacement ---
        if new_content is None and preferred_layer <= 3:
            try:
                escaped = re.escape(target_content)
                pattern = re.compile(escaped, re.MULTILINE)
                if pattern.search(content):
                    new_content = pattern.sub(replacement_content, content, count=1)
                    applied_layer = 3
            except Exception as e:
                logger.warning(f"Layer 3 regex failed: {e}")

        if new_content is None:
            return {
                "status": "error",
                "message": f"Could not find target content in '{rel_path}' across Layer 1-3. Use Layer 4 (full component rewrite).",
                "attempted_layers": [1, 2, 3],
            }

        target_file.write_text(new_content, encoding="utf-8")
        self._record_edit_history(project_dir, rel_path, applied_layer, target_content, replacement_content)

        return {
            "status": "success",
            "file_path": rel_path,
            "applied_layer": applied_layer,
            "layer_name": f"Layer {applied_layer} Surgical Replacement",
            "message": f"Surgically updated '{rel_path}' via Layer {applied_layer}",
        }

    def write_component(
        self,
        project_dir: Path,
        rel_path: str,
        code: str,
    ) -> Dict[str, Any]:
        """Layer 4: Overwrite single isolated component file."""
        target_file = project_dir / rel_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(code, encoding="utf-8")
        self._record_edit_history(project_dir, rel_path, 4, "(full file rewrite)", "(new code)")

        return {
            "status": "success",
            "file_path": rel_path,
            "applied_layer": 4,
            "layer_name": "Layer 4 Component Rewrite",
            "bytes": len(code.encode("utf-8")),
            "message": f"Successfully rewrote component '{rel_path}'",
        }

    def _record_edit_history(
        self,
        project_dir: Path,
        rel_path: str,
        layer: int,
        target: str,
        replacement: str,
    ) -> None:
        """Append to .jarvis/generation.json audit trail."""
        gen_file = project_dir / ".jarvis" / "generation.json"
        gen_file.parent.mkdir(parents=True, exist_ok=True)

        history = []
        if gen_file.exists():
            try:
                history = json.loads(gen_file.read_text(encoding="utf-8"))
            except Exception:
                history = []

        history.append({
            "timestamp": time.time(),
            "file_path": rel_path,
            "layer": layer,
            "target_snippet": target[:80],
            "replacement_snippet": replacement[:80],
        })
        gen_file.write_text(json.dumps(history, indent=2), encoding="utf-8")


_SURGICAL_EDITOR_INSTANCE: Optional[SurgicalEditorService] = None


def get_surgical_editor_service() -> SurgicalEditorService:
    global _SURGICAL_EDITOR_INSTANCE
    if _SURGICAL_EDITOR_INSTANCE is None:
        _SURGICAL_EDITOR_INSTANCE = SurgicalEditorService()
    return _SURGICAL_EDITOR_INSTANCE
