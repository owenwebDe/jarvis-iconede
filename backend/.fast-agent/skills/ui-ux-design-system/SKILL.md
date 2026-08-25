---
name: ui-ux-design-system
description: Master UI/UX Design System and Visual Architecture skill for AI agents. Enforces high-end executive typography, clean cinematic background overlays, strict zero-emoji rules with clean SVG icons, 8pt spacing rhythm, luxury 60-30-10 palettes, and WCAG 2.2 AA accessibility.
---

# Master UI/UX Design System & Executive Visual Architecture

This skill enforces world-class, clean, executive web design standards.

---

## 1. Golden Rules for Presentable, Executive Websites

### Rule #1: Strictly Zero Emojis
*   **NEVER use emojis** in professional/luxury web applications (No `✨`, `🔥`, `🛵`, `💳`, `💬`, `🛍️`, `⚡`, `🎉`, etc.).
*   Emojis look amateur and degrade brand perception.
*   **Always use clean vector SVG icons / FontAwesome / Lucide icons** with refined 1.5px stroke weight.

### Rule #2: Clean Cinematic Background Imagery & Vignette Overlays
*   Never leave a page on flat solid pitch black or harsh plain white.
*   Use high-resolution, atmospheric photography (restaurant interior, architectural textures, warm ambient dining lighting) paired with a deep dark glass vignette overlay:
    ```css
    background: linear-gradient(180deg, rgba(8, 9, 13, 0.82) 0%, rgba(8, 9, 13, 0.96) 100%),
                url('https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1920&q=80') center/cover no-repeat fixed;
    ```

### Rule #3: High-Fashion Typography Hierarchy
*   **Display Font**: *Playfair Display*, *Cormorant Garamond*, or *Syne* for editorial titles.
*   **Body Font**: *Plus Jakarta Sans*, *Inter*, or *Geist* with clean line heights (`leading-relaxed`, 1.6).
*   **Subtitles**: Keep subtitles short, punchy (1 sentence max), and uncluttered. Avoid verbose paragraphs in hero sections.

---

## 2. The 60-30-10 Color Architecture

*   **60% Dominant Base**: Obsidian Navy (`#08090d`, `#0b0d13`).
*   **30% Structural Surfaces**: Translucent glass (`rgba(18, 20, 29, 0.75)`) with 1px border (`border-white/10`).
*   **10% High-Contrast Accent**: Refined Warm Gold (`#eab308`, `#d97706`) or Crimson Ember (`#dc2626`).

---

## 3. Micro-Interaction States for Every Interactive Element

Every button, card, and input MUST implement all 4 interactive states:
1.  **Default**: Clean, inviting, high contrast.
2.  **Hover**: Subtle elevation lift (`-translate-y-0.5`), glowing border tint.
3.  **Active / Tap**: Spring scale down (`active:scale-95`).
4.  **Focus-Visible**: High-contrast accessible ring.
