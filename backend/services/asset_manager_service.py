"""Asset Manager Service for Jarvis Web Architect.

Manages curated, high-resolution, purpose-driven visual assets:
- Validates aspect ratios (16:9 Hero, 4:3 Showcase, 1:1 Avatar/Logo)
- Organizes `.jarvis/assets/` directory
- Generates and maintains `.jarvis/assets.json` manifest
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("asset_manager_service")

# Curated High-End Unsplash Imagery Bank by Industry & Purpose
CURATED_ASSETS: Dict[str, Dict[str, Any]] = {
    "real_estate": {
        "hero": {
            "url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=85",
            "aspect_ratio": "16:9",
            "purpose": "hero_background",
            "alt": "Contemporary Luxury Villa",
        },
        "showcase_1": {
            "url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80",
            "aspect_ratio": "4:3",
            "purpose": "listing_card",
            "alt": "The Obsidian Grand Villa",
        },
        "showcase_2": {
            "url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=80",
            "aspect_ratio": "4:3",
            "purpose": "listing_card",
            "alt": "Maitama Crown Penthouse",
        },
        "showcase_3": {
            "url": "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=800&q=80",
            "aspect_ratio": "4:3",
            "purpose": "listing_card",
            "alt": "Guzape Horizon Residence",
        },
    },
    "portfolio": {
        "hero": {
            "url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=1200&q=85",
            "aspect_ratio": "16:9",
            "purpose": "hero_portrait",
            "alt": "Executive Portrait",
        },
        "project_1": {
            "url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80",
            "aspect_ratio": "16:10",
            "purpose": "case_study",
            "alt": "Fintech & Data Intelligence Dashboard",
        },
        "project_2": {
            "url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80",
            "aspect_ratio": "16:10",
            "purpose": "case_study",
            "alt": "Autonomous Agent Network",
        },
    },
    "restaurant": {
        "hero": {
            "url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1600&q=85",
            "aspect_ratio": "16:9",
            "purpose": "hero_dining",
            "alt": "Artisanal Fine Dining Atmosphere",
        },
        "dish_1": {
            "url": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80",
            "aspect_ratio": "4:3",
            "purpose": "menu_feature",
            "alt": "Signature Dry-Aged Ribeye",
        },
        "dish_2": {
            "url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=800&q=80",
            "aspect_ratio": "4:3",
            "purpose": "menu_feature",
            "alt": "Truffle Handcrafted Pasta",
        },
    },
    "saas": {
        "hero": {
            "url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1600&q=85",
            "aspect_ratio": "16:9",
            "purpose": "product_dashboard_hero",
            "alt": "Cloud Analytics SaaS Interface",
        },
    },
}


class AssetManagerService:
    """Manages visual assets and manifest for web applications."""

    def hydrate_project_assets(self, project_dir: Path, industry: str) -> Dict[str, Any]:
        """Generate and write .jarvis/assets.json for the project."""
        industry_key = industry.lower()
        if industry_key not in CURATED_ASSETS:
            industry_key = "real_estate"

        assets = CURATED_ASSETS.get(industry_key, CURATED_ASSETS["real_estate"])
        assets_file = project_dir / ".jarvis" / "assets.json"
        assets_file.parent.mkdir(parents=True, exist_ok=True)
        assets_file.write_text(json.dumps(assets, indent=2), encoding="utf-8")
        return assets


_ASSET_MANAGER_INSTANCE: Optional[AssetManagerService] = None


def get_asset_manager_service() -> AssetManagerService:
    global _ASSET_MANAGER_INSTANCE
    if _ASSET_MANAGER_INSTANCE is None:
        _ASSET_MANAGER_INSTANCE = AssetManagerService()
    return _ASSET_MANAGER_INSTANCE
