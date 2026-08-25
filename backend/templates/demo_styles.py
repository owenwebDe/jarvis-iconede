"""Enhanced Demo Styles & UI Component Library.

Modern, pixel-perfect design tokens and reusable components for
high-converting demo websites.
"""


# ══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS
# ══════════════════════════════════════════════════════════════════════════════

DESIGN_TOKENS = {
    "luxury": {
        "colors": {
            "primary": "#0a0a0a",
            "secondary": "#1a1a1a",
            "accent": "#c9a962",
            "accent_light": "#e8d5a3",
            "background": "#faf9f6",
            "surface": "#ffffff",
            "text": "#0a0a0a",
            "text_secondary": "#525252",
            "border": "#e5e5e5",
        },
        "typography": {
            "heading": "'Playfair Display', serif",
            "body": "'Inter', sans-serif",
            "accent": "'Cormorant Garamond', serif",
        },
        "shadows": {
            "sm": "0 1px 2px rgba(0,0,0,0.05)",
            "md": "0 4px 6px -1px rgba(0,0,0,0.1)",
            "lg": "0 10px 15px -3px rgba(0,0,0,0.1)",
            "xl": "0 20px 25px -5px rgba(0,0,0,0.1)",
        },
        "border_radius": "0px",
    },
    "tech_saas": {
        "colors": {
            "primary": "#6366f1",
            "secondary": "#4f46e5",
            "accent": "#06b6d4",
            "accent_light": "#22d3ee",
            "background": "#0f172a",
            "surface": "#1e293b",
            "text": "#f8fafc",
            "text_secondary": "#94a3b8",
            "border": "#334155",
        },
        "typography": {
            "heading": "'Inter', sans-serif",
            "body": "'Inter', sans-serif",
            "accent": "'JetBrains Mono', monospace",
        },
        "shadows": {
            "sm": "0 1px 2px rgba(0,0,0,0.3)",
            "md": "0 4px 6px -1px rgba(0,0,0,0.4)",
            "lg": "0 10px 15px -3px rgba(0,0,0,0.5)",
            "xl": "0 20px 25px -5px rgba(0,0,0,0.6)",
        },
        "border_radius": "12px",
    },
    "minimal_editorial": {
        "colors": {
            "primary": "#171717",
            "secondary": "#262626",
            "accent": "#dc2626",
            "accent_light": "#f87171",
            "background": "#fafafa",
            "surface": "#ffffff",
            "text": "#171717",
            "text_secondary": "#525252",
            "border": "#e5e5e5",
        },
        "typography": {
            "heading": "'Georgia', serif",
            "body": "'Helvetica Neue', sans-serif",
            "accent": "'Courier New', monospace",
        },
        "shadows": {
            "sm": "0 1px 2px rgba(0,0,0,0.05)",
            "md": "0 4px 6px -1px rgba(0,0,0,0.1)",
            "lg": "0 10px 15px -3px rgba(0,0,0,0.1)",
            "xl": "0 20px 25px -5px rgba(0,0,0,0.1)",
        },
        "border_radius": "0px",
    },
    "hospitality_dining": {
        "colors": {
            "primary": "#1c1917",
            "secondary": "#292524",
            "accent": "#b45309",
            "accent_light": "#d97706",
            "background": "#fafaf9",
            "surface": "#ffffff",
            "text": "#1c1917",
            "text_secondary": "#57534e",
            "border": "#e7e5e4",
        },
        "typography": {
            "heading": "'Playfair Display', serif",
            "body": "'Lato', sans-serif",
            "accent": "'Great Vibes', cursive",
        },
        "shadows": {
            "sm": "0 1px 2px rgba(0,0,0,0.05)",
            "md": "0 4px 6px -1px rgba(0,0,0,0.1)",
            "lg": "0 10px 15px -3px rgba(0,0,0,0.1)",
            "xl": "0 20px 25px -5px rgba(0,0,0,0.1)",
        },
        "border_radius": "8px",
    },
    "corporate_legal": {
        "colors": {
            "primary": "#0c4a6e",
            "secondary": "#075985",
            "accent": "#0ea5e9",
            "accent_light": "#38bdf8",
            "background": "#f0f9ff",
            "surface": "#ffffff",
            "text": "#0c4a6e",
            "text_secondary": "#475569",
            "border": "#bae6fd",
        },
        "typography": {
            "heading": "'Merriweather', serif",
            "body": "'Source Sans Pro', sans-serif",
            "accent": "'Roboto Mono', monospace",
        },
        "shadows": {
            "sm": "0 1px 2px rgba(0,0,0,0.05)",
            "md": "0 4px 6px -1px rgba(0,0,0,0.1)",
            "lg": "0 10px 15px -3px rgba(0,0,0,0.1)",
            "xl": "0 20px 25px -5px rgba(0,0,0,0.1)",
        },
        "border_radius": "4px",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# REUSABLE UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

UI_COMPONENTS = {
    "hero_variants": [
        {
            "name": "split_hero",
            "description": "Two-column hero with image on right",
            "html": """
<section class="hero-split">
  <div class="hero-content">
    <span class="hero-badge">{{badge}}</span>
    <h1 class="hero-title">{{title}}</h1>
    <p class="hero-subtitle">{{subtitle}}</p>
    <div class="hero-cta">
      <a href="#contact" class="btn btn-primary">{{cta_primary}}</a>
      <a href="#portfolio" class="btn btn-outline">{{cta_secondary}}</a>
    </div>
    <div class="hero-stats">
      <div class="stat"><span class="stat-number">{{stat1_number}}</span><span class="stat-label">{{stat1_label}}</span></div>
      <div class="stat"><span class="stat-number">{{stat2_number}}</span><span class="stat-label">{{stat2_label}}</span></div>
      <div class="stat"><span class="stat-number">{{stat3_number}}</span><span class="stat-label">{{stat3_label}}</span></div>
    </div>
  </div>
  <div class="hero-image">
    <img src="{{hero_image}}" alt="{{title}}" />
  </div>
</section>
""",
        },
        {
            "name": "fullscreen_hero",
            "description": "Full-screen hero with overlay text",
            "html": """
<section class="hero-fullscreen" style="background-image: url('{{hero_image}}')">
  <div class="hero-overlay"></div>
  <div class="hero-content">
    <span class="hero-badge">{{badge}}</span>
    <h1 class="hero-title">{{title}}</h1>
    <p class="hero-subtitle">{{subtitle}}</p>
    <a href="#contact" class="btn btn-primary btn-lg">{{cta}}</a>
  </div>
</section>
""",
        },
        {
            "name": "centered_hero",
            "description": "Centered hero with background gradient",
            "html": """
<section class="hero-centered">
  <div class="hero-content">
    <span class="hero-badge">{{badge}}</span>
    <h1 class="hero-title">{{title}}</h1>
    <p class="hero-subtitle">{{subtitle}}</p>
    <div class="hero-cta">
      <a href="#contact" class="btn btn-primary">{{cta_primary}}</a>
      <a href="#about" class="btn btn-ghost">{{cta_secondary}}</a>
    </div>
  </div>
</section>
""",
        },
    ],
    "feature_variants": [
        {
            "name": "grid_features",
            "description": "3-column feature grid with icons",
            "html": """
<section class="features-grid">
  <div class="section-header">
    <span class="section-badge">{{badge}}</span>
    <h2 class="section-title">{{title}}</h2>
    <p class="section-subtitle">{{subtitle}}</p>
  </div>
  <div class="features-container">
    {{#each features}}
    <div class="feature-card">
      <div class="feature-icon">{{icon}}</div>
      <h3 class="feature-title">{{title}}</h3>
      <p class="feature-description">{{description}}</p>
    </div>
    {{/each}}
  </div>
</section>
""",
        },
        {
            "name": "split_features",
            "description": "Alternating left/right feature sections",
            "html": """
<section class="features-split">
  {{#each features}}
  <div class="feature-row {{#if reverse}}reverse{{/if}}">
    <div class="feature-content">
      <span class="feature-number">{{number}}</span>
      <h3 class="feature-title">{{title}}</h3>
      <p class="feature-description">{{description}}</p>
      <a href="#" class="feature-link">{{link_text}} →</a>
    </div>
    <div class="feature-image">
      <img src="{{image}}" alt="{{title}}" />
    </div>
  </div>
  {{/each}}
</section>
""",
        },
    ],
    "cta_variants": [
        {
            "name": "gradient_cta",
            "description": "Full-width gradient CTA section",
            "html": """
<section class="cta-gradient">
  <div class="cta-content">
    <h2 class="cta-title">{{title}}</h2>
    <p class="cta-subtitle">{{subtitle}}</p>
    <div class="cta-buttons">
      <a href="#contact" class="btn btn-white">{{cta_primary}}</a>
      <a href="tel:{{phone}}" class="btn btn-outline-white">{{cta_secondary}}</a>
    </div>
  </div>
</section>
""",
        },
        {
            "name": "card_cta",
            "description": "Card-based CTA with icon",
            "html": """
<section class="cta-card">
  <div class="cta-card-inner">
    <div class="cta-icon">{{icon}}</div>
    <h2 class="cta-title">{{title}}</h2>
    <p class="cta-subtitle">{{subtitle}}</p>
    <a href="#contact" class="btn btn-primary btn-lg">{{cta}}</a>
  </div>
</section>
""",
        },
    ],
    "testimonial_variants": [
        {
            "name": "card_testimonials",
            "description": "Testimonial cards with photos",
            "html": """
<section class="testimonials">
  <div class="section-header">
    <span class="section-badge">{{badge}}</span>
    <h2 class="section-title">{{title}}</h2>
  </div>
  <div class="testimonials-grid">
    {{#each testimonials}}
    <div class="testimonial-card">
      <div class="testimonial-stars">{{stars}}</div>
      <p class="testimonial-text">"{{text}}"</p>
      <div class="testimonial-author">
        <img src="{{avatar}}" alt="{{name}}" class="author-avatar" />
        <div class="author-info">
          <span class="author-name">{{name}}</span>
          <span class="author-role">{{role}}</span>
        </div>
      </div>
    </div>
    {{/each}}
  </div>
</section>
""",
        },
    ],
    "pricing_variants": [
        {
            "name": "pricing_cards",
            "description": "Three-tier pricing cards",
            "html": """
<section class="pricing">
  <div class="section-header">
    <span class="section-badge">{{badge}}</span>
    <h2 class="section-title">{{title}}</h2>
    <p class="section-subtitle">{{subtitle}}</p>
  </div>
  <div class="pricing-grid">
    {{#each plans}}
    <div class="pricing-card {{#if featured}}featured{{/if}}">
      {{#if featured}}<span class="pricing-badge">Most Popular</span>{{/if}}
      <h3 class="pricing-name">{{name}}</h3>
      <div class="pricing-price">
        <span class="currency">{{currency}}</span>
        <span class="amount">{{amount}}</span>
        <span class="period">/{{period}}</span>
      </div>
      <ul class="pricing-features">
        {{#each features}}
        <li class="feature-item">{{icon}} {{text}}</li>
        {{/each}}
      </ul>
      <a href="#contact" class="btn {{#if featured}}btn-primary{{else}}btn-outline{{/if}} btn-block">{{cta}}</a>
    </div>
    {{/each}}
  </div>
</section>
""",
        },
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# CSS UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

CSS_UTILITIES = """
/* ═══ BASE RESET ═══ */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: var(--font-body); color: var(--text); background: var(--bg); line-height: 1.6; }

/* ═══ TYPOGRAPHY ═══ */
h1, h2, h3, h4, h5, h6 { font-family: var(--font-heading); font-weight: 700; line-height: 1.2; }
h1 { font-size: clamp(2.5rem, 5vw, 4rem); }
h2 { font-size: clamp(2rem, 4vw, 3rem); }
h3 { font-size: clamp(1.5rem, 3vw, 2rem); }

/* ═══ BUTTONS ═══ */
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 12px 24px; font-weight: 600; text-decoration: none;
  border-radius: var(--radius); transition: all 0.3s ease;
  cursor: pointer; border: 2px solid transparent;
}
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover { background: var(--accent-dark); transform: translateY(-2px); box-shadow: 0 4px 12px var(--accent-glow); }
.btn-outline { background: transparent; border-color: var(--accent); color: var(--accent); }
.btn-outline:hover { background: var(--accent); color: white; }
.btn-white { background: white; color: var(--primary); }
.btn-white:hover { background: var(--accent-light); }
.btn-lg { padding: 16px 32px; font-size: 1.125rem; }
.btn-block { width: 100%; }

/* ═══ SECTIONS ═══ */
section { padding: 80px 0; }
.section-header { text-align: center; max-width: 700px; margin: 0 auto 60px; }
.section-badge { display: inline-block; padding: 6px 16px; background: var(--accent-bg); color: var(--accent); border-radius: 999px; font-size: 0.875rem; font-weight: 600; margin-bottom: 16px; }
.section-title { margin-bottom: 16px; }
.section-subtitle { color: var(--text-secondary); font-size: 1.125rem; }

/* ═══ HERO ═══ */
.hero-split { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; align-items: center; min-height: 80vh; }
.hero-fullscreen { position: relative; min-height: 100vh; display: flex; align-items: center; justify-content: center; background-size: cover; background-position: center; }
.hero-overlay { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(0,0,0,0.8), rgba(0,0,0,0.6)); }
.hero-centered { min-height: 80vh; display: flex; align-items: center; justify-content: center; text-align: center; }
.hero-badge { display: inline-block; padding: 8px 20px; background: var(--accent-bg); color: var(--accent); border-radius: 999px; font-size: 0.875rem; font-weight: 600; margin-bottom: 24px; }
.hero-title { margin-bottom: 24px; }
.hero-subtitle { font-size: 1.25rem; color: var(--text-secondary); margin-bottom: 32px; max-width: 600px; }
.hero-cta { display: flex; gap: 16px; margin-bottom: 48px; }
.hero-stats { display: flex; gap: 40px; }
.hero-image img { width: 100%; height: auto; border-radius: var(--radius); }

/* ═══ FEATURES ═══ */
.features-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 32px; }
.feature-card { padding: 32px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); transition: all 0.3s ease; }
.feature-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.feature-icon { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; background: var(--accent-bg); color: var(--accent); border-radius: 12px; font-size: 1.5rem; margin-bottom: 20px; }
.feature-title { margin-bottom: 12px; font-size: 1.25rem; }
.feature-description { color: var(--text-secondary); }

/* ═══ TESTIMONIALS ═══ */
.testimonials-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; }
.testimonial-card { padding: 32px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
.testimonial-stars { color: #fbbf24; font-size: 1.25rem; margin-bottom: 16px; }
.testimonial-text { font-size: 1.125rem; font-style: italic; margin-bottom: 24px; line-height: 1.8; }
.testimonial-author { display: flex; align-items: center; gap: 16px; }
.author-avatar { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; }
.author-name { font-weight: 600; display: block; }
.author-role { color: var(--text-secondary); font-size: 0.875rem; }

/* ═══ PRICING ═══ */
.pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; max-width: 1000px; margin: 0 auto; }
.pricing-card { padding: 40px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); text-align: center; position: relative; }
.pricing-card.featured { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-bg); }
.pricing-badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--accent); color: white; padding: 4px 16px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
.pricing-name { font-size: 1.5rem; margin-bottom: 16px; }
.pricing-price { margin-bottom: 24px; }
.pricing-price .amount { font-size: 3rem; font-weight: 700; }
.pricing-price .currency { font-size: 1.5rem; vertical-align: top; }
.pricing-price .period { color: var(--text-secondary); }
.pricing-features { list-style: none; text-align: left; margin-bottom: 32px; }
.feature-item { padding: 8px 0; border-bottom: 1px solid var(--border); }

/* ═══ CTA ═══ */
.cta-gradient { background: linear-gradient(135deg, var(--accent), var(--accent-dark)); color: white; text-align: center; padding: 80px 24px; }
.cta-card { padding: 80px 24px; }
.cta-card-inner { max-width: 600px; margin: 0 auto; text-align: center; padding: 60px; background: var(--surface); border-radius: var(--radius); box-shadow: var(--shadow-xl); }

/* ═══ FOOTER ═══ */
.footer { background: var(--primary); color: white; padding: 60px 24px 24px; }
.footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px; max-width: 1200px; margin: 0 auto; }
.footer-brand { font-size: 1.5rem; font-weight: 700; margin-bottom: 16px; }
.footer-description { color: rgba(255,255,255,0.7); margin-bottom: 24px; }
.footer-heading { font-size: 1rem; font-weight: 600; margin-bottom: 16px; }
.footer-links { list-style: none; }
.footer-links li { margin-bottom: 8px; }
.footer-links a { color: rgba(255,255,255,0.7); text-decoration: none; transition: color 0.3s; }
.footer-links a:hover { color: white; }
.footer-bottom { border-top: 1px solid rgba(255,255,255,0.1); margin-top: 40px; padding-top: 24px; text-align: center; color: rgba(255,255,255,0.5); font-size: 0.875rem; }

/* ═══ RESPONSIVE ═══ */
@media (max-width: 768px) {
  .hero-split { grid-template-columns: 1fr; text-align: center; }
  .hero-cta { justify-content: center; flex-wrap: wrap; }
  .hero-stats { justify-content: center; }
  .features-container { grid-template-columns: 1fr; }
  .testimonials-grid { grid-template-columns: 1fr; }
  .pricing-grid { grid-template-columns: 1fr; }
  .footer-grid { grid-template-columns: 1fr; text-align: center; }
}

/* ═══ ANIMATIONS ═══ */
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideInLeft { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
@keyframes slideInRight { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }
@keyframes scaleIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
.animate-fade-in { animation: fadeIn 0.6s ease-out; }
.animate-fade-up { animation: fadeInUp 0.6s ease-out; }
"""


def get_design_tokens(archetype: str = "luxury") -> dict:
    """Get design tokens for an archetype."""
    return DESIGN_TOKENS.get(archetype, DESIGN_TOKENS["luxury"])


def get_ui_components() -> dict:
    """Get all UI component variants."""
    return UI_COMPONENTS


def get_css_utilities() -> str:
    """Get CSS utility classes."""
    return CSS_UTILITIES
