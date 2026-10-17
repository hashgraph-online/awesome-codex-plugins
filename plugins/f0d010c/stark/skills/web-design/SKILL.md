---
name: web-design
description: Use for web interfaces, landing pages, product sites, dashboards, React, Next.js, Astro, Tailwind, frontend audits, responsive design, browser interaction, web motion, or requests for a distinctive non-generic website. Select the web surface and implementation track, load a small reference bundle, preserve usability and accessibility, and validate the rendered result. Skip when the target is exclusively native Apple, Android, or Windows.
---

# Web design

Design the product surface before choosing decoration or libraries.

## Context budget

Load two core references for the selected mode and no more than two conditional references. Use `../../references/ui-patterns/README.md` and `../../references/web-patterns/README.md` only as catalogs. Do not read every linked document.

## Classify the surface

Choose one:

- product application;
- operational dashboard;
- product-proof landing page;
- campaign or cinematic page;
- docs or API platform;
- checkout or trust flow;
- design system or component library;
- targeted audit or repair.

Do not apply campaign spacing and choreography to repeated-use applications.

## Choose a reference bundle

| Surface | Core references | Conditional additions |
|---|---|---|
| Product app | `task-ergonomics.md`, `interaction-state-matrix.md` | navigation, component API, direct manipulation, responsive gate |
| Dashboard | `dashboard-insight-hierarchy.md`, `data-visualization-library-selection.md` | realistic data, adaptive composition, performance |
| Product landing | `creative-direction.md`, `page-proof-architecture.md` | conversion proof, brand motif, asset realism |
| Cinematic page | `animation-creation.md`, `choreography-state-machine.md` | cinematic landing, motion libraries, performance |
| Docs/API | `navigation-information-architecture.md`, `progressive-disclosure-information-scent.md` | typography, search/command interaction |
| Checkout/trust | `form-state-validation-system.md`, `accessibility-interaction-contract.md` | conversion proof, usability scenarios |
| Design system | `design-system-production-loop.md`, `token-implementation-contract.md` | component API, state gallery |
| Audit/repair | `ui-audit-rubric.md`, `visual-repair-playbook.md` | usability, accessibility, fingerprint diversity |

Paths in this table are under `../../references/ui-patterns/` except `task-ergonomics.md`, which is under `../../references/ux-patterns/`.

## Make the web decision brief

Before code, state:

- user and product job;
- surface type and primary object;
- implementation track;
- composition and first-viewport focal path;
- typography posture and concrete font plan;
- material, palette, and motif;
- proof asset or data strategy;
- required states and recovery;
- responsive replacement;
- motion level and owner;
- selected references;
- acceptance evidence.

## Choose the implementation track

Read `../../references/ui-patterns/web-implementation-tracks.md` when the stack is not already fixed.

| Track | Choose when |
|---|---|
| Existing stack | The repository already has a viable frontend |
| Static HTML/CSS/JS | Small page, minimal state, portability matters |
| Vite + React | Stateful UI or rich interaction without server rendering |
| Next.js | Routing, server rendering, metadata, or server components matter |
| Astro | Content-first page with isolated interactive islands |

Use native CSS and platform APIs before adding libraries. If a library is needed, give it one explicit job.

## Choose a visual direction

For open-ended or high-craft work, read `../../references/ui-patterns/creative-direction.md`. Pick one direction and define:

- composition grammar;
- typography contrast;
- palette ratio;
- material language;
- repeated motif;
- one tasteful risk;
- explicit restraints.

For established direction families, load one matching file:

- `../../references/web-direction-editorial.md`
- `../../references/web-direction-brutalist.md`
- `../../references/web-direction-glow-grain.md`
- `../../references/web-direction-industrial-mono.md`
- `../../references/web-direction-active-bento.md`
- `../../references/web-direction-type-as-hero.md`

Do not merge several directions into a sampler.

## Typography, copy, and assets

- Use `../../references/web-fonts.md` when choosing fonts.
- Use `../../references/web-copy-voice.md` when copy is vague, generic, or central to conversion.
- Use `../../references/ui-patterns/asset-selection.md` when imagery or proof media is required.
- Use `../../references/ui-patterns/art-direction-asset-board.md` only when hero/key art needs responsive crops and layer ownership.

Use real product nouns, states, units, and actions. Avoid placeholder media, random stock photos, fake charts, and generic “built for modern teams” copy.

## Interaction and motion

Use the lowest-complexity technique that expresses the product behavior:

- CSS transitions for local state feedback;
- View Transitions for page or shared-object continuity;
- Motion for React component/layout choreography;
- GSAP for authored timelines and pinned sequences;
- Three/R3F, canvas, Rive, Lottie, or video only when the medium proves the product.

For animation-led work, load `animation-creation.md` and `choreography-state-machine.md`. Add `performance-budget-contract.md` before implementing expensive media or rendering. Always define reduced-motion and failed-load fallbacks.

Use `../../references/web-patterns/README.md` to select specific interaction recipes. Do not install patterns merely because they are available.

## Responsive and accessible behavior

Define breakpoint triggers from content failure, not device labels. Specify:

- navigation replacement;
- dense-region replacement;
- media crop or fallback;
- input and touch behavior;
- scroll ownership;
- long-text and zoom behavior.

For serious interactive UI, load `../../references/ui-patterns/accessibility-interaction-contract.md`. Preserve semantic HTML, accessible names, keyboard paths, visible focus, status announcements, contrast, reflow, target size, and reduced motion.

## Web bans

Reject:

- generic centered hero + floating cards without product proof;
- default shadcn/Radix/Tailwind visual identity;
- undifferentiated dark slate with indigo accents;
- identical section spacing throughout;
- excessive glass, blur, glow, or rounded containers;
- decorative libraries with no product job;
- placeholder images, fake dashboards, or hype copy;
- controls that look interactive but do nothing;
- page-level horizontal overflow;
- animation that obscures content or cannot be paused/reduced.

See `../../references/web-bans.md` only when an audit needs the expanded list.

## Rendered validation

After implementation:

1. inspect desktop and mobile;
2. exercise primary, error, empty, loading, and recovery states;
3. check console/runtime failures;
4. verify keyboard and reduced-motion behavior;
5. load `../../references/ui-patterns/rendered-quality-gate.md`;
6. load one additional gate only if required:
   - usability: `../../references/ux-patterns/rendered-usability-acceptance-gate.md`
   - typography: `../../references/ui-patterns/rendered-typography-quality-gate.md`
   - advanced stack: `../../references/ui-patterns/capability-stack-rendered-gate.md`
7. repair the highest-impact failure and re-check it.

Do not claim high-craft, accessible, responsive, or production-ready output without evidence.
