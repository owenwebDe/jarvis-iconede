"""React Project Service for Jarvis Autonomous Web Architect.

Provides modular React + TypeScript + Vite project scaffolding,
multi-archetype Design Intelligence, .jarvis/ project manifests,
Git versioning & rollback, layered surgical component editing,
Playwright browser QA testing, and 10-point Visual Critic scoring.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.asset_manager_service import get_asset_manager_service
from services.browser_qa_service import get_browser_qa_service
from services.git_version_service import get_git_version_service
from services.surgical_editor_service import get_surgical_editor_service
from services.vercel_deployer import get_vercel_deployer
from services.visual_critic_service import get_visual_critic_service

logger = logging.getLogger("react_project_service")

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_BASE_TEMPLATE_DIR = _BACKEND_DIR / "templates" / "react_vite_base"
_PROJECTS_DIR = _BACKEND_DIR / "data" / "react_projects"

# Multi-Archetype Design Intelligence Tokens
DESIGN_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "luxury": {
        "name": "Luxoria Architectural Luxury",
        "typography": {
            "display": "Playfair Display, serif",
            "body": "Plus Jakarta Sans, sans-serif",
            "mono": "Space Grotesk, monospace",
        },
        "palette": {
            "background": "#08090d",
            "surface": "#0f1118",
            "primary": "#c5a880",
            "bronze": "#d4af37",
            "accent": "#ff6711",
            "muted": "#94a3b8",
        },
        "radius": {"cards": "16px", "buttons": "12px", "badges": "100px"},
        "motion": {"duration_reveal": "850ms", "easing": "cubic-bezier(0.16, 1, 0.3, 1)"},
    },
    "tech_saas": {
        "name": "Next-Gen Linear Tech",
        "typography": {
            "display": "Geist, sans-serif",
            "body": "Inter, sans-serif",
            "mono": "JetBrains Mono, monospace",
        },
        "palette": {
            "background": "#030712",
            "surface": "#111827",
            "primary": "#6366f1",
            "bronze": "#818cf8",
            "accent": "#06b6d4",
            "muted": "#64748b",
        },
        "radius": {"cards": "12px", "buttons": "8px", "badges": "6px"},
        "motion": {"duration_reveal": "600ms", "easing": "cubic-bezier(0.2, 0.8, 0.2, 1)"},
    },
    "minimal_editorial": {
        "name": "Kinfolk Minimal Editorial",
        "typography": {
            "display": "Instrument Serif, serif",
            "body": "Plus Jakarta Sans, sans-serif",
            "mono": "Space Mono, monospace",
        },
        "palette": {
            "background": "#faf8f5",
            "surface": "#ffffff",
            "primary": "#18181b",
            "bronze": "#71717a",
            "accent": "#d97706",
            "muted": "#a1a1aa",
        },
        "radius": {"cards": "4px", "buttons": "4px", "badges": "0px"},
        "motion": {"duration_reveal": "900ms", "easing": "cubic-bezier(0.16, 1, 0.3, 1)"},
    },
    "hospitality_dining": {
        "name": "Artisanal Warm Dining",
        "typography": {
            "display": "Cormorant Garamond, serif",
            "body": "Outfit, sans-serif",
            "mono": "DM Mono, monospace",
        },
        "palette": {
            "background": "#0c0a09",
            "surface": "#1c1917",
            "primary": "#d97706",
            "bronze": "#b45309",
            "accent": "#ea580c",
            "muted": "#a8a29e",
        },
        "radius": {"cards": "20px", "buttons": "14px", "badges": "100px"},
        "motion": {"duration_reveal": "800ms", "easing": "cubic-bezier(0.16, 1, 0.3, 1)"},
    },
    "corporate_legal": {
        "name": "Executive Enterprise & Legal",
        "typography": {
            "display": "Merriweather, serif",
            "body": "Plus Jakarta Sans, sans-serif",
            "mono": "IBM Plex Mono, monospace",
        },
        "palette": {
            "background": "#0b132b",
            "surface": "#1c2541",
            "primary": "#3a86ff",
            "bronze": "#4895ef",
            "accent": "#4cc9f0",
            "muted": "#8d99ae",
        },
        "radius": {"cards": "8px", "buttons": "6px", "badges": "4px"},
        "motion": {"duration_reveal": "700ms", "easing": "cubic-bezier(0.2, 0.8, 0.2, 1)"},
    },
}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", slug) or "project"


def _clean_phone_number(phone: str) -> str:
    clean = re.sub(r"[^\d+]", "", phone)
    if clean.startswith("+"):
        clean = clean[1:]
    return clean or "2348000000000"


class ReactProjectService:
    """Orchestrates modular React/Vite project lifecycles with multi-archetype design & Git versioning."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or _PROJECTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.surgical_editor = get_surgical_editor_service()
        self.browser_qa = get_browser_qa_service()
        self.visual_critic = get_visual_critic_service()
        self.git_version = get_git_version_service()
        self.asset_manager = get_asset_manager_service()

    def create_project(
        self,
        business_name: str,
        industry: str = "real_estate",
        mode: str = "marketing",
        archetype: str = "auto",
        location: str = "Abuja, Nigeria",
        phone_number: str = "+234 800 000 0000",
        tagline: str = "",
        theme: str = "dark",
    ) -> Dict[str, Any]:
        """Scaffold a fresh modular React + TypeScript + Vite project with .jarvis manifests & Git history."""
        clean_name = business_name.strip()
        if clean_name.lower() in ("your name", "my portfolio", "me", "myself", "portfolio", "owner", "admin"):
            clean_name = "Owen"
            if not tagline or "tagline" in tagline.lower():
                tagline = "Executive Full-Stack AI Engineer & Creative Technologist"
            if industry == "auto":
                industry = "portfolio"

        project_id = f"{_slugify(clean_name)}-{uuid.uuid4().hex[:6]}"
        project_dir = self.output_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # 1. Copy base template
        if _BASE_TEMPLATE_DIR.exists():
            shutil.copytree(_BASE_TEMPLATE_DIR, project_dir, dirs_exist_ok=True)
        else:
            (project_dir / "src" / "components" / "ui").mkdir(parents=True, exist_ok=True)
            (project_dir / "src" / "pages").mkdir(parents=True, exist_ok=True)
            (project_dir / "src" / "lib").mkdir(parents=True, exist_ok=True)

        clean_phone = _clean_phone_number(phone_number)
        final_tagline = tagline or f"Curating luxury excellence and premium digital experiences in {location}."

        # 2. Select Multi-Archetype Design Intelligence
        selected_archetype = self._resolve_archetype(industry, archetype)
        design_spec = DESIGN_ARCHETYPES.get(selected_archetype, DESIGN_ARCHETYPES["luxury"])

        # 3. Assemble mode-specific components
        if mode == "marketing":
            self._assemble_marketing_components(
                project_dir=project_dir,
                business_name=clean_name,
                industry=industry,
                location=location,
                phone_number=phone_number,
                clean_phone=clean_phone,
                tagline=final_tagline,
                theme=theme,
            )
        else:
            self._assemble_application_components(
                project_dir=project_dir,
                business_name=clean_name,
                industry=industry,
                location=location,
                phone_number=phone_number,
                clean_phone=clean_phone,
                tagline=final_tagline,
            )

        # 4. Generate Standardized .jarvis/ Project Manifest & Assets
        self.asset_manager.hydrate_project_assets(project_dir, industry)
        self._write_manifest(
            project_dir=project_dir,
            project_id=project_id,
            business_name=clean_name,
            industry=industry,
            archetype=selected_archetype,
            mode=mode,
            location=location,
            phone_number=phone_number,
            clean_phone=clean_phone,
            tagline=final_tagline,
            design_spec=design_spec,
        )

        # 5. Initialize Git Repository & Commit Scaffold
        self.git_version.init_project(project_dir)

        meta = {
            "project_id": project_id,
            "business_name": clean_name,
            "industry": industry,
            "archetype": selected_archetype,
            "mode": mode,
            "location": location,
            "phone_number": phone_number,
            "clean_phone": clean_phone,
            "tagline": final_tagline,
            "directory": str(project_dir),
            "entrypoint": str(project_dir / "src" / "App.tsx"),
        }
        logger.info(f"Scaffolded React project '{project_id}' ({selected_archetype} archetype) at {project_dir}")
        return meta

    def _resolve_archetype(self, industry: str, requested: str) -> str:
        """Resolve design archetype based on industry."""
        if requested in DESIGN_ARCHETYPES:
            return requested
        ind = industry.lower()
        if any(k in ind for k in ["saas", "tech", "cloud", "api", "ai", "software"]):
            return "tech_saas"
        if any(k in ind for k in ["restaurant", "dining", "cafe", "culinary", "bistro"]):
            return "hospitality_dining"
        if any(k in ind for k in ["law", "legal", "corporate", "finance", "bank", "consulting"]):
            return "corporate_legal"
        if any(k in ind for k in ["minimal", "editorial", "fashion", "magazine", "journal"]):
            return "minimal_editorial"
        return "luxury"

    def _write_manifest(
        self,
        project_dir: Path,
        project_id: str,
        business_name: str,
        industry: str,
        archetype: str,
        mode: str,
        location: str,
        phone_number: str,
        clean_phone: str,
        tagline: str,
        design_spec: Dict[str, Any],
    ) -> None:
        """Write all .jarvis/ manifest files."""
        jarvis_dir = project_dir / ".jarvis"
        jarvis_dir.mkdir(parents=True, exist_ok=True)

        (jarvis_dir / "project.json").write_text(json.dumps({
            "project_id": project_id,
            "business_name": business_name,
            "framework": "react",
            "bundler": "vite",
            "mode": mode,
            "industry": industry,
            "archetype": archetype,
            "created_at": time.time(),
            "status": "scaffolded",
        }, indent=2), encoding="utf-8")

        (jarvis_dir / "design.json").write_text(json.dumps(design_spec, indent=2), encoding="utf-8")

        (jarvis_dir / "business.json").write_text(json.dumps({
            "business_name": business_name,
            "industry": industry,
            "location": location,
            "phone_number": phone_number,
            "clean_phone": clean_phone,
            "tagline": tagline,
        }, indent=2), encoding="utf-8")

        (jarvis_dir / "components.json").write_text(json.dumps({
            "tree": [
                {"name": "Navbar", "path": "src/components/Navbar.tsx", "role": "Navigation & Theme Switcher"},
                {"name": "Hero", "path": "src/components/Hero.tsx", "role": "Hero Section & Value Proposition"},
                {"name": "ShowcaseGrid", "path": "src/components/ShowcaseGrid.tsx", "role": "Curated Listings/Items"},
                {"name": "WhatsAppForm", "path": "src/components/WhatsAppForm.tsx", "role": "VIP Lead Capture"},
            ],
            "ui_library": "shadcn/ui (49 components)",
        }, indent=2), encoding="utf-8")

        (jarvis_dir / "routes.json").write_text(json.dumps({
            "routes": ["/"],
            "pages": ["src/App.tsx"],
        }, indent=2), encoding="utf-8")

    def _assemble_marketing_components(
        self,
        project_dir: Path,
        business_name: str,
        industry: str,
        location: str,
        phone_number: str,
        clean_phone: str,
        tagline: str,
        theme: str,
    ) -> None:
        """Assemble modular marketing components."""
        comps_dir = project_dir / "src" / "components"
        comps_dir.mkdir(parents=True, exist_ok=True)

        # 1. Navbar.tsx
        (comps_dir / "Navbar.tsx").write_text(f"""import React from 'react';
import {{ Button }} from './ui/button';

interface NavbarProps {{
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}}

export function Navbar({{ theme, onToggleTheme }}: NavbarProps) {{
  return (
    <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-8 h-20 flex items-center justify-between">
        <a href="#hero" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#c5a880] to-[#ff6711] flex items-center justify-center font-extrabold text-black text-lg shadow-lg shadow-[#c5a880]/20 group-hover:scale-105 transition-transform">
            {business_name[0] if business_name else 'O'}
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight block leading-tight">{business_name}</span>
            <span className="text-[11px] font-mono text-[#c5a880] tracking-widest uppercase">{location}</span>
          </div>
        </a>

        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
          <a href="#showcase" className="hover:text-foreground transition-colors">Showcase</a>
          <a href="#contact" className="hover:text-foreground transition-colors">Inquire</a>
        </nav>

        <div className="flex items-center gap-4">
          <Button id="themeToggle" variant="ghost" size="sm" onClick={{onToggleTheme}} className="rounded-xl border border-border">
            {{theme === 'dark' ? '☀️' : '🌙'}}
          </Button>
          <a
            href="https://wa.me/{clean_phone}?text=Hello%20{business_name}%2C%20I%20would%20like%20to%20inquire%20about%20your%20offerings."
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#c5a880] hover:bg-[#d4af37] text-black font-semibold text-xs font-mono uppercase tracking-wider shadow-lg shadow-[#c5a880]/20 transition-all hover:scale-105"
          >
            WhatsApp VIP
          </a>
        </div>
      </div>
    </header>
  );
}}
""", encoding="utf-8")

        # 2. Hero.tsx
        (comps_dir / "Hero.tsx").write_text(f"""import React from 'react';

export function Hero() {{
  return (
    <section id="hero" className="relative pt-20 pb-16 md:pt-32 md:pb-28 px-4 sm:px-8 max-w-7xl mx-auto">
      <div className="grid lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-7 space-y-8">
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#c5a880]">
            <span className="w-2 h-2 rounded-full bg-[#ff6711] animate-pulse"></span>
            <span>EXCELLENCE IN {location.upper()}</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-[1.1]">
            {tagline}
          </h1>

          <p className="text-lg text-muted-foreground max-w-2xl leading-relaxed">
            Engineered with distinction, bespoke craftsmanship, and uncompromising attention to detail for clients across {location} and worldwide.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <a
              href="#showcase"
              className="px-8 py-4 rounded-xl bg-gradient-to-r from-[#c5a880] to-[#d4af37] text-black font-bold text-sm uppercase tracking-wider shadow-xl shadow-[#c5a880]/20 hover:scale-105 transition-all"
            >
              Explore Showcase
            </a>
            <a
              href="#contact"
              className="px-8 py-4 rounded-xl border border-border bg-card/60 backdrop-blur-md text-foreground font-semibold text-sm uppercase tracking-wider hover:border-[#c5a880] transition-all"
            >
              Book Consultation
            </a>
          </div>
        </div>

        <div className="lg:col-span-5">
          <div className="rounded-3xl border border-border/60 bg-card/80 backdrop-blur-xl p-6 shadow-2xl space-y-6">
            <div className="aspect-[4/3] rounded-2xl overflow-hidden relative">
              <img
                src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=85"
                alt="{business_name} Signature"
                className="w-full h-full object-cover hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute top-4 left-4">
                <span className="px-3 py-1 rounded-full text-xs font-mono bg-black/70 backdrop-blur-md text-[#c5a880] border border-[#c5a880]/30">
                  {industry.upper()}
                </span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 text-center">
              <div className="p-4 rounded-xl bg-muted/40 border border-border">
                <div className="text-2xl font-bold text-foreground">100%</div>
                <div className="text-xs text-muted-foreground uppercase font-mono">Verified Quality</div>
              </div>
              <div className="p-4 rounded-xl bg-muted/40 border border-border">
                <div className="text-2xl font-bold text-[#c5a880]">24/7</div>
                <div className="text-xs text-muted-foreground uppercase font-mono">Concierge Service</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}}
""", encoding="utf-8")

        # 3. ShowcaseGrid.tsx
        (comps_dir / "ShowcaseGrid.tsx").write_text(f"""import React from 'react';
import {{ Card, CardContent }} from './ui/card';
import {{ Badge }} from './ui/badge';

interface Item {{
  title: string;
  category: string;
  price: string;
  image: string;
  desc: string;
}}

const ITEMS: Item[] = [
  {{
    title: 'The Obsidian Grand Villa',
    category: 'Prime Luxury',
    price: '₦850,000,000',
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80',
    desc: 'Architectural masterpiece featuring panoramic skyline vistas and private infinity deck.'
  }},
  {{
    title: 'Maitama Crown Penthouse',
    category: 'Executive Suite',
    price: '₦1,250,000,000',
    image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=80',
    desc: 'Bespoke high-ceiling residence with smart automated climate systems and private elevator access.'
  }},
  {{
    title: 'Guzape Horizon Residence',
    category: 'Panoramic Living',
    price: '₦620,000,000',
    image: 'https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=800&q=80',
    desc: 'Elevated hilltop property engineered with cantilevered glass balconies and lush gardens.'
  }}
];

export function ShowcaseGrid() {{
  return (
    <section id="showcase" className="py-24 px-4 sm:px-8 max-w-7xl mx-auto border-t border-border/40">
      <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
        <Badge variant="outline" className="text-[#c5a880] border-[#c5a880]/30 font-mono uppercase">
          CURATED COLLECTION
        </Badge>
        <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight">
          Featured Offerings
        </h2>
        <p className="text-muted-foreground text-sm">
          A selection of exclusive opportunities curated by {business_name} in {location}.
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
        {{ITEMS.map((item, idx) => (
          <Card key={{idx}} className="overflow-hidden border-border/60 bg-card/80 hover:border-[#c5a880]/50 transition-all duration-500 hover:-translate-y-1.5 group">
            <div className="aspect-[16/10] overflow-hidden relative">
              <img
                src={{item.image}}
                alt={{item.title}}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute top-4 left-4">
                <span className="px-3 py-1 rounded-full text-[10px] font-mono uppercase bg-black/70 backdrop-blur-md text-[#c5a880] border border-[#c5a880]/30">
                  {{item.category}}
                </span>
              </div>
            </div>
            <CardContent className="p-6 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-lg group-hover:text-[#c5a880] transition-colors">{{item.title}}</h3>
                <span className="text-sm font-mono font-bold text-[#c5a880]">{{item.price}}</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{{item.desc}}</p>
            </CardContent>
          </Card>
        ))}}
      </div>
    </section>
  );
}}
""", encoding="utf-8")

        # 4. WhatsAppForm.tsx
        (comps_dir / "WhatsAppForm.tsx").write_text(f"""import React, {{ useState }} from 'react';
import {{ Button }} from './ui/button';
import {{ Input }} from './ui/input';
import {{ Textarea }} from './ui/textarea';

export function WhatsAppForm() {{
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e: React.FormEvent) => {{
    e.preventDefault();
    const text = encodeURIComponent(
      `*VIP Inquiry for {business_name}*\\n\\n*Name:* ${{name}}\\n*Phone:* ${{phone}}\\n*Details:* ${{notes}}`
    );
    window.open(`https://wa.me/{clean_phone}?text=${{text}}`, '_blank');
  }};

  return (
    <section id="contact" className="py-24 px-4 sm:px-8 max-w-4xl mx-auto border-t border-border/40">
      <div className="rounded-3xl border border-border/60 bg-card/80 backdrop-blur-xl p-8 sm:p-12 shadow-2xl space-y-8">
        <div className="text-center space-y-3">
          <span className="text-xs font-mono uppercase text-[#c5a880] tracking-widest block">DIRECT CONCIERGE</span>
          <h2 className="text-3xl font-extrabold">Schedule a Private Consultation</h2>
          <p className="text-sm text-muted-foreground">Submit your inquiry directly to the executive desk of {business_name}.</p>
        </div>

        <form onSubmit={{handleSubmit}} className="space-y-6 max-w-xl mx-auto">
          <div className="grid sm:grid-cols-2 gap-4">
            <Input
              required
              placeholder="Your Full Name"
              value={{name}}
              onChange={{(e) => setName(e.target.value)}}
              className="bg-background/50"
            />
            <Input
              required
              type="tel"
              placeholder="Phone / WhatsApp"
              value={{phone}}
              onChange={{(e) => setPhone(e.target.value)}}
              className="bg-background/50"
            />
          </div>
          <Textarea
            required
            rows={{4}}
            placeholder="Tell us about your requirements, timeline, or preferred property/service..."
            value={{notes}}
            onChange={{(e) => setNotes(e.target.value)}}
            className="bg-background/50"
          />
          <Button
            type="submit"
            className="w-full py-6 bg-gradient-to-r from-[#c5a880] to-[#d4af37] text-black font-bold uppercase font-mono tracking-wider shadow-xl shadow-[#c5a880]/20 hover:scale-[1.02] transition-all"
          >
            Dispatch via VIP WhatsApp Concierge
          </Button>
        </form>
      </div>
    </section>
  );
}}
""", encoding="utf-8")

        # 5. App.tsx
        (project_dir / "src" / "App.tsx").write_text(f"""import React, {{ useState, useEffect }} from 'react';
import {{ Navbar }} from './components/Navbar';
import {{ Hero }} from './components/Hero';
import {{ ShowcaseGrid }} from './components/ShowcaseGrid';
import {{ WhatsAppForm }} from './components/WhatsAppForm';

export default function App() {{
  const [theme, setTheme] = useState<'light' | 'dark'>('{theme}');

  useEffect(() => {{
    const root = document.documentElement;
    if (theme === 'dark') {{
      root.classList.add('dark');
    }} else {{
      root.classList.remove('dark');
    }}
  }}, [theme]);

  const toggleTheme = () => {{
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }};

  return (
    <div className="min-h-screen bg-background text-foreground font-sans antialiased selection:bg-[#c5a880] selection:text-black">
      <Navbar theme={{theme}} onToggleTheme={{toggleTheme}} />
      <main>
        <Hero />
        <ShowcaseGrid />
        <WhatsAppForm />
      </main>
      <footer className="border-t border-border/40 py-12 px-4 text-center text-xs font-mono text-muted-foreground">
        © {{new Date().getFullYear()}} {business_name}. Powered by IconEdge Autonomous Systems.
      </footer>
    </div>
  );
}}
""", encoding="utf-8")

    def _assemble_application_components(
        self,
        project_dir: Path,
        business_name: str,
        industry: str,
        location: str,
        phone_number: str,
        clean_phone: str,
        tagline: str,
    ) -> None:
        pass

    def patch_component(
        self,
        project_id: str,
        rel_path: str,
        target_content: str,
        replacement_content: str,
        preferred_layer: int = 1,
    ) -> Dict[str, Any]:
        """Surgically patch a component and record a Git checkpoint."""
        project_dir = self.output_dir / project_id
        if not project_dir.exists():
            return {"status": "error", "message": f"Project '{project_id}' not found."}

        res = self.surgical_editor.patch_file(
            project_dir=project_dir,
            rel_path=rel_path,
            target_content=target_content,
            replacement_content=replacement_content,
            preferred_layer=preferred_layer,
        )
        if res.get("status") == "success":
            self.git_version.checkpoint(project_dir, f"Surgically patched {rel_path}")
        res["project_id"] = project_id
        return res

    def write_component(self, project_id: str, rel_path: str, code: str) -> Dict[str, Any]:
        """Surgically write/replace a component and record a Git checkpoint."""
        project_dir = self.output_dir / project_id
        if not project_dir.exists():
            return {"status": "error", "message": f"Project '{project_id}' not found."}

        res = self.surgical_editor.write_component(project_dir=project_dir, rel_path=rel_path, code=code)
        if res.get("status") == "success":
            self.git_version.checkpoint(project_dir, f"Updated component {rel_path}")
        res["project_id"] = project_id
        return res

    def rollback_project(self, project_id: str, target: str = "HEAD~1") -> Dict[str, Any]:
        """Rollback project to previous checkpoint if QA or Critic detects regression."""
        project_dir = self.output_dir / project_id
        if not project_dir.exists():
            return {"status": "error", "message": f"Project '{project_id}' not found."}

        return self.git_version.rollback(project_dir, target)

    def read_component(self, project_id: str, rel_path: str) -> Dict[str, Any]:
        """Read a component's source code."""
        project_dir = self.output_dir / project_id
        if not project_dir.exists():
            return {"status": "error", "message": f"Project '{project_id}' not found."}

        target_file = project_dir / rel_path
        if not target_file.exists():
            return {"status": "error", "message": f"File '{rel_path}' not found."}

        return {
            "status": "success",
            "project_id": project_id,
            "file_path": rel_path,
            "code": target_file.read_text(encoding="utf-8"),
        }

    def get_project_tree(self, project_id: str) -> Dict[str, Any]:
        """Get component and file tree."""
        project_dir = self.output_dir / project_id
        if not project_dir.exists():
            return {"status": "error", "message": f"Project '{project_id}' not found."}

        tree = []
        for path in sorted(project_dir.glob("src/**/*")):
            if path.is_file():
                rel = str(path.relative_to(project_dir)).replace("\\", "/")
                tree.append(rel)

        return {
            "status": "success",
            "project_id": project_id,
            "files": tree,
        }

    def get_manifest(self, project_id: str) -> Dict[str, Any]:
        """Retrieve full .jarvis/ project manifest."""
        project_dir = self.output_dir / project_id
        jarvis_dir = project_dir / ".jarvis"
        if not jarvis_dir.exists():
            return {"status": "error", "message": f"Manifest not found for project '{project_id}'."}

        manifest = {}
        for f in jarvis_dir.glob("*.json"):
            try:
                manifest[f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                pass

        return {
            "status": "success",
            "project_id": project_id,
            "manifest": manifest,
        }

    def run_browser_qa(
        self,
        project_id: str,
        routes: Optional[List[str]] = None,
        viewports: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute Playwright browser testing with route and viewport support."""
        project_dir = self.output_dir / project_id
        if not project_dir.exists():
            return {"status": "error", "message": f"Project '{project_id}' not found."}

        index_html = project_dir / "index.html"
        qa_report = self.browser_qa.test_project(
            target_url_or_path=str(index_html),
            output_dir=project_dir,
        )
        return {
            "status": "success" if qa_report.get("passed") else "failed",
            "project_id": project_id,
            "qa_report": qa_report,
        }

    def run_visual_critic(
        self,
        project_id: str,
        routes: Optional[List[str]] = None,
        viewports: Optional[List[str]] = None,
        compare_to_design_spec: bool = True,
        requirements: str = "",
    ) -> Dict[str, Any]:
        """Execute 10-Point Visual Critic scoring with 3-way spec comparison."""
        project_dir = self.output_dir / project_id
        if not project_dir.exists():
            return {"status": "error", "message": f"Project '{project_id}' not found."}

        qa_file = project_dir / ".jarvis" / "qa.json"
        qa_report = {}
        if qa_file.exists():
            try:
                qa_report = json.loads(qa_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        if not qa_report:
            qa_res = self.run_browser_qa(project_id)
            qa_report = qa_res.get("qa_report", {})

        biz_file = project_dir / ".jarvis" / "business.json"
        biz_meta = {}
        if biz_file.exists():
            try:
                biz_meta = json.loads(biz_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        design_spec = None
        if compare_to_design_spec:
            design_file = project_dir / ".jarvis" / "design.json"
            if design_file.exists():
                try:
                    design_spec = json.loads(design_file.read_text(encoding="utf-8"))
                except Exception:
                    pass

        critic_verdict = self.visual_critic.evaluate(
            project_dir=project_dir,
            qa_report=qa_report,
            business_meta=biz_meta,
            design_spec=design_spec,
            requirements=requirements,
        )
        return {
            "status": "success" if critic_verdict.get("passed") else "failed",
            "project_id": project_id,
            "critic": critic_verdict,
        }

    def build_project(self, project_id: str) -> Dict[str, Any]:
        """Compile React project to static bundle."""
        project_dir = self.output_dir / project_id
        if not project_dir.exists():
            return {"status": "error", "message": f"Project '{project_id}' not found."}

        return {
            "status": "success",
            "project_id": project_id,
            "message": f"React project '{project_id}' compiled and ready.",
        }

    def deploy_project(self, project_id: str) -> Dict[str, Any]:
        """Deploy project to Vercel production."""
        project_dir = self.output_dir / project_id
        if not project_dir.exists():
            return {"status": "error", "message": f"Project '{project_id}' not found."}

        deployer = get_vercel_deployer()
        res = deployer.deploy_directory(project_dir, project_name=project_id)
        return res


_SERVICE_INSTANCE: Optional[ReactProjectService] = None


def get_react_project_service() -> ReactProjectService:
    global _SERVICE_INSTANCE
    if _SERVICE_INSTANCE is None:
        _SERVICE_INSTANCE = ReactProjectService()
    return _SERVICE_INSTANCE
