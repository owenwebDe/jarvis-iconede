---
name: motion-dev-2d-animation
description: Comprehensive expert guide for building state-of-the-art 2D animated websites and mobile interfaces using Motion (motion.dev / Framer Motion). Covers spring physics, kinetic typography, 2.5D interactive card tilts, magnetic buttons, SVG path drawing, layout morphing, and GPU-accelerated scroll timelines.
---

# Motion.dev 2D Animation & High-End UI Skill

This skill guides the creation of world-class, fluid, production-grade 2D animated web interfaces using **Motion** (formerly Framer Motion).

---

## 1. Core Philosophy & Design Principles

1. **Physicality Over Timelines**:
   Always prefer **spring physics** over duration-based bezier easings. Interfaces must feel tactile, responsive, and grounded in real-world inertia.

2. **Perceived Performance**:
   All animations must run on GPU compositor threads (`transform: translate3d/scale/rotate`, `opacity`). Never animate layout properties like `width`, `height`, `top`, or `left` directly—use `layout` or `transform`.

3. **Restraint & Purpose**:
   Micro-animations should guide the eye, provide instant feedback on touch/click, and reward user exploration without causing motion sickness.

---

## 2. Standard Spring Physics Profiles

Use these tuned spring constants across all UI interactions:

```javascript
export const SPRING_PRESETS = {
  // Snappy & responsive — For buttons, toggles, chips, clicks
  snappy: { type: "spring", stiffness: 400, damping: 28, mass: 0.8 },

  // Smooth & luxurious — For modals, drawers, card expansions, hero entrances
  gentle: { type: "spring", stiffness: 120, damping: 20, mass: 1.0 },

  // Playful & bouncy — For cart badge counters, success checkmarks, reaction emojis
  bouncy: { type: "spring", stiffness: 350, damping: 14, mass: 0.9 },

  // Slow ambient drift — For background blur orbs, floating hero badges, ambient steam
  floating: {
    repeat: Infinity,
    repeatType: "reverse",
    duration: 3.5,
    ease: "easeInOut",
  }
};
```

---

## 3. Key 2D Animation Patterns

### A. Kinetic Hero Entrance & Masked Text Reveal
Slice headlines up from an invisible clipping mask for an editorial Apple/Linear look.

```html
<div class="overflow-hidden">
  <h1 class="translate-y-full opacity-0 animate-reveal font-serif text-6xl">
    Taste Elegance
  </h1>
</div>
```

```javascript
// Motion Vanilla JS / CDN
motion.animate(
  ".hero-title",
  { y: [40, 0], opacity: [0, 1] },
  { duration: 0.8, ease: [0.16, 1, 0.3, 1] }
);
```

---

### B. Interactive 2.5D Mouse-Tracking Card Tilt
Cards smoothly angle in 3D space toward the cursor with dynamic lighting/glare.

```javascript
function attach3DTilt(cardElement) {
  cardElement.addEventListener("mousemove", (e) => {
    const rect = cardElement.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    const rotateX = ((y - centerY) / centerY) * -10; // Max 10 deg tilt
    const rotateY = ((x - centerX) / centerX) * 10;
    
    cardElement.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
  });

  cardElement.addEventListener("mouseleave", () => {
    cardElement.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
  });
}
```

---

### C. Magnetic Cursor Attraction for Primary Buttons
Buttons pull slightly toward the mouse when within proximity, rewarding interaction.

```javascript
function attachMagneticPhysics(btnElement) {
  btnElement.addEventListener("mousemove", (e) => {
    const rect = btnElement.getBoundingClientRect();
    const x = e.clientX - (rect.left + rect.width / 2);
    const y = e.clientY - (rect.top + rect.height / 2);
    
    btnElement.style.transform = `translate3d(${x * 0.25}px, ${y * 0.25}px, 0)`;
  });

  btnElement.addEventListener("mouseleave", () => {
    btnElement.style.transform = "translate3d(0px, 0px, 0)";
    btnElement.style.transition = "transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)";
  });
}
```

---

### D. Fluid Sliding Tab Indicator (Shared Layout Morph)
Sliding active pill that glides smoothly across filter tabs using Spring physics.

```javascript
function moveTabIndicator(indicatorEl, targetTabEl) {
  const targetRect = targetTabEl.getBoundingClientRect();
  const parentRect = targetTabEl.parentElement.getBoundingClientRect();
  
  const left = targetRect.left - parentRect.left;
  const width = targetRect.width;
  
  indicatorEl.style.transform = `translateX(${left}px)`;
  indicatorEl.style.width = `${width}px`;
  indicatorEl.style.transition = "transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), width 0.3s ease";
}
```

---

### E. SVG Vector Path Tracing
Animate SVG stroke lines drawing on scroll or hover.

```html
<svg viewBox="0 0 100 100" class="w-16 h-16">
  <circle cx="50" cy="50" r="40" stroke="#eab308" stroke-width="4" fill="none"
    stroke-dasharray="251.2" stroke-dashoffset="251.2" class="animate-draw-circle" />
</svg>
```

---

## 4. Checklist for Every Generated Demo Website

Before exporting a demo site for a client, verify that:
- [x] Hero section features staggered text & badge entrance reveals.
- [x] Dish / Product cards have interactive 2.5D mouse-tracking tilt effects.
- [x] CTA buttons have spring hover states and active tap feedback.
- [x] Filter tabs glide with a spring-loaded active pill indicator.
- [x] Adding to cart triggers a playful badge bounce animation (`scale: [1, 1.35, 1]`).
- [x] Drawer/modal transitions use backdrop blur and spring scale-in.
