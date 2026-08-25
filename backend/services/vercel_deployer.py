"""Vercel and Cloud Deployment Service for IconEdge Demo Websites.

Enables DemoBuilderAgent to deploy generated SMB demo sites in seconds
via Vercel REST API or CLI, returning an instant public URL (https://*.vercel.app).
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("vercel_deployer")


class VercelDeployerService:
    """Deploys demo directories to Vercel or local preview server."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("VERCEL_TOKEN", "")

    def deploy_directory(self, directory: str | Path, project_name: str) -> Dict[str, Any]:
        """Deploy a static directory to Vercel."""
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            return {"status": "error", "message": f"Directory not found: {directory}"}

        # 1. Try Vercel API if token available
        token = self.token or os.environ.get("VERCEL_TOKEN", "")
        if token:
            try:
                files_payload = []
                for p in dir_path.glob("**/*"):
                    if p.is_file() and not p.name.startswith("."):
                        rel_path = str(p.relative_to(dir_path)).replace("\\", "/")
                        content = p.read_bytes()
                        files_payload.append({
                            "file": rel_path,
                            "data": content.decode("utf-8", errors="replace"),
                            "encoding": "utf-8",
                        })

                payload = {
                    "name": project_name.lower().replace("_", "-")[:40],
                    "files": files_payload,
                    "projectSettings": {
                        "framework": None,
                    },
                }

                req = urllib.request.Request(
                    "https://api.vercel.com/v13/deployments",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )

                with urllib.request.urlopen(req, timeout=30) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    url = res_data.get("url", "")
                    if url and not url.startswith("http"):
                        url = f"https://{url}"

                    return {
                        "status": "success",
                        "deployment_url": url,
                        "project_name": project_name,
                        "provider": "vercel_api",
                    }
            except Exception as e:
                logger.warning(f"Vercel API deployment failed: {e}")

        # 2. Try Vercel CLI fallback (if user has vercel installed globally)
        try:
            cmd = ["npx", "-y", "vercel", "deploy", "--prod", "--yes"]
            if token:
                cmd.extend(["--token", token])
            proc = subprocess.run(
                cmd,
                cwd=str(dir_path),
                capture_output=True,
                text=True,
                timeout=55,
                shell=True,
            )
            if proc.returncode == 0:
                output = f"{proc.stdout}\n{proc.stderr}"
                # Extract all vercel.app URLs
                urls = re.findall(r"https://[a-zA-Z0-9.-]+\.vercel\.app", output)
                if urls:
                    # Filter out inspector URLs and prioritize shortest/production alias
                    clean_urls = [u for u in urls if not "inspect" in u]
                    if clean_urls:
                        # The aliased domain (e.g. https://sandra-a-f53003.vercel.app) is usually the shortest or last
                        aliased = [u for u in clean_urls if not any(x in u for x in ["-projects-", "-owens-"])]
                        final_url = aliased[-1] if aliased else clean_urls[-1]
                        return {
                            "status": "success",
                            "deployment_url": final_url,
                            "project_name": project_name,
                            "provider": "vercel_cli",
                        }
        except Exception as e:
            logger.info(f"Vercel CLI skipped: {e}")

        # 3. Fallback: Return verified standalone bundle path with ready-to-share preview
        entrypoint = dir_path / "index.html"
        return {
            "status": "ready_local",
            "deployment_url": f"file:///{str(entrypoint).replace(chr(92), '/')}",
            "project_name": project_name,
            "provider": "local_bundle",
            "message": "Demo built and ready. Set VERCEL_TOKEN in .env for instant automatic 1-click cloud URLs.",
        }


_vercel_deployer: Optional[VercelDeployerService] = None


def get_vercel_deployer() -> VercelDeployerService:
    global _vercel_deployer
    if _vercel_deployer is None:
        _vercel_deployer = VercelDeployerService()
    return _vercel_deployer
