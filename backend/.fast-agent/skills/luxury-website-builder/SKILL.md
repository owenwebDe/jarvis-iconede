---
name: luxury-website-builder
description: Master Website Builder & UI/UX Engineering Skill for DemoBuilderAgent. Implements ThemeForest-grade luxury templates (Prospera, Luxoria, Artisanal Dining), state-of-the-art scroll reveals, animated number counters, zero-emoji icon systems, 1-click theme toggles, and live Vercel cloud deployment.
---

# Master Luxury Website Builder & UI/UX Engineering Skill

This skill governs the entire workflow, architecture, animation runtime, and execution rules for **DemoBuilderAgent** and **Jarvis**.

---

## 1. Primary Tool Routing & Architecture

Whenever tasked with building or presenting a website demo for a client, follow this **Template-First Decision Hierarchy**:

| Industry / Niche | Preferred Tool Call | Underlying Master Template |
|---|---|---|
| **Real Estate (Diplomatic / Ultra-Luxury / Hilltop)** | `demo_build_luxoria_real_estate_website` | **Luxoria Template Kit** (Bronze-Gold, Syne/Playfair, District Filters) |
| **Real Estate (Modern Estates / Penthouses / Classic)** | `demo_build_real_estate_website` | **Prospera Template Kit** (Obsidian/Warm Chalk, Instrument Sans) |
| **Restaurants / Dining / Cafes / Bars** | `demo_build_restaurant_website` | **Artisanal Dining Kit** (Cart Drawer, Table Booking, Digital Menu) |
| **SaaS / Tech / Startup (Like Pindrop)** | `demo_build_pindrop_website` | **Pindrop Kit** (Modern SaaS, Clean UI, Dashboard) |
| **Custom / Healthcare / Fashion / Logistics** | `demo_build_website` | **AI Architect (From-Scratch Generation with Motion Runtime)** |
| **Cloud Deployment (Live Production URL)** | `demo_deploy_to_cloud(demo_id=...)` | **Vercel Edge Network** |

---

## 2. Mandatory Architectural Structure for Any Generated Website

Every single web application generated (whether from template or from scratch) MUST contain all of the following core structural sections:

1. **Top Announcement / Status Ticker Bar**:
   - Pulsing live status dot (`bg-emerald-400 animate-pulse`), business phone, and location badge.
2. **Glassmorphic Navigation Bar (`backdrop-filter: blur(20px)`)**:
   - Vector Logo, Clean Navigation Links, 1-Click Dark/Light Mode Theme Toggle, and VIP Action Button.
3. **Cinematic Hero Section**:
   - Atmospheric Unsplash high-res photography with deep vignette overlay gradient.
   - High-fashion editorial headline (`font-serif` or `font-display`).
   - Dual Call-to-Action buttons (Primary Offer + Schedule Consultation).
   - **4-Metric Animated Trust Bar** (Counters dynamically ticking up from 0 on scroll).
4. **Interactive Filterable Showcase Grid**:
   - Tab switcher (e.g. *Mansions, Penthouses, Waterfront* or *Appetizers, Mains, Cocktails*).
   - Rich cards with high-res imagery, price tags in Billions/Millions or local currency, specs pills, and detail modal triggers.
5. **Craftsmanship / Private Amenities Matrix (6 Grid Cards)**:
   - Minimalist FontAwesome 6 vector icons with subtle hover lift and rounded-3xl borders.
6. **Social Proof & Verified Testimonials**:
   - Customer avatar imagery, verified investor badges, and star ratings.
7. **Direct WhatsApp Private Consultation / Booking Form**:
   - Pre-filled structured WhatsApp message dispatched directly via `https://wa.me/{clean_phone}?text={encoded_msg}`.
8. **Executive Footer**:
   - Business biography, office hours, district links, newsletter form, and copyright.
9. **Mobile-First Fixed Bottom Action Bar (Screens < 768px)**:
   - Immediate thumb-zone buttons: `Call`, `WhatsApp`, and `Book / Order`.

---

## 3. The 5 Core Animation & Micro-Interaction Rules

### 1. Viewport Scroll Reveals (`IntersectionObserver`)
All key headings, cards, and sections MUST include the `.reveal` class:
```css
.reveal {
  opacity: 0;
  transform: translateY(32px);
  transition: opacity 0.85s cubic-bezier(0.16, 1, 0.3, 1), transform 0.85s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: opacity, transform;
}
.reveal.active {
  opacity: 1;
  transform: translateY(0);
}
.reveal-delay-1 { transition-delay: 0.15s; }
.reveal-delay-2 { transition-delay: 0.3s; }
```

### 2. Animated Number Counters
Every metric (e.g. `₦75B+`, `100%`, `22+`) MUST use data attributes and tick smoothly from 0:
```html
<div class="font-display text-4xl font-bold text-amber-500"
     data-counter-target="75"
     data-counter-prefix="₦"
     data-counter-suffix="B+">₦0B+</div>
```
```javascript
const counterEls = document.querySelectorAll('[data-counter-target]');
const counterObs = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting && !entry.target.dataset.counted) {
      entry.target.dataset.counted = 'true';
      const target = parseFloat(entry.target.dataset.counterTarget);
      const prefix = entry.target.dataset.counterPrefix || '';
      const suffix = entry.target.dataset.counterSuffix || '';
      const isDecimal = target % 1 !== 0;
      let start = 0;
      const duration = 1400;
      const startTime = performance.now();
      function update(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const val = start + (target - start) * easeOut;
        entry.target.innerText = prefix + (isDecimal ? val.toFixed(1) : Math.floor(val).toLocaleString()) + suffix;
        if (progress < 1) requestAnimationFrame(update);
      }
      requestAnimationFrame(update);
    }
  });
}, { threshold: 0.2 });
counterEls.forEach(el => counterObs.observe(el));
```

### 3. Hover Lift & Image Scale
```css
.hover-lift {
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s ease;
}
.hover-lift:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.2);
}
```

### 4. Interactive Detail Modals
Lightbox modals with smooth backdrop blur (`backdrop-filter: blur(16px)`) for viewing floor plans, food specs, or project details.

### 5. 1-Click Dark/Light Mode Theme Switcher
Persistent dark/light theme toggle saved in `localStorage.getItem('theme')`.

---

## 4. Typography & Visual Standards

* **Heading Fonts**: `Syne`, `Instrument Sans`, `Playfair Display`, `Cormorant Garamond`.
* **Body / UI Fonts**: `Plus Jakarta Sans`, `Inter`.
* **Zero Emojis**: NEVER use unicode emojis. Always use FontAwesome 6 vector icons (`fa-solid`, `fa-brands`).
* **Touch Targets**: Minimum 48px height on all buttons and inputs.
