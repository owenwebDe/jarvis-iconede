"""Autonomous AI Web Architect & Multi-Industry Generator for IconEdge Technology.

Generates ultra-luxury, high-converting, mobile-first, zero-emoji client demo web applications
across ANY industry (Real Estate, Restaurants, Portfolios, SaaS, Clinics, Boutiques, Auto)
with complete interactive sections, theme switchers, modal dialogs, and WhatsApp direct checkout.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("demo_generator")

_DEMOS_DIR = Path(__file__).resolve().parent.parent / "data" / "demos"
_DEMOS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug or "demo"


def _clean_phone_number(phone: str) -> str:
    clean = re.sub(r"[^\d+]", "", phone)
    if clean.startswith("+"):
        clean = clean[1:]
    return clean or "2348000000000"


# Verified High-Res Architectural & Luxury Unsplash Asset Library
UNSPLASH_ASSETS = {
    "portraits": [
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=800&q=85",
    ],
    "creative_work": [
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1558655146-d09347e92766?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1542744094-3a31f272c490?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1600132806370-bf17e65e942f?auto=format&fit=crop&w=1200&q=85",
    ],
    "real_estate": [
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1600&q=85",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=85",
    ],
    "food": [
        "https://images.unsplash.com/photo-1558030006-450675393462?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=85",
    ],
    "tech_analytics": [
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=85",
    ],
    "fashion": [
        "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=1200&q=85",
    ],
    "clinic": [
        "https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=1200&q=85",
    ],
}


class DemoGeneratorService:
    """Autonomous AI Web Architect & Multi-Industry Generator."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or _DEMOS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")

        self.clients = []
        if self.groq_key:
            self.clients.append({
                "client": OpenAI(api_key=self.groq_key, base_url="https://api.groq.com/openai/v1", timeout=30.0),
                "model": "qwen/qwen3.6-27b",
                "provider": "Groq",
            })
        if self.openrouter_key:
            self.clients.append({
                "client": OpenAI(
                    api_key=self.openrouter_key,
                    base_url="https://openrouter.ai/api/v1",
                    default_headers={"HTTP-Referer": "https://jarvis.iconedge.com", "X-Title": "Jarvis Autonomous Web Architect"},
                    timeout=30.0,
                ),
                "model": "openai/gpt-4o-mini",
                "provider": "OpenRouter",
            })
        if self.deepseek_key:
            self.clients.append({
                "client": OpenAI(api_key=self.deepseek_key, base_url="https://api.deepseek.com/v1", timeout=30.0),
                "model": "deepseek-chat",
                "provider": "DeepSeek",
            })

    def _generate_with_ai(
        self,
        business_name: str,
        industry: str,
        location: str,
        phone_number: str,
        tagline: str,
        default_theme: str = "light",
    ) -> Optional[str]:
        """Call LLM to write a completely bespoke, pixel-perfect single-page web app."""
        if not self.clients:
            return None

        is_portfolio = any(k in f"{business_name} {industry} {tagline}".lower() for k in ["portfolio", "resume", "cv", "designer", "developer", "creator", "artist"])
        is_analytics = any(k in f"{business_name} {industry} {tagline}".lower() for k in ["analytic", "data", "metric", "saas", "dashboard", "news"])
        is_real_estate = any(k in f"{business_name} {industry} {tagline}".lower() for k in ["estate", "home", "property", "villa", "penthouse", "ordanic"])
        is_restaurant = any(k in f"{business_name} {industry} {tagline}".lower() for k in ["restaurant", "dining", "kitchen", "bistro", "cafe", "food", "grill", "menu"])

        prompt = f"""You are the world's elite Lead Creative Front-End Architect at IconEdge Technologies.
You act as a COMPILER. Generate a complete, visually breathtaking, production-ready Single Page Web Application with full HTML body, Tailwind CSS, FontAwesome 6 icons, and interactive JavaScript for:
- Client / Brand Name: {business_name}
- Industry / Specialty: {industry}
- Location: {location}
- Phone / WhatsApp: {phone_number}
- Tagline / Brief: {tagline}
- Default Theme: {default_theme}

CRITICAL ARCHITECTURAL RULES:
1. USE TAILWIND CSS CDN: Include `<script src="https://cdn.tailwindcss.com"></script>`.
2. KEEP `<style>` UNDER 30 LINES: Do NOT write massive custom CSS. Use Tailwind classes directly on HTML elements for layout, colors, typography, and responsive grids. Only use `<style>` for `.reveal`, `.active`, and custom keyframe animations.
3. COMPLETE RICH HTML BODY: You MUST write the complete, non-empty `<body>` with all 10 sections in this exact DOM order:
   1. [StatusTicker] — Top scrolling announcement ticker with pulsing dot.
   2. [GlassNavbar] — Sticky glassmorphism header with logo, navigation links, 1-click theme toggle, and WhatsApp CTA.
   3. [HeroSection] — Bold headline (`text-4xl md:text-6xl font-bold`), subheadline, Unsplash backdrop, trust metrics, and dual action buttons.
   4. [StatsBar] — 4 interactive KPI metric cards (`data-counter-target`) that count up dynamically on scroll.
   5. [ShowcaseGrid] — Interactive 4-card filterable showcase grid (portfolio projects / properties / menu items / services) with badges, price/metrics, and hover zoom.
   6. [FeaturesMatrix] — 6-card feature/service grid with FontAwesome 6 vector icons and hover-lift effect.
   7. [Testimonials] — 3 verified client reviews with star ratings and executive avatars.
   8. [WhatsAppContactForm] — Interactive inquiry form that automatically generates pre-filled WhatsApp links to `{phone_number}`.
   9. [ExecutiveFooter] — Rich footer with brand bio, quick links, contact info, and copyright.
   10. [FixedMobileBottomBar] — Sticky bottom thumb-zone bar (Call, WhatsApp, Book) visible only on mobile screens (`md:hidden`).
   11. [LightboxModal] — Quick preview modal for viewing card details.

4. EMBEDDED JAVASCRIPT ENGINE (Place before `</body>`):
   - `IntersectionObserver` scroll reveals: elements with `.reveal` gain `.active` (`opacity: 1; transform: translateY(0)`).
   - Dynamic Number Counters: smoothly animate numbers in `data-counter-target` from 0 when scrolled into view.
   - 1-Click Dark/Light Theme Switcher: toggle `dark` class on `<html>` and save to `localStorage`.

5. STRICT ZERO EMOJIS: Use FontAwesome 6 vector icons only (`<i class="fa-solid fa-..."></i>`).
6. REAL BESPOKE COPY: Tailored specifically for {business_name} in {location}. No filler 'lorem ipsum'.

OUTPUT FORMAT:
Return ONLY the complete raw HTML code starting with `<!DOCTYPE html>` and ending with `</html>`. Do NOT wrap in markdown backticks.
"""

        for c_entry in self.clients:
            client = c_entry["client"]
            model = c_entry["model"]
            provider = c_entry["provider"]
            try:
                logger.info(f"Generating bespoke AI website for {business_name} ({industry}) via {provider} ({model})...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a world-class principal frontend engineer and UI/UX designer. You write complete, production-ready, beautiful HTML/Tailwind/JS applications with full HTML body content, rich sections, no shortcuts, no placeholder comments, and strictly zero emojis. Output pure HTML directly.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=8000,
                )
                content = response.choices[0].message.content.strip()
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                if "```html" in content:
                    m = re.search(r"```html\s*(.*?)\s*```", content, flags=re.DOTALL)
                    if m:
                        content = m.group(1).strip()
                elif "```" in content:
                    m = re.search(r"```\s*(<!DOCTYPE html>.*?)```", content, flags=re.DOTALL | re.IGNORECASE)
                    if m:
                        content = m.group(1).strip()

                doctype_idx = content.lower().find("<!doctype html>")
                if doctype_idx != -1:
                    html_end = content.lower().rfind("</html>")
                    if html_end != -1:
                        content = content[doctype_idx:html_end + 7].strip()

                if ("<!doctype html>" in content.lower() or "<html" in content.lower()) and "<body" in content.lower() and len(content) > 3000:
                    if "</html>" not in content.lower():
                        content += "\n</script>\n</body>\n</html>"
                    if "<!doctype html>" not in content.lower():
                        content = "<!DOCTYPE html>\n" + content
                    logger.info(f"AI Website generated successfully via {provider} ({len(content)} chars)")
                    return content
            except Exception as e:
                logger.error(f"AI website generation failed via {provider}: {e}")
                continue

        return None

    def generate_website_demo(
        self,
        business_name: str,
        industry: str = "auto",
        location: str = "Abuja, Nigeria",
        phone_number: str = "+234 814 000 7788",
        tagline: str = "",
        default_theme: str = "light",
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate bespoke demo website using AI Architect with intelligent fallback."""
        demo_id = f"{_slugify(business_name)}-{uuid.uuid4().hex[:6]}"
        demo_folder = self.output_dir / demo_id
        demo_folder.mkdir(parents=True, exist_ok=True)

        clean_industry = industry.lower()
        if clean_industry in ("luxoria", "prospera"):
            pass
        elif any(k in f"{business_name} {clean_industry} {tagline}".lower() for k in ["estate", "home", "property", "villa", "penthouse", "ordanic", "realty"]):
            clean_industry = "real_estate"
        elif any(k in f"{business_name} {clean_industry} {tagline}".lower() for k in ["restaurant", "dining", "kitchen", "bistro", "cafe", "food", "grill", "menu"]):
            clean_industry = "restaurant"
        elif any(k in f"{business_name} {clean_industry} {tagline}".lower() for k in ["portfolio", "resume", "designer", "developer", "creator"]):
            clean_industry = "portfolio"
        elif any(k in f"{business_name} {clean_industry} {tagline}".lower() for k in ["clinic", "hospital", "doctor", "health", "dental", "aesthetic"]):
            clean_industry = "clinic"
        elif any(k in f"{business_name} {clean_industry} {tagline}".lower() for k in ["fashion", "boutique", "apparel", "clothing", "wear"]):
            clean_industry = "fashion"
        elif any(k in f"{business_name} {clean_industry} {tagline}".lower() for k in ["saas", "analytic", "data", "software", "dashboard"]):
            clean_industry = "saas"

        # 1. Template-First Architecture:
        # Check if a dedicated production-grade template exists for this industry
        template_content = self._get_hydrated_template(
            industry=clean_industry,
            business_name=business_name,
            location=location,
            phone_number=phone_number,
            tagline=tagline,
        )

        if template_content:
            logger.info(f"Loaded and hydrated master template for industry: {clean_industry}")
            html_content = template_content
            engine_used = f"template_{clean_industry}"
        else:
            # 2. If NO template exists, call AI Architect to build 100% bespoke from scratch
            logger.info(f"No pre-built template for '{clean_industry}'. Calling AI Web Architect from scratch...")
            html_content = self._generate_with_ai(
                business_name=business_name,
                industry=clean_industry,
                location=location,
                phone_number=phone_number,
                tagline=tagline,
                default_theme=default_theme,
            )

            # 3. Fallback: If AI returns short snippet, use master generator
            if not html_content or len(html_content) < 2500:
                logger.info(f"Using Master Production Engine fallback for industry: {clean_industry}")
                html_content = self._build_production_html(
                    business_name=business_name,
                    industry=clean_industry,
                    location=location,
                    phone_number=phone_number,
                    tagline=tagline,
                    default_theme=default_theme,
                )
            engine_used = "ai_bespoke_architect"

        index_file = demo_folder / "index.html"
        index_file.write_text(html_content, encoding="utf-8")

        meta = {
            "demo_id": demo_id,
            "business_name": business_name,
            "category": clean_industry,
            "location": location,
            "phone_number": phone_number,
            "files": ["index.html"],
            "entrypoint": str(index_file),
            "directory": str(demo_folder),
            "engine": engine_used,
        }
        (demo_folder / "demo.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return meta

    def _get_hydrated_template(
        self,
        industry: str,
        business_name: str,
        location: str,
        phone_number: str,
        tagline: str,
        variant: Optional[str] = None,
    ) -> Optional[str]:
        """Fetch and hydrate a pre-built master template if one exists."""
        template_map = {
            "real_estate": "real_estate_prospera.html",
            "prospera": "real_estate_prospera.html",
            "luxoria": "real_estate_luxoria.html",
            "restaurant": "restaurant_artisanal.html",
            "portfolio": "portfolio_master.html",
        }
        if variant and variant in template_map:
            tpl_file = template_map[variant]
        else:
            tpl_file = template_map.get(industry)
            
        if not tpl_file:
            return None

        tpl_path = Path(__file__).resolve().parent.parent / "templates" / tpl_file
        if not tpl_path.exists():
            return None

        clean_phone = _clean_phone_number(phone_number)
        content = tpl_path.read_text(encoding="utf-8")
        
        # Dual-case replacement for complete template compatibility
        content = content.replace("{{ business_name }}", business_name)
        content = content.replace("{{ BUSINESS_NAME }}", business_name)
        content = content.replace("{{ location }}", location)
        content = content.replace("{{ LOCATION }}", location)
        content = content.replace("{{ phone_number }}", phone_number)
        content = content.replace("{{ PHONE_NUMBER }}", phone_number)
        content = content.replace("{{ clean_phone }}", clean_phone)
        content = content.replace("{{ PHONE_CLEAN }}", clean_phone)
        
        default_tagline = f"Executive Architect & Digital Technologist in {location}." if industry == "portfolio" else f"Curating architectural marvels & prime properties in {location}."
        final_tagline = tagline if tagline and "tagline" not in tagline.lower() else default_tagline
        content = content.replace("{{ tagline }}", final_tagline)
        content = content.replace("{{ TAGLINE }}", final_tagline)
        return content

    def generate_portfolio_demo(
        self,
        business_name: str = "Owen",
        location: str = "Abuja, Nigeria",
        phone_number: str = "+234 800 000 0000",
        tagline: str = "Executive Full-Stack AI Engineer & Creative Technologist",
        default_theme: str = "dark",
    ) -> Dict[str, Any]:
        """Generate bespoke executive portfolio web application."""
        return self.generate_website_demo(
            business_name=business_name,
            industry="portfolio",
            location=location,
            phone_number=phone_number,
            tagline=tagline,
            default_theme=default_theme,
        )

    def generate_luxoria_demo(
        self,
        business_name: str = "Ordanic Homes",
        location: str = "Maitama, Guzape & Jabi, Abuja",
        phone_number: str = "+234 814 000 7788",
        tagline: str = "Architectural marvels for connoisseurs of distinction across Abuja.",
        default_theme: str = "light",
    ) -> Dict[str, Any]:
        """Generate bespoke luxury Real Estate demo using Luxoria architectural template."""
        return self.generate_website_demo(
            business_name=business_name,
            industry="luxoria",
            location=location,
            phone_number=phone_number,
            tagline=tagline,
            default_theme=default_theme,
        )

    def generate_real_estate_demo(
        self,
        business_name: str = "Ordanic Homes",
        location: str = "Maitama, Guzape & Jabi, Abuja",
        phone_number: str = "+234 814 000 7788",
        tagline: str = "Curating architectural marvels, luxury villas & premium real estate investments in Abuja.",
        default_theme: str = "light",
    ) -> Dict[str, Any]:
        """Generate ultra-luxury real estate web application."""
        return self.generate_website_demo(
            business_name=business_name,
            industry="real_estate",
            location=location,
            phone_number=phone_number,
            tagline=tagline,
            default_theme=default_theme,
        )

    def generate_restaurant_demo(
        self,
        business_name: str = "Kitchen Glory",
        location: str = "Wuse 2, Abuja",
        phone_number: str = "+234 800 000 0000",
        tagline: str = "Exquisite Dining & Fast Online Ordering",
        default_theme: str = "light",
    ) -> Dict[str, Any]:
        """Generate ultra-luxury modern restaurant web application."""
        return self.generate_website_demo(
            business_name=business_name,
            industry="restaurant",
            location=location,
            phone_number=phone_number,
            tagline=tagline,
            default_theme=default_theme,
        )

    def _build_production_html(
        self,
        business_name: str,
        industry: str,
        location: str,
        phone_number: str,
        tagline: str,
        default_theme: str,
    ) -> str:
        """Route to specialized master HTML generators."""
        if industry == "real_estate":
            return self._build_real_estate_html(business_name, location, phone_number, tagline, default_theme)
        elif industry == "restaurant":
            return self._build_restaurant_html(business_name, location, phone_number, tagline, default_theme)
        elif industry == "portfolio":
            return self._build_portfolio_html(business_name, location, phone_number, tagline, default_theme)
        else:
            return self._build_real_estate_html(business_name, location, phone_number, tagline, default_theme)

    def _build_real_estate_html(
        self,
        business_name: str,
        location: str,
        phone_number: str,
        tagline: str,
        theme: str = "light",
    ) -> str:
        """Generate complete, ultra-luxury Real Estate web application."""
        clean_phone = _clean_phone_number(phone_number)
        tag = tagline or "Curating architectural marvels, luxury villas & premium real estate investments."

        return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth" id="html-root">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{business_name} • Ultra-Luxury Real Estate & Residences</title>
  <meta name="description" content="{tag} Located in {location}." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Syne:wght@500;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" />
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            serif: ['Playfair Display', 'serif'],
            sans: ['Plus Jakarta Sans', 'sans-serif'],
            display: ['Syne', 'sans-serif'],
          }},
          colors: {{
            gold: {{ 400: '#e5c378', 500: '#d4af37', 600: '#aa8c2c' }},
            obsidian: '#080a10',
            cardDark: '#0e111a',
          }}
        }}
      }}
    }}
  </script>
  <style>
    .glass-nav {{
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
    }}
    .property-card:hover .card-img {{
      transform: scale(1.06);
    }}
  </style>
</head>
<body class="font-sans bg-[#faf9f5] dark:bg-[#07090e] text-[#12151e] dark:text-[#f0f2f8] antialiased transition-colors duration-300">

  <!-- TOP ANNOUNCEMENT TICKER -->
  <div class="bg-black text-white text-xs py-2 px-4 text-center tracking-widest uppercase font-display border-b border-white/10 flex justify-center items-center gap-3">
    <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
    <span>Private Collection 2026 • Exclusive Inquiries Available for {location}</span>
  </div>

  <!-- NAVIGATION -->
  <nav class="sticky top-0 z-40 glass-nav bg-[#faf9f5]/85 dark:bg-[#07090e]/85 border-b border-black/5 dark:border-white/10 transition-colors">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
      <a href="#" class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gold-500/10 border border-gold-500/30 flex items-center justify-center text-gold-500 font-serif font-bold text-xl">
          <i class="fa-solid fa-landmark"></i>
        </div>
        <div>
          <span class="font-serif font-bold text-xl tracking-tight text-black dark:text-white block leading-none">{business_name}</span>
          <span class="text-[10px] uppercase tracking-[0.2em] text-neutral-500 font-display block mt-1">Private Residences</span>
        </div>
      </a>

      <!-- Desktop Links -->
      <div class="hidden md:flex items-center gap-8 text-sm font-medium">
        <a href="#properties" class="hover:text-gold-500 transition">Estates & Villas</a>
        <a href="#amenities" class="hover:text-gold-500 transition">Curated Living</a>
        <a href="#floorplans" class="hover:text-gold-500 transition">Floor Plans</a>
        <a href="#craftsmanship" class="hover:text-gold-500 transition">Craftsmanship</a>
        <a href="#inquiry" class="hover:text-gold-500 transition">Private Inspection</a>
      </div>

      <!-- Action Area -->
      <div class="flex items-center gap-3">
        <!-- Theme Toggle Button -->
        <button id="theme-toggle" class="w-10 h-10 rounded-full border border-black/10 dark:border-white/15 flex items-center justify-center text-neutral-600 dark:text-neutral-300 hover:text-gold-500 transition" title="Toggle Light/Dark Theme">
          <i class="fa-solid fa-moon dark:hidden"></i>
          <i class="fa-solid fa-sun hidden dark:block text-gold-400"></i>
        </button>

        <a href="https://wa.me/{clean_phone}?text=Hello%20{business_name},%20I%20am%20interested%20in%20arranging%20a%20private%20inspection%20tour." target="_blank" class="hidden sm:inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-gold-500 hover:bg-gold-600 text-black font-semibold text-xs tracking-wider uppercase transition shadow-lg shadow-gold-500/20">
          <i class="fa-brands fa-whatsapp text-sm"></i>
          <span>VIP Concierge</span>
        </a>
      </div>
    </div>
  </nav>

  <!-- HERO SECTION -->
  <section class="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
    <!-- Background Image with Film Grain Overlay -->
    <div class="absolute inset-0 z-0">
      <img src="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1920&q=85" alt="Luxury Villa Architecture" class="w-full h-full object-cover object-center scale-105 transition duration-1000" />
      <div class="absolute inset-0 bg-gradient-to-t from-[#faf9f5] dark:from-[#07090e] via-black/50 to-black/70"></div>
    </div>

    <div class="relative z-10 max-w-5xl mx-auto px-4 py-24 text-center text-white">
      <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-gold-400 text-xs uppercase tracking-widest font-display mb-6">
        <i class="fa-solid fa-gem text-xs"></i>
        <span>Prime Architectural Collection • {location}</span>
      </div>

      <h1 class="font-serif text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight mb-6 leading-[1.1]">
        Architectural Marvels <br />
        <span class="italic font-normal text-gold-400">Crafted for Posterity</span>
      </h1>

      <p class="max-w-2xl mx-auto text-base sm:text-lg text-neutral-200 font-light mb-10 leading-relaxed">
        {tag} Discover ultra-exclusive penthouses, private villas, and bespoke residential sanctuaries.
      </p>

      <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
        <a href="#properties" class="w-full sm:w-auto px-8 py-4 rounded-full bg-gold-500 hover:bg-gold-600 text-black font-bold text-sm tracking-wider uppercase transition shadow-xl shadow-gold-500/25">
          Explore Residences
        </a>
        <a href="#inquiry" class="w-full sm:w-auto px-8 py-4 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/30 text-white font-semibold text-sm tracking-wider uppercase transition">
          Book Private Tour
        </a>
      </div>
    </div>
  </section>

  <!-- KEY METRICS & CREDENTIALS BAR -->
  <section class="border-y border-black/10 dark:border-white/10 bg-white/50 dark:bg-[#0c0f17]/50 backdrop-blur-md py-10">
    <div class="max-w-7xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
      <div>
        <div class="font-serif text-3xl sm:text-4xl font-bold text-gold-500 mb-1">₦65B+</div>
        <div class="text-xs uppercase tracking-widest text-neutral-500 font-display">Portfolio Delivered</div>
      </div>
      <div>
        <div class="font-serif text-3xl sm:text-4xl font-bold text-gold-500 mb-1">100%</div>
        <div class="text-xs uppercase tracking-widest text-neutral-500 font-display">C of O Title Verification</div>
      </div>
      <div>
        <div class="font-serif text-3xl sm:text-4xl font-bold text-gold-500 mb-1">18+</div>
        <div class="text-xs uppercase tracking-widest text-neutral-500 font-display">Architectural Awards</div>
      </div>
      <div>
        <div class="font-serif text-3xl sm:text-4xl font-bold text-gold-500 mb-1">24/7</div>
        <div class="text-xs uppercase tracking-widest text-neutral-500 font-display">Private VIP Concierge</div>
      </div>
    </div>
  </section>

  <!-- FEATURED PROPERTIES SECTION -->
  <section id="properties" class="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex flex-col md:flex-row md:items-end justify-between mb-16">
      <div>
        <span class="text-xs uppercase tracking-[0.25em] text-gold-500 font-display font-semibold block mb-2">Exclusive Portfolio</span>
        <h2 class="font-serif text-3xl sm:text-5xl font-bold tracking-tight">Prime Residences</h2>
      </div>

      <!-- Filter Tabs -->
      <div class="flex items-center gap-2 mt-6 md:mt-0 overflow-x-auto pb-2" id="property-filters">
        <button class="filter-btn active px-5 py-2 rounded-full text-xs font-semibold uppercase tracking-wider bg-black dark:bg-white text-white dark:text-black transition" onclick="filterProperties('all', this)">All</button>
        <button class="filter-btn px-5 py-2 rounded-full text-xs font-semibold uppercase tracking-wider bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 transition" onclick="filterProperties('villa', this)">Villas</button>
        <button class="filter-btn px-5 py-2 rounded-full text-xs font-semibold uppercase tracking-wider bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 transition" onclick="filterProperties('penthouse', this)">Penthouses</button>
        <button class="filter-btn px-5 py-2 rounded-full text-xs font-semibold uppercase tracking-wider bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 transition" onclick="filterProperties('estate', this)">Mansions</button>
      </div>
    </div>

    <!-- Properties Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" id="property-grid">

      <!-- Property Card 1 -->
      <div class="property-item villa rounded-3xl overflow-hidden bg-white dark:bg-cardDark border border-black/10 dark:border-white/10 shadow-xl transition hover:-translate-y-1 duration-300">
        <div class="relative h-72 overflow-hidden">
          <img src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=85" alt="The Elysian Villa" class="card-img w-full h-full object-cover transition duration-700" />
          <div class="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/70 backdrop-blur-md text-white text-[10px] font-display uppercase tracking-widest">Maitama Prime</div>
          <div class="absolute bottom-4 right-4 px-3 py-1 rounded-full bg-emerald-500 text-black font-bold text-xs uppercase tracking-wider">Available</div>
        </div>
        <div class="p-6">
          <div class="flex justify-between items-start mb-2">
            <h3 class="font-serif text-2xl font-bold">The Elysian Villa</h3>
            <span class="text-gold-500 font-bold text-lg font-serif">₦1.85B</span>
          </div>
          <p class="text-sm text-neutral-500 dark:text-neutral-400 mb-6">7-Bedroom Masterpiece with infinity pool, private elevator & 12-car subterranean garage.</p>
          <div class="flex items-center justify-between border-t border-black/10 dark:border-white/10 pt-4 text-xs text-neutral-600 dark:text-neutral-300 font-medium">
            <span><i class="fa-solid fa-bed me-1.5 text-gold-500"></i>7 Beds</span>
            <span><i class="fa-solid fa-bath me-1.5 text-gold-500"></i>8 Baths</span>
            <span><i class="fa-solid fa-vector-square me-1.5 text-gold-500"></i>1,450 sqm</span>
          </div>
          <button onclick="openModal('The Elysian Villa', '₦1.85B', 'Maitama, Abuja', '7 Beds • 8 Baths • 1,450 sqm', 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=85')" class="mt-6 w-full py-3 rounded-xl bg-black/5 dark:bg-white/10 hover:bg-gold-500 hover:text-black dark:hover:bg-gold-500 dark:hover:text-black font-semibold text-xs tracking-wider uppercase transition">
            View Floor Plan & Specs
          </button>
        </div>
      </div>

      <!-- Property Card 2 -->
      <div class="property-item penthouse rounded-3xl overflow-hidden bg-white dark:bg-cardDark border border-black/10 dark:border-white/10 shadow-xl transition hover:-translate-y-1 duration-300">
        <div class="relative h-72 overflow-hidden">
          <img src="https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=85" alt="Aura Sky Penthouse" class="card-img w-full h-full object-cover transition duration-700" />
          <div class="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/70 backdrop-blur-md text-white text-[10px] font-display uppercase tracking-widest">Guzape Hills</div>
          <div class="absolute bottom-4 right-4 px-3 py-1 rounded-full bg-gold-500 text-black font-bold text-xs uppercase tracking-wider">Private Sale</div>
        </div>
        <div class="p-6">
          <div class="flex justify-between items-start mb-2">
            <h3 class="font-serif text-2xl font-bold">Aura Sky Penthouse</h3>
            <span class="text-gold-500 font-bold text-lg font-serif">₦950M</span>
          </div>
          <p class="text-sm text-neutral-500 dark:text-neutral-400 mb-6">360-degree panoramic city views, heated rooftop plunge pool & bespoke Italian marble kitchen.</p>
          <div class="flex items-center justify-between border-t border-black/10 dark:border-white/10 pt-4 text-xs text-neutral-600 dark:text-neutral-300 font-medium">
            <span><i class="fa-solid fa-bed me-1.5 text-gold-500"></i>5 Beds</span>
            <span><i class="fa-solid fa-bath me-1.5 text-gold-500"></i>6 Baths</span>
            <span><i class="fa-solid fa-vector-square me-1.5 text-gold-500"></i>820 sqm</span>
          </div>
          <button onclick="openModal('Aura Sky Penthouse', '₦950M', 'Guzape, Abuja', '5 Beds • 6 Baths • 820 sqm', 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=85')" class="mt-6 w-full py-3 rounded-xl bg-black/5 dark:bg-white/10 hover:bg-gold-500 hover:text-black dark:hover:bg-gold-500 dark:hover:text-black font-semibold text-xs tracking-wider uppercase transition">
            View Floor Plan & Specs
          </button>
        </div>
      </div>

      <!-- Property Card 3 -->
      <div class="property-item estate rounded-3xl overflow-hidden bg-white dark:bg-cardDark border border-black/10 dark:border-white/10 shadow-xl transition hover:-translate-y-1 duration-300">
        <div class="relative h-72 overflow-hidden">
          <img src="https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=800&q=85" alt="The Grand Regent Estate" class="card-img w-full h-full object-cover transition duration-700" />
          <div class="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/70 backdrop-blur-md text-white text-[10px] font-display uppercase tracking-widest">Asokoro Ridge</div>
          <div class="absolute bottom-4 right-4 px-3 py-1 rounded-full bg-emerald-500 text-black font-bold text-xs uppercase tracking-wider">Available</div>
        </div>
        <div class="p-6">
          <div class="flex justify-between items-start mb-2">
            <h3 class="font-serif text-2xl font-bold">Grand Regent Estate</h3>
            <span class="text-gold-500 font-bold text-lg font-serif">₦3.2B</span>
          </div>
          <p class="text-sm text-neutral-500 dark:text-neutral-400 mb-6">Palatial ambassadorial residence with private helipad, biometric fortress security & smart cinema.</p>
          <div class="flex items-center justify-between border-t border-black/10 dark:border-white/10 pt-4 text-xs text-neutral-600 dark:text-neutral-300 font-medium">
            <span><i class="fa-solid fa-bed me-1.5 text-gold-500"></i>8 Beds</span>
            <span><i class="fa-solid fa-bath me-1.5 text-gold-500"></i>10 Baths</span>
            <span><i class="fa-solid fa-vector-square me-1.5 text-gold-500"></i>2,800 sqm</span>
          </div>
          <button onclick="openModal('Grand Regent Estate', '₦3.2B', 'Asokoro, Abuja', '8 Beds • 10 Baths • 2,800 sqm', 'https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=800&q=85')" class="mt-6 w-full py-3 rounded-xl bg-black/5 dark:bg-white/10 hover:bg-gold-500 hover:text-black dark:hover:bg-gold-500 dark:hover:text-black font-semibold text-xs tracking-wider uppercase transition">
            View Floor Plan & Specs
          </button>
        </div>
      </div>

    </div>
  </section>

  <!-- AMENITIES & CRAFTSMANSHIP SECTION -->
  <section id="amenities" class="py-24 bg-black/5 dark:bg-white/5 border-y border-black/5 dark:border-white/10">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-3xl mx-auto mb-20">
        <span class="text-xs uppercase tracking-[0.25em] text-gold-500 font-display font-semibold block mb-2">Uncompromising Standards</span>
        <h2 class="font-serif text-3xl sm:text-5xl font-bold tracking-tight mb-4">Curated Luxury Finishes</h2>
        <p class="text-neutral-500 dark:text-neutral-400 text-sm sm:text-base">Every residence by {business_name} integrates European architectural finishes, biometric privacy, and private amenities.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div class="p-8 rounded-3xl bg-white dark:bg-cardDark border border-black/5 dark:border-white/10">
          <div class="w-12 h-12 rounded-2xl bg-gold-500/10 text-gold-500 flex items-center justify-center text-xl mb-6"><i class="fa-solid fa-fingerprint"></i></div>
          <h4 class="font-serif text-xl font-bold mb-2">Biometric Fortress Security</h4>
          <p class="text-sm text-neutral-500 dark:text-neutral-400">24/7 AI perimeter surveillance, biometric keyless access, and armored security perimeters.</p>
        </div>
        <div class="p-8 rounded-3xl bg-white dark:bg-cardDark border border-black/5 dark:border-white/10">
          <div class="w-12 h-12 rounded-2xl bg-gold-500/10 text-gold-500 flex items-center justify-center text-xl mb-6"><i class="fa-solid fa-water-ladder"></i></div>
          <h4 class="font-serif text-xl font-bold mb-2">Private Infinity Pools</h4>
          <p class="text-sm text-neutral-500 dark:text-neutral-400">Heated temperature-controlled pools with submerged sun-loungers and automated filtration.</p>
        </div>
        <div class="p-8 rounded-3xl bg-white dark:bg-cardDark border border-black/5 dark:border-white/10">
          <div class="w-12 h-12 rounded-2xl bg-gold-500/10 text-gold-500 flex items-center justify-center text-xl mb-6"><i class="fa-solid fa-solar-panel"></i></div>
          <h4 class="font-serif text-xl font-bold mb-2">Uninterrupted Smart Power</h4>
          <p class="text-sm text-neutral-500 dark:text-neutral-400">Industrial solar microgrids paired with high-capacity soundproof hybrid energy backup.</p>
        </div>
        <div class="p-8 rounded-3xl bg-white dark:bg-cardDark border border-black/5 dark:border-white/10">
          <div class="w-12 h-12 rounded-2xl bg-gold-500/10 text-gold-500 flex items-center justify-center text-xl mb-6"><i class="fa-solid fa-kitchen-set"></i></div>
          <h4 class="font-serif text-xl font-bold mb-2">Italian Marble & Miele</h4>
          <p class="text-sm text-neutral-500 dark:text-neutral-400">Custom imported Calacatta marble countertops, bespoke cabinetry & integrated Miele appliances.</p>
        </div>
        <div class="p-8 rounded-3xl bg-white dark:bg-cardDark border border-black/5 dark:border-white/10">
          <div class="w-12 h-12 rounded-2xl bg-gold-500/10 text-gold-500 flex items-center justify-center text-xl mb-6"><i class="fa-solid fa-elevator"></i></div>
          <h4 class="font-serif text-xl font-bold mb-2">Private Schindler Elevators</h4>
          <p class="text-sm text-neutral-500 dark:text-neutral-400">Dedicated private lift serving all levels from subterranean parking to rooftop sky lounges.</p>
        </div>
        <div class="p-8 rounded-3xl bg-white dark:bg-cardDark border border-black/5 dark:border-white/10">
          <div class="w-12 h-12 rounded-2xl bg-gold-500/10 text-gold-500 flex items-center justify-center text-xl mb-6"><i class="fa-solid fa-bell-concierge"></i></div>
          <h4 class="font-serif text-xl font-bold mb-2">Private Chauffeur & Valet</h4>
          <p class="text-sm text-neutral-500 dark:text-neutral-400">On-demand executive fleet management, private airport transit, and residential concierge.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- TESTIMONIALS SECTION -->
  <section class="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center max-w-2xl mx-auto mb-16">
      <span class="text-xs uppercase tracking-[0.25em] text-gold-500 font-display font-semibold block mb-2">Distinguished Patrons</span>
      <h2 class="font-serif text-3xl sm:text-5xl font-bold tracking-tight">Verified Buyer Acclaim</h2>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-cardDark border border-black/10 dark:border-white/10 shadow-lg">
        <div class="flex text-gold-500 mb-4 text-xs gap-1">
          <i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i>
        </div>
        <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-6 italic">"{business_name} delivered our Maitama villa with unmatched finish quality and strict attention to privacy. The title handover was seamless."</p>
        <div class="flex items-center gap-3">
          <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=120&q=85" alt="Dr. Aliyu B." class="w-10 h-10 rounded-full object-cover" />
          <div>
            <div class="font-bold text-xs">Dr. Aliyu B.</div>
            <div class="text-[10px] text-neutral-500">Maitama Resident</div>
          </div>
        </div>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-cardDark border border-black/10 dark:border-white/10 shadow-lg">
        <div class="flex text-gold-500 mb-4 text-xs gap-1">
          <i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i>
        </div>
        <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-6 italic">"The architectural detailing and solar infrastructure are phenomenal. Best real estate investment decision in Abuja."</p>
        <div class="flex items-center gap-3">
          <img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=120&q=85" alt="Mrs. Folashade A." class="w-10 h-10 rounded-full object-cover" />
          <div>
            <div class="font-bold text-xs">Mrs. Folashade A.</div>
            <div class="text-[10px] text-neutral-500">Guzape Penthouse Owner</div>
          </div>
        </div>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-cardDark border border-black/10 dark:border-white/10 shadow-lg">
        <div class="flex text-gold-500 mb-4 text-xs gap-1">
          <i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i>
        </div>
        <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-6 italic">"Executive concierge and post-handover property maintenance are 5-star standard. Highly recommended for diaspora investors."</p>
        <div class="flex items-center gap-3">
          <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=85" alt="Ambassador K. Davies" class="w-10 h-10 rounded-full object-cover" />
          <div>
            <div class="font-bold text-xs">Ambassador K. Davies</div>
            <div class="text-[10px] text-neutral-500">Asokoro Diplomatic Quarter</div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- PRIVATE INSPECTION BOOKING SECTION -->
  <section id="inquiry" class="py-24 bg-black text-white relative overflow-hidden">
    <div class="max-w-5xl mx-auto px-4 relative z-10">
      <div class="text-center max-w-2xl mx-auto mb-12">
        <span class="text-xs uppercase tracking-[0.25em] text-gold-400 font-display font-semibold block mb-2">By Confidential Appointment</span>
        <h2 class="font-serif text-3xl sm:text-5xl font-bold tracking-tight">Schedule Private Inspection</h2>
        <p class="text-neutral-400 text-sm mt-3">Arrange a private in-person walkthrough or live virtual inspection with our Senior Property Partner.</p>
      </div>

      <form id="inspection-form" onsubmit="handleInspectionSubmit(event)" class="max-w-2xl mx-auto bg-white/5 backdrop-blur-xl border border-white/10 p-8 sm:p-10 rounded-3xl space-y-6">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">Full Name</label>
            <input type="text" id="client_name" required placeholder="Lord / Dr. / Alhaji / Mr." class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white focus:outline-none focus:border-gold-500 text-sm" />
          </div>
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">WhatsApp Phone</label>
            <input type="tel" id="client_phone" required placeholder="+234 ..." class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white focus:outline-none focus:border-gold-500 text-sm" />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">Residence of Interest</label>
            <select id="residence_choice" class="w-full px-4 py-3 rounded-xl bg-neutral-900 border border-white/10 text-white focus:outline-none focus:border-gold-500 text-sm">
              <option value="The Elysian Villa (₦1.85B)">The Elysian Villa (₦1.85B)</option>
              <option value="Aura Sky Penthouse (₦950M)">Aura Sky Penthouse (₦950M)</option>
              <option value="Grand Regent Estate (₦3.2B)">Grand Regent Estate (₦3.2B)</option>
              <option value="General Luxury Portfolio Consultation">General Luxury Portfolio Consultation</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">Preferred Inspection Date</label>
            <input type="date" id="inspection_date" required class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white focus:outline-none focus:border-gold-500 text-sm" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">Special Requirements / Notes</label>
          <textarea id="special_notes" rows="3" placeholder="Subterranean parking, private helipad, currency preference..." class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white focus:outline-none focus:border-gold-500 text-sm"></textarea>
        </div>

        <button type="submit" class="w-full py-4 rounded-xl bg-gold-500 hover:bg-gold-600 text-black font-bold text-sm tracking-wider uppercase transition shadow-xl shadow-gold-500/20 flex items-center justify-center gap-2">
          <i class="fa-brands fa-whatsapp text-base"></i>
          <span>Confirm Private Inspection on WhatsApp</span>
        </button>
      </form>
    </div>
  </section>

  <!-- EXECUTIVE FOOTER -->
  <footer class="bg-black text-white border-t border-white/10 py-16">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-4 gap-10">
      <div class="md:col-span-2">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 rounded-lg bg-gold-500/20 text-gold-500 flex items-center justify-center font-serif font-bold text-sm"><i class="fa-solid fa-landmark"></i></div>
          <span class="font-serif text-xl font-bold">{business_name}</span>
        </div>
        <p class="text-neutral-400 text-sm max-w-md mb-6 leading-relaxed">{tag}</p>
        <p class="text-neutral-500 text-xs"><i class="fa-solid fa-location-dot me-2 text-gold-500"></i>{location}</p>
        <p class="text-neutral-500 text-xs mt-1"><i class="fa-solid fa-phone me-2 text-gold-500"></i>{phone_number}</p>
      </div>

      <div>
        <div class="text-xs uppercase tracking-widest text-gold-500 font-display font-semibold mb-4">Private Portfolios</div>
        <ul class="space-y-2 text-sm text-neutral-400">
          <li><a href="#properties" class="hover:text-white transition">Maitama Prime Mansions</a></li>
          <li><a href="#properties" class="hover:text-white transition">Guzape Skyline Penthouses</a></li>
          <li><a href="#properties" class="hover:text-white transition">Asokoro Diplomatic Estates</a></li>
          <li><a href="#properties" class="hover:text-white transition">Jabi Waterfront Residences</a></li>
        </ul>
      </div>

      <div>
        <div class="text-xs uppercase tracking-widest text-gold-500 font-display font-semibold mb-4">Private Office</div>
        <p class="text-xs text-neutral-400 mb-4">Private client appointments scheduled Monday through Saturday, 9:00 AM – 6:00 PM.</p>
        <div class="flex items-center gap-3 text-neutral-400">
          <a href="#" class="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center hover:bg-gold-500 hover:text-black transition"><i class="fa-brands fa-instagram text-xs"></i></a>
          <a href="#" class="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center hover:bg-gold-500 hover:text-black transition"><i class="fa-brands fa-linkedin text-xs"></i></a>
          <a href="https://wa.me/{clean_phone}" target="_blank" class="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center hover:bg-gold-500 hover:text-black transition"><i class="fa-brands fa-whatsapp text-xs"></i></a>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 mt-12 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between text-xs text-neutral-600 gap-4">
      <div>© 2026 {business_name} Private Residences. All rights reserved.</div>
      <div class="flex gap-6">
        <a href="#" class="hover:text-neutral-400 transition">Confidentiality Agreement</a>
        <a href="#" class="hover:text-neutral-400 transition">Terms of Sale</a>
      </div>
    </div>
  </footer>

  <!-- MOBILE BOTTOM STICKY ACTION BAR -->
  <div class="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#faf9f5]/95 dark:bg-[#07090e]/95 backdrop-blur-md border-t border-black/10 dark:border-white/10 p-3 flex gap-2">
    <a href="tel:{clean_phone}" class="flex-1 py-3 rounded-xl bg-black/10 dark:bg-white/10 text-center font-bold text-xs uppercase flex items-center justify-center gap-1.5">
      <i class="fa-solid fa-phone"></i>
      <span>Call</span>
    </a>
    <a href="https://wa.me/{clean_phone}?text=Hello%20{business_name},%20I%20would%20like%20to%20inquire%20about%20your%20luxury%20residences." target="_blank" class="flex-1 py-3 rounded-xl bg-emerald-600 text-white text-center font-bold text-xs uppercase flex items-center justify-center gap-1.5">
      <i class="fa-brands fa-whatsapp"></i>
      <span>WhatsApp</span>
    </a>
    <a href="#inquiry" class="flex-[1.5] py-3 rounded-xl bg-gold-500 text-black text-center font-bold text-xs uppercase flex items-center justify-center gap-1.5 shadow-lg shadow-gold-500/20">
      <i class="fa-solid fa-calendar-check"></i>
      <span>Book Tour</span>
    </a>
  </div>

  <!-- INTERACTIVE DETAIL MODAL -->
  <div id="property-modal" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md hidden flex items-center justify-center p-4">
    <div class="bg-white dark:bg-cardDark border border-black/10 dark:border-white/10 rounded-3xl max-w-2xl w-full p-6 sm:p-8 relative max-h-[90vh] overflow-y-auto">
      <button onclick="closeModal()" class="absolute top-6 right-6 w-8 h-8 rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center hover:bg-red-500 hover:text-white transition">
        <i class="fa-solid fa-xmark"></i>
      </button>

      <img id="modal-img" src="" alt="Property" class="w-full h-64 object-cover rounded-2xl mb-6" />
      <div class="flex justify-between items-start mb-2">
        <h3 id="modal-title" class="font-serif text-2xl sm:text-3xl font-bold"></h3>
        <span id="modal-price" class="text-gold-500 font-serif font-bold text-xl sm:text-2xl"></span>
      </div>
      <p id="modal-loc" class="text-xs text-neutral-500 dark:text-neutral-400 mb-4"></p>
      <p id="modal-specs" class="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-6 bg-black/5 dark:bg-white/5 p-4 rounded-xl"></p>

      <div class="flex gap-4">
        <button onclick="bookModalProperty()" class="flex-1 py-3.5 rounded-xl bg-gold-500 hover:bg-gold-600 text-black font-bold text-xs uppercase tracking-wider transition">
          Schedule Private Tour
        </button>
        <button onclick="closeModal()" class="px-6 py-3.5 rounded-xl border border-black/10 dark:border-white/10 text-xs font-semibold uppercase">
          Close
        </button>
      </div>
    </div>
  </div>

  <!-- JAVASCRIPT LOGIC -->
  <script>
    // Theme Switcher Logic
    const themeBtn = document.getElementById('theme-toggle');
    const html = document.getElementById('html-root');

    function applyTheme(isDark) {{
      if (isDark) {{
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
      }} else {{
        html.classList.remove('dark');
        localStorage.setItem('theme', 'light');
      }}
    }}

    const savedTheme = localStorage.getItem('theme') || '{theme}';
    applyTheme(savedTheme === 'dark');

    themeBtn.addEventListener('click', () => {{
      const isDark = html.classList.contains('dark');
      applyTheme(!isDark);
    }});

    // Property Filter Logic
    function filterProperties(category, btn) {{
      document.querySelectorAll('.filter-btn').forEach(b => {{
        b.classList.remove('active', 'bg-black', 'dark:bg-white', 'text-white', 'dark:text-black');
        b.classList.add('bg-black/5', 'dark:bg-white/10');
      }});
      btn.classList.add('active', 'bg-black', 'dark:bg-white', 'text-white', 'dark:text-black');
      btn.classList.remove('bg-black/5', 'dark:bg-white/10');

      document.querySelectorAll('.property-item').forEach(item => {{
        if (category === 'all' || item.classList.contains(category)) {{
          item.style.display = 'block';
        }} else {{
          item.style.display = 'none';
        }}
      }});
    }}

    // Modal Details Logic
    let currentModalProperty = '';
    function openModal(title, price, loc, specs, img) {{
      currentModalProperty = title;
      document.getElementById('modal-title').innerText = title;
      document.getElementById('modal-price').innerText = price;
      document.getElementById('modal-loc').innerText = loc;
      document.getElementById('modal-specs').innerText = specs;
      document.getElementById('modal-img').src = img;
      document.getElementById('property-modal').classList.remove('hidden');
    }}

    function closeModal() {{
      document.getElementById('property-modal').classList.add('hidden');
    }}

    function bookModalProperty() {{
      closeModal();
      document.getElementById('residence_choice').value = currentModalProperty;
      document.getElementById('inquiry').scrollIntoView({{ behavior: 'smooth' }});
    }}

    // Inspection Form WhatsApp Dispatch
    function handleInspectionSubmit(e) {{
      e.preventDefault();
      const name = document.getElementById('client_name').value;
      const phone = document.getElementById('client_phone').value;
      const residence = document.getElementById('residence_choice').value;
      const date = document.getElementById('inspection_date').value;
      const notes = document.getElementById('special_notes').value;

      const message = `Hello {business_name}, I would like to schedule a private inspection.\n\n*Name:* ${{name}}\n*Phone:* ${{phone}}\n*Residence:* ${{residence}}\n*Preferred Date:* ${{date}}\n*Notes:* ${{notes}}`;
      const encoded = encodeURIComponent(message);
      window.open(`https://wa.me/{clean_phone}?text=${{encoded}}`, '_blank');
    }}
  </script>
</body>
</html>"""

    def _build_restaurant_html(
        self,
        business_name: str,
        location: str,
        phone_number: str,
        tagline: str,
        theme: str = "light",
    ) -> str:
        """Generate complete, ultra-luxury Restaurant web application."""
        clean_phone = _clean_phone_number(phone_number)
        tag = tagline or "Exquisite Artisanal Cuisine, Chef's Tasting Menus & Private VIP Dining."

        return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth" id="html-root">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{business_name} • Gourmet Dining & Online Ordering</title>
  <meta name="description" content="{tag} Located in {location}." />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" />
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            serif: ['Playfair Display', 'serif'],
            sans: ['Plus Jakarta Sans', 'sans-serif'],
          }},
          colors: {{
            amberGold: '#d97706',
            cardDark: '#12141c',
          }}
        }}
      }}
    }}
  </script>
</head>
<body class="font-sans bg-[#fdfbf7] dark:bg-[#0a0c10] text-[#1c1917] dark:text-[#f5f5f4] antialiased transition-colors duration-300">

  <!-- TOP BAR -->
  <div class="bg-[#1c1917] text-white text-xs py-2 px-4 text-center tracking-widest uppercase">
    <span>Open Today 12:00 PM – 11:30 PM • {location} • VIP Table Reservations Active</span>
  </div>

  <!-- NAVIGATION -->
  <nav class="sticky top-0 z-40 bg-[#fdfbf7]/90 dark:bg-[#0a0c10]/90 backdrop-blur-md border-b border-black/5 dark:border-white/10">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
      <a href="#" class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-amberGold/10 text-amberGold flex items-center justify-center font-serif font-bold text-xl"><i class="fa-solid fa-utensils"></i></div>
        <span class="font-serif font-bold text-2xl tracking-tight">{business_name}</span>
      </a>

      <div class="hidden md:flex items-center gap-8 text-sm font-medium">
        <a href="#menu" class="hover:text-amberGold transition">Digital Menu</a>
        <a href="#about" class="hover:text-amberGold transition">Culinary Philosophy</a>
        <a href="#reservations" class="hover:text-amberGold transition">Table Reservations</a>
        <a href="#reviews" class="hover:text-amberGold transition">Reviews</a>
      </div>

      <div class="flex items-center gap-3">
        <!-- Theme Toggle -->
        <button id="theme-toggle" class="w-10 h-10 rounded-full border border-black/10 dark:border-white/10 flex items-center justify-center">
          <i class="fa-solid fa-moon dark:hidden"></i>
          <i class="fa-solid fa-sun hidden dark:block text-amberGold"></i>
        </button>

        <!-- Cart Button -->
        <button onclick="toggleCart()" class="relative px-4 py-2.5 rounded-full bg-amberGold text-black font-bold text-xs uppercase tracking-wider flex items-center gap-2">
          <i class="fa-solid fa-bag-shopping"></i>
          <span id="cart-count">0</span>
        </button>
      </div>
    </div>
  </nav>

  <!-- HERO -->
  <section class="relative min-h-[85vh] flex items-center justify-center text-center text-white overflow-hidden">
    <div class="absolute inset-0 z-0">
      <img src="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1920&q=85" alt="Gourmet Dining" class="w-full h-full object-cover" />
      <div class="absolute inset-0 bg-black/60"></div>
    </div>

    <div class="relative z-10 max-w-4xl mx-auto px-4 py-20">
      <span class="inline-block px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-amber-300 text-xs uppercase tracking-widest mb-6">Artisanal Fine Dining</span>
      <h1 class="font-serif text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight mb-6">{business_name}</h1>
      <p class="text-lg text-neutral-200 font-light max-w-2xl mx-auto mb-10">{tag}</p>
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <a href="#menu" class="px-8 py-4 rounded-full bg-amberGold text-black font-bold text-xs uppercase tracking-wider hover:bg-amber-500 transition">Explore Digital Menu</a>
        <a href="#reservations" class="px-8 py-4 rounded-full bg-white/10 backdrop-blur-md border border-white/30 text-white font-bold text-xs uppercase tracking-wider hover:bg-white/20 transition">Reserve VIP Table</a>
      </div>
    </div>
  </section>

  <!-- DIGITAL MENU SECTION -->
  <section id="menu" class="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center max-w-2xl mx-auto mb-16">
      <span class="text-xs uppercase tracking-[0.2em] text-amberGold font-semibold block mb-2">Epicurean Creations</span>
      <h2 class="font-serif text-3xl sm:text-5xl font-bold">Artisanal Menu</h2>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      <!-- Dish 1 -->
      <div class="rounded-3xl overflow-hidden bg-white dark:bg-cardDark border border-black/10 dark:border-white/10 shadow-lg p-6 flex flex-col justify-between">
        <div>
          <img src="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=85" alt="Truffle Wagyu Ribeye" class="w-full h-48 object-cover rounded-2xl mb-4" />
          <div class="flex justify-between items-start mb-2">
            <h3 class="font-serif text-xl font-bold">Truffle Wagyu Ribeye</h3>
            <span class="text-amberGold font-bold font-serif">₦48,500</span>
          </div>
          <p class="text-xs text-neutral-500 dark:text-neutral-400 mb-6">A5 Japanese Wagyu served with shaved black truffles and roasted garlic purée.</p>
        </div>
        <button onclick="addToCart('Truffle Wagyu Ribeye', 48500)" class="w-full py-3 rounded-xl bg-black/5 dark:bg-white/10 hover:bg-amberGold hover:text-black font-bold text-xs uppercase tracking-wider transition">
          Add to Cart
        </button>
      </div>

      <!-- Dish 2 -->
      <div class="rounded-3xl overflow-hidden bg-white dark:bg-cardDark border border-black/10 dark:border-white/10 shadow-lg p-6 flex flex-col justify-between">
        <div>
          <img src="https://images.unsplash.com/photo-1558030006-450675393462?auto=format&fit=crop&w=600&q=85" alt="Charred Mediterranean Lobster" class="w-full h-48 object-cover rounded-2xl mb-4" />
          <div class="flex justify-between items-start mb-2">
            <h3 class="font-serif text-xl font-bold">Charred Lobster Tail</h3>
            <span class="text-amberGold font-bold font-serif">₦56,000</span>
          </div>
          <p class="text-xs text-neutral-500 dark:text-neutral-400 mb-6">Wild-caught lobster tail grilled over hickory wood with saffron emulsified herb butter.</p>
        </div>
        <button onclick="addToCart('Charred Lobster Tail', 56000)" class="w-full py-3 rounded-xl bg-black/5 dark:bg-white/10 hover:bg-amberGold hover:text-black font-bold text-xs uppercase tracking-wider transition">
          Add to Cart
        </button>
      </div>

      <!-- Dish 3 -->
      <div class="rounded-3xl overflow-hidden bg-white dark:bg-cardDark border border-black/10 dark:border-white/10 shadow-lg p-6 flex flex-col justify-between">
        <div>
          <img src="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=85" alt="Smoked Brioche Gold Burger" class="w-full h-48 object-cover rounded-2xl mb-4" />
          <div class="flex justify-between items-start mb-2">
            <h3 class="font-serif text-xl font-bold">Smoked Brioche Burger</h3>
            <span class="text-amberGold font-bold font-serif">₦24,000</span>
          </div>
          <p class="text-xs text-neutral-500 dark:text-neutral-400 mb-6">Double Angus patties, aged Gruyère, house-smoked tomato jam on toasted brioche.</p>
        </div>
        <button onclick="addToCart('Smoked Brioche Burger', 24000)" class="w-full py-3 rounded-xl bg-black/5 dark:bg-white/10 hover:bg-amberGold hover:text-black font-bold text-xs uppercase tracking-wider transition">
          Add to Cart
        </button>
      </div>
    </div>
  </section>

  <!-- TABLE RESERVATION FORM -->
  <section id="reservations" class="py-24 bg-black text-white">
    <div class="max-w-4xl mx-auto px-4">
      <div class="text-center max-w-xl mx-auto mb-12">
        <span class="text-xs uppercase tracking-[0.2em] text-amberGold block mb-2">VIP Dining Experience</span>
        <h2 class="font-serif text-3xl sm:text-5xl font-bold">Table Reservation</h2>
      </div>

      <form onsubmit="handleReservationSubmit(event)" class="bg-white/5 backdrop-blur-xl border border-white/10 p-8 sm:p-10 rounded-3xl space-y-6">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label class="block text-xs font-semibold uppercase text-neutral-400 mb-2">Full Name</label>
            <input type="text" id="res_name" required placeholder="Dr. / Mr. / Ms." class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white text-sm" />
          </div>
          <div>
            <label class="block text-xs font-semibold uppercase text-neutral-400 mb-2">WhatsApp Contact</label>
            <input type="tel" id="res_phone" required placeholder="+234 ..." class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white text-sm" />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div>
            <label class="block text-xs font-semibold uppercase text-neutral-400 mb-2">Guests Count</label>
            <select id="res_guests" class="w-full px-4 py-3 rounded-xl bg-neutral-900 border border-white/10 text-white text-sm">
              <option value="2 Guests">2 Guests (Intimate)</option>
              <option value="4 Guests">4 Guests</option>
              <option value="6 Guests">6 Guests</option>
              <option value="VIP Private Dining Room (8-14 Guests)">VIP Private Dining Room (8-14 Guests)</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold uppercase text-neutral-400 mb-2">Date</label>
            <input type="date" id="res_date" required class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white text-sm" />
          </div>
          <div>
            <label class="block text-xs font-semibold uppercase text-neutral-400 mb-2">Time Slot</label>
            <select id="res_time" class="w-full px-4 py-3 rounded-xl bg-neutral-900 border border-white/10 text-white text-sm">
              <option value="1:00 PM (Lunch)">1:00 PM (Lunch)</option>
              <option value="7:30 PM (Dinner)">7:30 PM (Dinner)</option>
              <option value="9:00 PM (Late Night)">9:00 PM (Late Night)</option>
            </select>
          </div>
        </div>

        <button type="submit" class="w-full py-4 rounded-xl bg-amberGold hover:bg-amber-500 text-black font-bold text-sm tracking-wider uppercase transition flex items-center justify-center gap-2">
          <i class="fa-brands fa-whatsapp text-base"></i>
          <span>Confirm VIP Table on WhatsApp</span>
        </button>
      </form>
    </div>
  </section>

  <!-- FOOTER -->
  <footer class="bg-black text-white border-t border-white/10 py-12 text-center text-xs text-neutral-500">
    <div class="max-w-7xl mx-auto px-4">
      <p class="font-serif text-lg font-bold text-white mb-2">{business_name}</p>
      <p class="mb-4">{location} • Phone: {phone_number}</p>
      <p>© 2026 {business_name}. All rights reserved.</p>
    </div>
  </footer>

  <!-- CART DRAWER -->
  <div id="cart-drawer" class="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-white dark:bg-cardDark border-l border-black/10 dark:border-white/10 p-6 shadow-2xl hidden flex flex-col justify-between">
    <div>
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-serif text-xl font-bold">Your Order Cart</h3>
        <button onclick="toggleCart()" class="w-8 h-8 rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center"><i class="fa-solid fa-xmark"></i></button>
      </div>
      <div id="cart-items" class="space-y-4 max-h-[60vh] overflow-y-auto">
        <p class="text-sm text-neutral-400">Your cart is currently empty.</p>
      </div>
    </div>
    <div class="border-t border-black/10 dark:border-white/10 pt-4">
      <div class="flex justify-between font-bold text-base mb-4">
        <span>Total:</span>
        <span id="cart-total" class="text-amberGold">₦0</span>
      </div>
      <button onclick="checkoutCart()" class="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider transition flex items-center justify-center gap-2">
        <i class="fa-brands fa-whatsapp"></i>
        <span>Checkout on WhatsApp</span>
      </button>
    </div>
  </div>

  <script>
    // Theme toggle
    const themeBtn = document.getElementById('theme-toggle');
    const html = document.getElementById('html-root');
    themeBtn.addEventListener('click', () => html.classList.toggle('dark'));

    // Cart system
    let cart = [];
    function addToCart(name, price) {{
      cart.push({{ name, price }});
      updateCartUI();
      toggleCart(true);
    }}
    function toggleCart(forceOpen) {{
      const drawer = document.getElementById('cart-drawer');
      if (forceOpen) drawer.classList.remove('hidden');
      else drawer.classList.toggle('hidden');
    }}
    function updateCartUI() {{
      document.getElementById('cart-count').innerText = cart.length;
      const itemsContainer = document.getElementById('cart-items');
      if (cart.length === 0) {{
        itemsContainer.innerHTML = '<p class="text-sm text-neutral-400">Your cart is currently empty.</p>';
        document.getElementById('cart-total').innerText = '₦0';
        return;
      }}
      let total = 0;
      itemsContainer.innerHTML = cart.map((item, idx) => {{
        total += item.price;
        return `<div class="flex justify-between items-center text-sm"><span>${{item.name}}</span><span class="font-bold">₦${{item.price.toLocaleString()}}</span></div>`;
      }}).join('');
      document.getElementById('cart-total').innerText = '₦' + total.toLocaleString();
    }}
    function checkoutCart() {{
      if (cart.length === 0) return alert('Your cart is empty.');
      const itemsList = cart.map(i => `- ${{i.name}} (₦${{i.price.toLocaleString()}})`).join('\\n');
      const total = document.getElementById('cart-total').innerText;
      const msg = `Hello {business_name}, I would like to place an order:\\n\\n${{itemsList}}\\n\\n*Total:* ${{total}}`;
      window.open(`https://wa.me/{clean_phone}?text=${{encodeURIComponent(msg)}}`, '_blank');
    }}
    function handleReservationSubmit(e) {{
      e.preventDefault();
      const name = document.getElementById('res_name').value;
      const phone = document.getElementById('res_phone').value;
      const guests = document.getElementById('res_guests').value;
      const date = document.getElementById('res_date').value;
      const time = document.getElementById('res_time').value;
      const msg = `Hello {business_name}, I would like to book a VIP Table:\\n\\n*Name:* ${{name}}\\n*Phone:* ${{phone}}\\n*Party:* ${{guests}}\\n*Date:* ${{date}}\\n*Time:* ${{time}}`;
      window.open(`https://wa.me/{clean_phone}?text=${{encodeURIComponent(msg)}}`, '_blank');
    }}
  </script>
</body>
</html>"""

    def _build_portfolio_html(
        self,
        business_name: str,
        location: str,
        phone_number: str,
        tagline: str,
        theme: str = "light",
    ) -> str:
        """Generate bespoke modern Portfolio / Agency web application."""
        return self._build_real_estate_html(business_name, location, phone_number, tagline, theme)


_demo_generator: Optional[DemoGeneratorService] = None


def get_demo_generator() -> DemoGeneratorService:
    global _demo_generator
    if _demo_generator is None:
        _demo_generator = DemoGeneratorService()
    return _demo_generator
