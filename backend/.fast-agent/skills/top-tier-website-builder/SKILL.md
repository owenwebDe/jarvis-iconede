---
name: top-tier-website-builder
description: Master skill for writing top-tier, production-grade website build specifications. Treats the AI as a compiler, enforcing the 7 Golden Rules (no adjectives without numbers, verbatim copy, DOM order stated up front, tokens declared once, shared component recipes, exact asset mapping, and parameter checksum recaps).
---

# Skill: Writing Top-Tier Website Build Prompts

## Why generic agents produce generic sites

Most website-agent prompts say "build a hero section with a headline and CTA." The
agent fills every gap with its own default — default spacing, default easing,
default copy tone. That's why every output looks the same.

The Lumora method never leaves a gap. It treats the AI as a **compiler**,
not a collaborator. Every number, curve, and word is fixed. That's the entire
difference. This skill is that method, generalized.

---

## The 7 Rules (Apply to Every Section You Spec)

1. **No adjectives without a number.** Never "large heading" → always
   `font-size: 2.25rem` (with breakpoint variants). Never "smooth animation" →
   always a spring config `{tension, friction}` or a `cubic-bezier(0.16, 1, 0.3, 1)` + ms duration (e.g. `850ms`).
2. **Verbatim copy.** Every headline, label, button text, placeholder is quoted
   exactly. The agent should never invent filler copy.
3. **DOM order stated up front.** One line listing every section top to bottom
   before the detailed spec starts. Prevents the agent reordering or merging sections.
4. **Tokens declared once, referenced everywhere.** Palette, radii, spacing unit,
   font weights, breakpoints — define once at the top as constants, then every
   section just says "background: var/token name" instead of re-deriving colors.
5. **Shared component recipes, defined once.** If a pill button, tag chip, or
   hover-spring pattern repeats across sections, name it once ("PillButton",
   "AnimatedLink") with its full spec, then just reference the name in each
   section instead of re-describing it.
6. **Exact asset mapping.** If images/icons swap roles, state the mapping explicitly and flag it
   as "do not swap" — this is where agents most often silently get it wrong.
7. **End with a flat parameter recap.** A final section that re-lists every
   number used anywhere in the doc (delays, spring configs, breakpoints). Acts
   as a checksum the agent can cross-reference while building.

---

## Modular Section Library

Don't force every site into a single mold. Before writing the spec, decide
which of these the site actually needs — only spec the ones that apply:

| Section | Include when... |
|---|---|
| **PageLoader** | Site wants a branded first-paint moment; skip for fast, content-first sites |
| **Header/Nav** | Always, but overlay-style full-screen NavMenu only for image-heavy/portfolio sites |
| **Hero w/ cursor effect** | Visual/design-forward brands; skip for SaaS/dashboard/utility sites — use a plainer hero instead |
| **About / statement block** | Studio, agency, personal brand sites |
| **Portfolio/Work grid** | Agencies, freelancers, product galleries |
| **Services rows** | Agencies, consultancies |
| **Stats/count-up panel** | Sites with credible numbers to show off (traction, scale) |
| **Footer CTA + columns** | Always, but skip the giant watermark/columns for single-product landing pages |
| **Request/Contact modal** | Only if the site's real conversion action is "get in touch" — skip for e-commerce/app sites (use signup/cart flow spec instead) |

For a dashboard or SaaS app specifically: swap Hero/Portfolio/Stats-panel for
a spec of the actual app screens (sidebar nav, data tables, charts, empty
states) using the exact same 7 rules — numbers, not adjectives.

---

## Prompt Skeleton to Reuse

```markdown
# Recreate this site as [file target]: <Name> — <one-line positioning>

You are an expert creative front-end developer. Produce a **single
self-contained** [index.html / component] that reproduces the project below
exactly. [Tech constraints: no framework / which lib is allowed / etc.]

## What it is
[2-4 sentence plain description — palette family, typeface, mood, the one
"signature" interaction if any]

Sections in DOM order: [A → B → C → ...]  <- only the ones you chose above

## Page shell & libraries
[head, imports, CSS reset, grid/spacing system]

## Fixed palette & tokens
[hex values, radii, spacing unit, font weights — declared once]

## [Section 1 name]
[exact layout, exact copy, exact spring/easing, exact breakpoints]

## [Section 2 name]
...

## Shared component recipes
[PillButton, Eyebrow, TagChip, AnimatedLink, etc. — defined once]

## Assets
[table: original path → full URL → role, with explicit "do not swap" notes
where mapping is non-obvious]

## Fixed parameters (recap)
[flat list of every color/radius/delay/spring config used above]
```

---

## How to Apply This in Generation

Before generating a website specification or code:
1. **First output the DOM-order section list** for *this* site only, choosing from the modular library. Do not include a section unless it serves this site's actual goal.
2. **Generate the full code following the 7 rules**:
   - No adjective without a number.
   - No section without a name reference back to the tokens/recipes block.
   - Exact verbatim copy.
   - Precise timing curves (`cubic-bezier(0.16, 1, 0.3, 1)` and `850ms`).
