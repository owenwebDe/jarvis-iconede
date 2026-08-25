---
name: mobile-first-typography
description: Master skill for Mobile-First Responsive Engineering and Luxury Typography Systems for web applications. Enforces touch-optimized 48px hit areas, fluid clamp() typography scaling, fixed mobile bottom action bars, swipeable category rails, and Awwwards-grade curated font pairings (Playfair Display, Cormorant Garamond, Syne, Satoshi, Plus Jakarta Sans, DM Sans).
---

# Master Mobile-First Responsive Engineering & Luxury Typography System

This skill enforces mobile-perfect responsiveness and high-fashion typography across every generated web application.

---

## 1. Golden Rules of Mobile-First Architecture

### Rule #1: Fluid Typography with CSS `clamp()`
Headlines must scale smoothly from 320px mobile screens to 4K ultra-wide monitors without awkward line breaks or horizontal scrolling:
```css
/* Hero Display Headline */
font-size: clamp(2.2rem, 7vw, 4.5rem);
line-height: 1.08;
letter-spacing: -0.025em;

/* Section Headings */
font-size: clamp(1.75rem, 5vw, 3rem);

/* Body & Subtitles */
font-size: clamp(0.95rem, 2vw, 1.15rem);
line-height: 1.6;
```

### Rule #2: Touch-Target Ergonomics (48px Rule)
*   Every button, icon, link, and form input on mobile must have a minimum interactive tap target of **44px – 48px**.
*   Spacing between adjacent touch targets must be at least **8px** to prevent accidental mis-taps.

### Rule #3: Mobile Sticky Bottom Action Bar (Thumb Zone)
On viewports `< 768px`, users navigate with their thumbs. Web apps must provide a fixed floating bottom bar containing:
*   **Quick Menu Anchor**
*   **VIP Table Booking**
*   **Floating Cart Trigger with Live Count & Subtotal**
*   **WhatsApp / Direct Call**

### Rule #4: Swipeable Horizontal Category Rail
*   Category tabs on mobile must scroll smoothly horizontally (`overflow-x-auto no-scrollbar scroll-smooth flex-nowrap`).
*   Active tab auto-scrolls into view with tactile feedback.

### Rule #5: Responsive Hero Visual Stage
*   On desktop: 440px side-by-side circular showcase.
*   On mobile: Graceful 260px–300px centered stage stacked cleanly beneath the headline, never causing viewport overflow.

---

## 2. Awwwards-Grade Curated Typography Pairings

| Aesthetic Tier | Display / Heading Font | UI & Body Font | Ideal For |
| :--- | :--- | :--- | :--- |
| **Luxury Fine Dining & Hospitality** | **Playfair Display** (600–900) or **Cormorant Garamond** | **Plus Jakarta Sans** (400–700) | Steakhouses, Gourmet Restaurants, Wineries |
| **Modern Kinetic & Fast Casual** | **Syne** (700–800) | **Inter** or **DM Sans** | Smash Burgers, Urban Cafes, Trend Lounges |
| **Contemporary Editorial** | **Cabinet Grotesk** / **Clash Display** | **Satoshi** or **General Sans** | Boutique Fashion, Tech Agencies, Art Studios |

### Letter-Spacing & Kerning Hierarchy
*   **Oversized Headlines**: `tracking-tight` (`-0.025em` to `-0.035em`)
*   **Uppercase Category Badges & Overlines**: `tracking-[0.18em]` (`uppercase text-[10px] font-black`)
*   **Body Copy**: `tracking-normal` with generous line-height (`leading-relaxed` / `1.65`)
