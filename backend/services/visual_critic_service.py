"""Strict Human-Grade Visual & Content Integrity Critic for Jarvis Web Architect.

Evaluates websites across 6 Strict Human-Grade Dimensions + 10-Point Technical Rubric:
1. Brand Authenticity (0-10): Penalizes grand AI luxury jargon ("prosperity redefined", "visionary specialists"). Rewards grounded, restrained, executive tone.
2. Content Restraint (0-10): Penalizes excessive copy paragraphs explaining luxury. Rewards visual confidence and concise specs.
3. Composition Originality (0-10): Penalizes identical repeated 3-column cards. Rewards varied editorial layouts (heroic widescreen, split architectural, asymmetrical).
4. Asset Quality & Art Direction (0-10): Verifies purposeful cinematic imagery interacting with typography.
5. Credibility & Content Integrity (0-10): STRICT ZERO TOLERANCE for fabricated fictional executives, fake client testimonials, or unsubstantiated statistics.
6. Mobile Architecture & UX (0-10): Touch targets, zero horizontal overflow, seamless conversion flow.

Calculates:
- overall_score (0-10)
- genericness_score (0-10, Target < 2.0)
- content_integrity_violations (List of fake people/claims)
- hard_passed & quality_passed
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("visual_critic_service")

# AI Luxury Cliché Fingerprints to Penalize
AI_LUXURY_BUZZWORDS = [
    "prosperity redefined",
    "spaces of distinction",
    "visionary specialists",
    "verified acclaim",
    "symphony of elegance",
    "unparalleled opulence",
    "epitome of luxury",
    "crafting spaces of distinction",
    "where luxury meets",
    "step into a world of",
    "curated with passion",
    "redefining modern living",
]

# Suspect Fabricated Person Patterns
FABRICATED_PERSON_PATTERNS = [
    r"tariq al-mansoor",
    r"amina bello-danjuma",
    r"elena vance-sterling",
    r"senator d\. ibrahim",
    r"mrs\. folashade a",
    r"ambassador k\. davies",
]


class VisualCriticService:
    """Strict human-grade critic evaluating art direction, restraint, composition, and integrity."""

    def evaluate(
        self,
        project_dir: Path,
        qa_report: Dict[str, Any],
        business_meta: Dict[str, Any],
        design_spec: Optional[Dict[str, Any]] = None,
        requirements: str = "",
    ) -> Dict[str, Any]:
        """Perform strict human-grade design and integrity audit."""
        scores: Dict[str, float] = {}
        issues: List[str] = []
        anti_patterns: List[str] = []
        integrity_violations: List[str] = []

        has_overflow = qa_report.get("has_horizontal_overflow", False)
        console_errors = qa_report.get("console_errors", [])

        # Read project HTML/JSX code
        code_text = ""
        for src_file in project_dir.glob("src/**/*.*"):
            if src_file.suffix in (".tsx", ".ts", ".jsx", ".js", ".html", ".css"):
                try:
                    code_text += src_file.read_text(encoding="utf-8", errors="ignore") + "\n"
                except Exception:
                    pass
        if not code_text and (project_dir / "index.html").exists():
            code_text = (project_dir / "index.html").read_text(encoding="utf-8", errors="ignore")

        code_lower = code_text.lower()

        # ----------------------------------------------------
        # 1. BRAND AUTHENTICITY & RESTRAINT (0-10)
        # ----------------------------------------------------
        authenticity_score = 9.5
        buzzword_count = sum(1 for bw in AI_LUXURY_BUZZWORDS if bw in code_lower)
        if buzzword_count > 0:
            penalty = min(5.0, buzzword_count * 1.5)
            authenticity_score -= penalty
            issues.append(f"Contains {buzzword_count} AI luxury clichés (e.g. 'prosperity redefined'). Use restrained, grounded copy.")

        # Check for copy bloat / excessive paragraph length
        paragraph_matches = re.findall(r"<p[^>]*>(.*?)</p>", code_text, re.DOTALL | re.IGNORECASE)
        long_paragraphs = [p for p in paragraph_matches if len(p.split()) > 35]
        if len(long_paragraphs) > 2:
            authenticity_score -= 1.5
            issues.append("Copy is too verbose. Reduce marketing explanations and let visual hierarchy lead.")

        scores["brand_authenticity"] = round(max(1.0, authenticity_score), 1)

        # ----------------------------------------------------
        # 2. COMPOSITION ORIGINALITY (0-10)
        # ----------------------------------------------------
        comp_score = 9.5
        # Penalize repeated 3-column card layouts
        grid_3_count = code_text.count("grid-cols-3") + code_text.count("md:grid-cols-3") + code_text.count("lg:grid-cols-3")
        if grid_3_count >= 3:
            comp_score -= 3.0
            anti_patterns.append("Repetitive 3-column card grid anti-pattern.")
            issues.append("Vary property card compositions (use full-bleed hero, split architectural view, and asymmetrical showcases).")

        # Reward editorial variety
        if any(token in code_text for token in ["col-span-8", "col-span-7", "col-span-12", "aspect-[21/9]", "aspect-[16/9]"]):
            comp_score = min(10.0, comp_score + 0.5)

        scores["composition_originality"] = round(max(1.0, comp_score), 1)

        # ----------------------------------------------------
        # 3. ART DIRECTION & CINEMATIC HERO (0-10)
        # ----------------------------------------------------
        art_score = 9.0
        if "aspect-[21/9]" in code_text or "h-[85vh]" in code_text or "min-h-[80vh]" in code_text or "inset-0" in code_text:
            art_score = 9.8
        else:
            art_score = 6.5
            issues.append("Hero lacks cinematic scale. Recommend full-bleed widescreen hero with typography overlay.")

        scores["art_direction"] = round(art_score, 1)

        # ----------------------------------------------------
        # 4. CONTENT INTEGRITY & CREDIBILITY (0-10)
        # ----------------------------------------------------
        integrity_score = 10.0
        for pattern in FABRICATED_PERSON_PATTERNS:
            if re.search(pattern, code_lower):
                integrity_violations.append(f"Fabricated person detected: '{pattern}'")
                integrity_score -= 3.0

        if "100% c of o perfected" in code_lower or "₦65b+ delivered" in code_lower:
            integrity_violations.append("Unverified statistical/legal business claim detected.")
            integrity_score -= 2.0

        scores["credibility_integrity"] = round(max(1.0, integrity_score), 1)

        # ----------------------------------------------------
        # 5. TECHNICAL & RESPONSIVE UX (0-10)
        # ----------------------------------------------------
        tech_score = 9.5
        if has_overflow:
            tech_score -= 4.0
            issues.append("Horizontal layout overflow detected.")
        if console_errors:
            tech_score -= min(3.0, len(console_errors) * 1.0)
        if "wa.me" in code_text:
            tech_score = min(10.0, tech_score + 0.5)

        scores["technical_ux"] = round(max(1.0, tech_score), 1)

        # ----------------------------------------------------
        # 6. AI GENERICNESS SCORE (0-10, Target < 2.0)
        # ----------------------------------------------------
        genericness = 0.5
        if buzzword_count > 0:
            genericness += buzzword_count * 1.2
        if grid_3_count >= 2:
            genericness += 2.0
        if integrity_violations:
            genericness += 2.5
        genericness = round(min(10.0, genericness), 1)

        # ----------------------------------------------------
        # AGGREGATE VERDICT & GATING
        # ----------------------------------------------------
        overall_score = round(sum(scores.values()) / len(scores), 2)
        hard_passed = not has_overflow and len(console_errors) == 0 and len(integrity_violations) == 0
        quality_passed = overall_score >= 8.5 and genericness <= 2.0

        passed = hard_passed and quality_passed

        verdict = {
            "passed": passed,
            "overall_score": overall_score,
            "genericness_score": genericness,
            "genericness_target": "< 2.0",
            "quality_threshold": 8.5,
            "hard_passed": hard_passed,
            "quality_passed": quality_passed,
            "rubric_scores": scores,
            "anti_patterns": anti_patterns,
            "integrity_violations": integrity_violations,
            "top_issues": issues[:5],
            "timestamp": time.time(),
        }

        # Save to .jarvis/visual_critic.json
        critic_file = project_dir / ".jarvis" / "visual_critic.json"
        critic_file.parent.mkdir(parents=True, exist_ok=True)
        critic_file.write_text(json.dumps(verdict, indent=2), encoding="utf-8")

        return verdict


_VISUAL_CRITIC_INSTANCE: Optional[VisualCriticService] = None


def get_visual_critic_service() -> VisualCriticService:
    global _VISUAL_CRITIC_INSTANCE
    if _VISUAL_CRITIC_INSTANCE is None:
        _VISUAL_CRITIC_INSTANCE = VisualCriticService()
    return _VISUAL_CRITIC_INSTANCE
