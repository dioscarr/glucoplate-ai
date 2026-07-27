---
name: minimalist-ui
description: Clean editorial-style interfaces. Warm monochrome palette, typographic contrast, flat bento grids, muted pastels. No gradients, no heavy shadows.
---

# Protocol: Premium Utilitarian Minimalism UI Architect

## 1. Protocol Overview

Name: Premium Utilitarian Minimalism & Editorial UI

Description: An advanced frontend engineering directive for generating highly refined, ultra-minimalist, document-style web interfaces analogous to top-tier workspace platforms.

This protocol strictly enforces a high-contrast warm monochrome palette, bespoke typographic hierarchies, meticulous structural macro-whitespace, bento-grid layouts, and an ultra-flat component architecture with deliberate muted pastel accents. It actively rejects standard generic SaaS design trends.

## 2. Absolute Negative Constraints

- Do not use Inter, Roboto, or Open Sans typefaces.
- Do not use generic thin-line icon libraries such as Lucide, Feather, or standard Heroicons.
- Do not use Tailwind default heavy drop shadows. Shadows must be practically non-existent or heavily customized to ultra-diffuse, low opacity (under 0.05).
- Do not use primary colored backgrounds for large elements or sections.
- Do not use gradients, neon colors, or 3D glassmorphism beyond subtle navbar blurs.
- Do not use `rounded-full` for large containers, cards, or primary buttons.
- Do not use emojis in code, markup, text content, headings, or alt text. Use appropriate icons or clean SVG primitives.
- Do not use generic placeholder names or lorem ipsum. Use realistic contextual content.
- Do not use AI copywriting clichés such as “Elevate”, “Seamless”, “Unleash”, “Next-Gen”, “Game-changer”, or “Delve”. Write plain, specific language.

## 3. Typographic Architecture

- Primary sans-serif: `'SF Pro Display', 'Geist Sans', 'Helvetica Neue', 'Switzer', sans-serif`.
- Editorial serif for hero headings and quotes: `'Lyon Text', 'Newsreader', 'Playfair Display', 'Instrument Serif', serif`; use tight tracking (-0.02em to -0.04em) and 1.1 line-height.
- Monospace for code, keys, and metadata: `'Geist Mono', 'SF Mono', 'JetBrains Mono', monospace`.
- Body text: use off-black or charcoal (`#111111` or `#2F3437`) with generous 1.6 line-height.
- Secondary text: muted gray `#787774`.

## 4. Color Palette

- Canvas: `#FFFFFF`, `#F7F6F3`, or `#FBFBFA`.
- Cards: `#FFFFFF` or `#F9F9F8`.
- Borders/dividers: `#EAEAEA` or `rgba(0,0,0,0.06)`.
- Spot pastels only:
  - Pale red: `#FDEBEC` / text `#9F2F2D`
  - Pale blue: `#E1F3FE` / text `#1F6C9F`
  - Pale green: `#EDF3EC` / text `#346538`
  - Pale yellow: `#FBF3DB` / text `#956400`

## 5. Component Specifications

- Bento grids: use asymmetrical CSS grids. Cards have exactly `1px solid #EAEAEA`, 8px or 12px radius, and 24px–40px padding.
- Primary buttons: `#111111` background, white text, 4px–6px radius, no shadow; hover subtly shifts to `#333333` or micro-scales to 0.98.
- Tags/status badges: may be pill-shaped, small uppercase text with wide tracking, using defined pastels.
- Accordions: no container boxes; use only `border-bottom: 1px solid #EAEAEA` with sharp +/− controls.
- Keyboard shortcuts: use `<kbd>` with a 1px border, 4px radius, warm background, and monospace font.
- Faux OS windows: use a minimal white top bar with three small light-gray circles.

## 6. Icons and Imagery

- Use Phosphor Icons (Bold/Fill) or Radix UI Icons; standardize stroke width.
- Illustrations: monochromatic rough continuous-line ink sketches with one muted pastel geometric offset.
- Photography: high-quality, desaturated, warm toned; optional warm grain at 0.04 opacity. Never use oversaturated stock photography.
- Do not leave sections flat: use subtle low-opacity imagery, warm radial light at 0.03 opacity, or minimal line patterns.

## 7. Motion

- On scroll entry, use `translateY(12px)` and opacity transition over 600ms with `cubic-bezier(0.16, 1, 0.3, 1)`; use IntersectionObserver, never scroll listeners.
- Card hover may transition from no shadow to `0 2px 8px rgba(0,0,0,0.04)` over 200ms.
- Use 80ms staggered list reveals; do not mount everything at once.
- Optional ambient background motion is a single fixed, pointer-events-none radial layer, 20s+ duration, 0.02–0.04 opacity.
- Animate only transform and opacity; use will-change sparingly.

## 8. Execution Protocol

When implementing frontend code or designing layouts:

1. Establish macro whitespace first: large vertical section padding.
2. Constrain typography content to max-width 4xl or 5xl.
3. Apply typography and warm monochrome variables immediately.
4. Ensure all cards, dividers, and borders use the 1px `#EAEAEA` rule.
5. Add scroll-entry motion to major blocks.
6. Give sections quiet visual depth without gradients or dense decoration.
7. Produce an uncluttered, editorial result without manual adjustment.
