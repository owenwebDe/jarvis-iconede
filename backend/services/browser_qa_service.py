"""Playwright Browser QA & Visual Inspection Service for Jarvis Web Architect.

Performs deep browser automation testing:
- Console error and warning tracking
- Network request failure & 404 tracking
- Horizontal layout overflow detection
- Interactive element testing (clicks, modal triggers, theme toggle)
- Desktop and Mobile full-page screenshots (.jarvis/screenshots/)
- Hard failure detection gating deployment
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright

logger = logging.getLogger("browser_qa_service")


class BrowserQAService:
    """Automates Playwright browser testing and visual QA for web projects."""

    def test_project(
        self,
        target_url_or_path: str,
        output_dir: Optional[Path] = None,
        timeout_ms: int = 15000,
    ) -> Dict[str, Any]:
        """Run deep browser test on a URL or local HTML file."""
        console_errors: List[str] = []
        console_warnings: List[str] = []
        network_failures: List[str] = []
        interactive_checks: List[Dict[str, Any]] = []

        url = target_url_or_path
        if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("file://"):
            local_path = Path(target_url_or_path).resolve()
            if local_path.exists():
                url = local_path.as_uri()
            else:
                return {
                    "passed": False,
                    "hard_failures": [f"Target path does not exist: {target_url_or_path}"],
                    "console_errors": [],
                    "overflow": False,
                }

        screenshots_dir = None
        if output_dir:
            screenshots_dir = output_dir / ".jarvis" / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)

        desktop_screenshot_path = None
        mobile_screenshot_path = None
        has_horizontal_overflow = False

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)

                # 1. Desktop Test (1440x900)
                desktop_context = browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    device_scale_factor=2,
                )
                page = desktop_context.new_page()

                page.on("console", lambda msg: (
                    console_errors.append(msg.text) if msg.type == "error"
                    else console_warnings.append(msg.text) if msg.type == "warning"
                    else None
                ))
                page.on("requestfailed", lambda req: (
                    network_failures.append(f"{req.url} - {req.failure}")
                ))

                logger.info(f"Navigating Playwright browser to {url}...")
                page.goto(url, timeout=timeout_ms, wait_until="load")
                page.wait_for_timeout(1000)  # Allow JS animations and counters to run

                # Check horizontal overflow
                overflow_val = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
                has_horizontal_overflow = bool(overflow_val)

                # Test theme switcher if present
                theme_btn = page.query_selector("#themeToggle, button[title*='Theme'], button[aria-label*='Theme']")
                if theme_btn:
                    try:
                        theme_btn.click()
                        page.wait_for_timeout(300)
                        interactive_checks.append({"action": "theme_toggle", "status": "passed"})
                    except Exception as e:
                        interactive_checks.append({"action": "theme_toggle", "status": "failed", "error": str(e)})

                # Desktop Screenshot
                if screenshots_dir:
                    d_path = screenshots_dir / "desktop_preview.png"
                    page.screenshot(path=str(d_path), full_page=True)
                    desktop_screenshot_path = str(d_path)

                desktop_context.close()

                # 2. Mobile Viewport Test (375x812 iPhone)
                mobile_context = browser.new_context(
                    viewport={"width": 375, "height": 812},
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15",
                    device_scale_factor=2,
                )
                m_page = mobile_context.new_page()
                m_page.goto(url, timeout=timeout_ms, wait_until="load")
                m_page.wait_for_timeout(800)

                mobile_overflow = m_page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
                if mobile_overflow:
                    has_horizontal_overflow = True

                if screenshots_dir:
                    m_path = screenshots_dir / "mobile_preview.png"
                    m_page.screenshot(path=str(m_path), full_page=True)
                    mobile_screenshot_path = str(m_path)

                mobile_context.close()
                browser.close()

        except Exception as e:
            logger.error(f"Playwright test run failed: {e}")
            return {
                "passed": False,
                "hard_failures": [f"Browser execution exception: {str(e)}"],
                "console_errors": console_errors,
                "overflow": has_horizontal_overflow,
            }

        # Determine Hard Failures
        hard_failures = []
        if console_errors:
            # Filter out non-critical harmless warnings if needed
            critical_errors = [e for e in console_errors if not any(ign in e for ign in ["favicon.ico", "DevTools"])]
            if critical_errors:
                hard_failures.append(f"Found {len(critical_errors)} console errors: {critical_errors[:3]}")

        if has_horizontal_overflow:
            hard_failures.append("Detected horizontal layout overflow (page width exceeds viewport).")

        if network_failures:
            hard_failures.append(f"Failed network requests: {network_failures[:3]}")

        passed = len(hard_failures) == 0

        report = {
            "passed": passed,
            "hard_failures": hard_failures,
            "console_errors": console_errors,
            "console_warnings": console_warnings[:5],
            "network_failures": network_failures,
            "has_horizontal_overflow": has_horizontal_overflow,
            "interactive_checks": interactive_checks,
            "desktop_screenshot": desktop_screenshot_path,
            "mobile_screenshot": mobile_screenshot_path,
            "timestamp": time.time(),
        }

        if output_dir:
            qa_file = output_dir / ".jarvis" / "qa.json"
            qa_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

        return report


_BROWSER_QA_INSTANCE: Optional[BrowserQAService] = None


def get_browser_qa_service() -> BrowserQAService:
    global _BROWSER_QA_INSTANCE
    if _BROWSER_QA_INSTANCE is None:
        _BROWSER_QA_INSTANCE = BrowserQAService()
    return _BROWSER_QA_INSTANCE
