---
name: superloopy-clone
description: Use when the user asks for Superloopy clone or asks to clone, rebuild, reverse-engineer, replicate, or copy a website or page into a Superloopy-governed implementation. Triggers on "loopy clone", target URLs plus requests such as "clone this site", "rebuild this page", "make a copy of this website", "pixel-perfect clone", or "AI website clone". Requires browser automation and records component specs, assets, implementation, build output, and visual QA as Superloopy evidence.
---

# Superloopy Clone

Reverse-engineer a target URL into a working local implementation with audit artifacts. Use this only for authorized cloning, migration, learning, or recovery work. Do not help with phishing, deceptive impersonation, credential capture, or evading a site's terms.

When multiple URLs are provided, process each host independently. Keep every site's research, screenshots, assets, and evidence isolated under paths like `docs/research/<hostname>/`, `docs/design-references/<hostname>/`, and `.superloopy/evidence/website-clone/<hostname>/`.

This is not "inspect once, then redraw." Act as the foreman: inspect one section, write the exact spec, dispatch or build that bounded slice, then keep extracting the next section while builders run. A hard section is where extraction gets stricter, not where approximation becomes acceptable.

## Reference Example

Transferloom.com is a reference result for this workflow: `superloopy-clone` reproduced the page locally and passed desktop/mobile browser validation with preserved sticky navigation, animated hero, app preview sections, comparison table, security panel, sister app banner, footer, local assets, and a Superloopy evidence trail.

Use that bar for completion claims. A clone is successful only when it has this shape of evidence: source screenshots, research notes, component specs, downloaded assets, local browser screenshots, validation output, visual QA notes, and a final evidence artifact.

## Superloopy Contract

- Create or reuse a Superloopy plan. Use an evidence root like `.superloopy/evidence/website-clone/<hostname>/`.
- Preserve extraction artifacts: screenshots, topology, behavior notes, component specs, asset inventory, validation output, and visual QA notes.
- Record final proof with `SUPERLOOPY_EVIDENCE: <path-under-active-evidence-root>` when a worker is involved, or `superloopy loop evidence` when recording from the parent.
- Do not add dependencies without asking. If a clone needs a package for parity, explain why and get approval first.

## Scope Defaults

Unless the user gives different requirements, clone exactly what is visible at the target URL:

- Fidelity: pixel-focused parity for layout, spacing, typography, color, animation, responsive behavior, and visible interactions.
- In scope: visual layout, component structure, client-side interactions, responsive design, local assets, and demo data needed to render the page.
- Out of scope: real backend, authentication, payment flows, analytics, SEO optimization, and accessibility audit unless the user explicitly asks.
- Customization: none. Do not improve, restyle, rewrite copy, or replace assets during extraction.

## Fidelity Gate

Pixel-perfect means the default is extraction-first, not inspired reconstruction. If a section is driven by custom JavaScript, CSS keyframes, canvas, video, Lottie, WebGL, marquees, scroll timelines, masks, or layered absolute positioning, use **verbatim port** mode first:

- Preserve the original DOM subtree, CSS class block, and JS driver, then adapt asset URLs and framework boundaries.
- Write a dependency graph for the section: DOM roots, CSS selectors/keyframes, scripts/listeners, assets, timing, z-index, masks, and external libraries.
- Reimplementation is allowed only after proving the original implementation cannot be ported cleanly, recording why in the spec, and getting user approval when fidelity would drop.
- An unapproved approximation of an above-the-fold, animated, fixed, sticky, or interaction-heavy section is a blocker, not a known gap.
- Do not choose a similar redraw because the section is difficult. Dissect the original implementation and transplant it; if you cannot, stop and report the blocker with evidence.

## Preflight

1. Verify browser automation is available. Prefer Chrome or Playwright-style tools. If none are available, ask for a browser tool before proceeding.
2. Normalize and validate each target URL. Confirm the page loads. For multiple targets, prepare separate `docs/research/<hostname>/` and `docs/design-references/<hostname>/` folders before extraction.
3. Inspect the local app stack and existing commands before editing. Run the smallest existing check that proves the baseline, such as `npm run build`, `npm run typecheck`, or `npm test`.
4. Create research folders if needed: `docs/research/<hostname>/`, `docs/research/<hostname>/components/`, `docs/design-references/<hostname>/`, `scripts/`, and the Superloopy evidence root.
5. State authorization assumptions if the target is a third-party site.

## Superloopy Crew Dispatch

Use Superloopy actively when the clone has independent extraction, build, QA, or review lanes. Superloopy handoffs are parent-side bookkeeping; the host spawns workers, while Superloopy records and reconciles them.

- Treat `loopy team ... loopy clone`, `loopy team <url> clone`, `loopy crew ... clone`, `loopycrew ... clone`, and `ultrawork ... clone` as full-crew clone requests. Start with the crew plan, split extraction/build/QA/review lanes early, and record handoffs from the first dispatched lane.
- A plain `loopy clone` may stay solo only for a small static page or one clearly bounded component. The moment there are multiple sections, responsive states, animations, unknown assets, or parallelizable QA/review work, escalate to crew dispatch instead of continuing solo.
- `nami`: read-only navigator for target app structure, candidate selectors, route layout, existing component patterns, and asset paths. Use before broad repo searches or when multiple search angles are needed.
- `franky`: builder for exactly one bounded component, wrapper, or asset integration slice. Give the full spec inline, allowed files, validation command, artifact target, and `SUPERLOOPY_EVIDENCE` requirement.
- `usopp`: QA lane for build/typecheck/browser checks, screenshot capture, interaction sweep replay, and evidence reports.
- `zoro`: drift reviewer. Ask it to compare implementation against the component spec and call out simplified lookalikes, missing states, missing assets, and wrong interaction models.
- `robin`: audit lane for high-risk evidence, source attribution, suspicious extraction gaps, and final claim review. It ends with `SUPERLOOPY_AUDIT: <artifact>`.
- `jinbe`: final gate lane for fleet status, accepted evidence, outstanding blockers, and release readiness.

Record every dispatch with `superloopy loop handoff --agent <name> --assignment <self-contained task>`. When a worker returns, update that handoff with `--verdict <PASS|REJECT|NEEDS_CONTEXT>` and `--artifact <path>` when accepted. Run `superloopy loop fleet --json` before any final completion claim. Accepted handoffs require artifacts under the active evidence root; an ack-only worker is inconclusive, never a pass.

## Phase 1 - Reconnaissance

Capture the original before building:

- Full-page desktop screenshot at about 1440px.
- Mobile screenshot at about 390px.
- `PAGE_TOPOLOGY.md` listing sections from top to bottom, fixed layers, z-index relationships, and each section's interaction model.
- `BEHAVIORS.md` from scroll, click, hover, time, and responsive sweeps.
- `DESIGN_TOKENS.md` with fonts, colors, spacing, radii, shadows, animation timings, and global page behavior.
- `ASSETS.md` listing images, videos, background images, SVGs, favicons, fonts, and local target paths.
- `DEPENDENCY_GRAPH.md` mapping each complex section to its DOM roots, CSS blocks, JS drivers/listeners, keyframes, assets, masks, z-index layers, and third-party libraries.

Use computed styles, DOM inspection, and real assets. Do not estimate colors, spacing, text, or breakpoints when the browser can provide them.

### Mandatory Interaction Sweep

Run this sweep after initial screenshots and before component specs:

- Scroll before click. Move slowly from top to bottom first, because scroll-driven sidebars, sticky panels, snap points, reveal animations, and section-aware nav can masquerade as click tabs.
- Click every interactive-looking button, tab, pill, link, card, modal trigger, carousel control, and accordion. Extract each state's content and styles.
- Hover buttons, nav items, cards, images, and links. Record before/after values and transition timing.
- Wait for time-driven elements such as autoplaying carousels, counters, marquees, videos, Lottie animations, canvas loops, and WebGL scenes.
- Repeat at desktop 1440px, tablet 768px, and mobile 390px. Record breakpoints and layout changes.

`BEHAVIORS.md` is the behavior source of truth. If a component spec conflicts with it, re-extract before building.

## Phase 2 - Foundation

Build the shared foundation before sections:

- Fonts and metadata.
- Global CSS tokens and keyframes.
- Shared icon components from extracted SVGs.
- Content/type shapes for repeated section data.
- Downloaded assets under the project's existing public asset structure.
- A `scripts/download-assets.mjs` script or equivalent existing project script that downloads discovered images, videos, fonts, favicons, OG images, and binary assets into the local public asset tree with stable names.

Run the relevant build or typecheck after the foundation change and save the output under the Superloopy evidence root.

### Asset Discovery Script Pattern

Run a browser-side asset inventory before writing download code. Capture at least:

- `<img>` sources, natural dimensions, alt text, parent classes, sibling image count, `position`, and `z-index`.
- `<video>` sources, posters, autoplay, loop, muted, and source children.
- CSS background images from all elements, including pseudo-layer containers.
- Inline SVG count and deduplicated icon candidates.
- Fonts from link tags and sampled computed styles.
- Favicons, apple touch icons, webmanifest, and OG images.

Layered assets matter. A single visual may be a background, foreground image, mask, overlay icon, and clipped absolute layer. Enumerate all layers before assigning a builder. Do not build mockup HTML for content that is actually video, Lottie, canvas, or WebGL.

Use browser automation to gather this shape:

```javascript
JSON.stringify({
  images: [...document.querySelectorAll("img")].map((img) => ({
    src: img.currentSrc || img.src,
    alt: img.alt,
    width: img.naturalWidth,
    height: img.naturalHeight,
    parentClasses: img.parentElement?.className?.toString(),
    siblingImages: img.parentElement ? img.parentElement.querySelectorAll("img").length : 0,
    position: getComputedStyle(img).position,
    zIndex: getComputedStyle(img).zIndex
  })),
  videos: [...document.querySelectorAll("video")].map((video) => ({
    src: video.currentSrc || video.src || video.querySelector("source")?.src,
    poster: video.poster,
    autoplay: video.autoplay,
    loop: video.loop,
    muted: video.muted
  })),
  backgroundImages: [...document.querySelectorAll("*")]
    .map((element) => ({ element, backgroundImage: getComputedStyle(element).backgroundImage }))
    .filter((item) => item.backgroundImage && item.backgroundImage !== "none")
    .map(({ element, backgroundImage }) => ({
      url: backgroundImage,
      selectorHint: `${element.tagName.toLowerCase()}.${element.className?.toString().split(" ").slice(0, 3).join(".")}`
    })),
  svgCount: document.querySelectorAll("svg").length,
  favicons: [...document.querySelectorAll('link[rel*="icon"]')].map((link) => ({ href: link.href, sizes: link.sizes?.toString() })),
  fonts: [...new Set([...document.querySelectorAll("*")].slice(0, 250).map((element) => getComputedStyle(element).fontFamily))]
});
```

## Phase 3 - Component Specs

Before building each section, write a component spec at `docs/research/<hostname>/components/<component>.spec.md`. The spec is the contract for implementation and must include:

- Target component file.
- Screenshot path.
- DOM structure.
- Exact computed styles for the container and important children from `getComputedStyle()`.
- Interaction model: static, click-driven, scroll-driven, hover-driven, time-driven, or mixed.
- States and behaviors, including trigger, before/after values, transition, and implementation approach.
- Real text content.
- Assets with local paths.
- Responsive behavior for desktop, tablet, and mobile.
- Original implementation inventory for any complex section: DOM subtree, CSS class block, JS driver, keyframes, event listeners, timers, masks, z-index layers, and asset paths.
- Parity decision: `verbatim port`, `framework-adapted port`, or `approved reimplementation`; include the reason and approval if not porting.

If a spec grows beyond one focused component or a builder prompt exceeds about 150 lines, split it. Builders should not guess.

### Computed Style Extraction Contract

For each component container, run a browser extraction script instead of hand-measuring. The output goes into the spec and builder prompt:

```javascript
(function extractComponent(selector) {
  const root = document.querySelector(selector);
  if (!root) return JSON.stringify({ error: `missing ${selector}` });
  const props = [
    "fontSize", "fontWeight", "fontFamily", "lineHeight", "letterSpacing", "color",
    "background", "backgroundColor", "padding", "margin", "width", "height", "maxWidth",
    "display", "flexDirection", "justifyContent", "alignItems", "gap", "gridTemplateColumns",
    "borderRadius", "border", "boxShadow", "overflow", "position", "top", "right", "bottom",
    "left", "zIndex", "opacity", "transform", "transition", "objectFit", "objectPosition",
    "mixBlendMode", "filter", "backdropFilter", "whiteSpace", "textOverflow"
  ];
  function styles(element) {
    const computed = getComputedStyle(element);
    return Object.fromEntries(props.map((prop) => [prop, computed[prop]]).filter(([, value]) => value && value !== "normal" && value !== "auto" && value !== "none"));
  }
  function walk(element, depth = 0) {
    if (depth > 4) return null;
    return {
      tag: element.tagName.toLowerCase(),
      classes: element.className?.toString(),
      text: element.childNodes.length === 1 && element.childNodes[0].nodeType === Node.TEXT_NODE ? element.textContent.trim() : null,
      styles: styles(element),
      image: element.tagName === "IMG" ? { src: element.currentSrc || element.src, alt: element.alt, width: element.naturalWidth, height: element.naturalHeight } : null,
      children: [...element.children].slice(0, 30).map((child) => walk(child, depth + 1)).filter(Boolean)
    };
  }
  return JSON.stringify(walk(root), null, 2);
})("SELECTOR");
```

For stateful components, capture state A, trigger the behavior with browser automation, capture state B, then record the exact property diff, trigger, and transition.

### Component Spec Template

Each spec must include these headings. If a heading truly does not apply, write `N/A` with a reason:

- Overview: target file, screenshot, source URL, selector, and interaction model.
- DOM Structure: extracted hierarchy and source class names.
- Computed Styles: exact values for root and important children.
- States and Behaviors: trigger, state A, state B, transition, and implementation approach.
- Per-State Content: each tab, slide, accordion panel, or timed state.
- Assets: local paths for every image, background, overlay, SVG, video, font, mask, and poster.
- Text Content: verbatim live copy.
- Responsive Behavior: desktop, tablet, mobile, and observed breakpoints.
- Original Implementation Inventory: DOM subtree, CSS class block, JS driver/listeners, keyframes, timers, masks, layers, and third-party libraries.
- Parity Decision: `verbatim port`, `framework-adapted port`, or `approved reimplementation`.

### Pre-Dispatch Checklist

Before dispatching any builder, verify every item:

- Spec file exists under `docs/research/<hostname>/components/`.
- Every CSS value is extracted with `getComputedStyle()`, not guessed from utility classes.
- Interaction model is identified after scroll before click.
- Every state has content, styles, trigger, and transition.
- Scroll-driven components include threshold, mechanism, before/after styles, and transition.
- Hover states include before/after values and timing.
- All layered assets, overlays, masks, videos, Lottie, canvas, and SVGs are inventoried.
- Responsive behavior is documented for 1440px, 768px, and 390px.
- Builder prompt includes the full spec inline and stays under about 150 lines; otherwise split the component.

## Phase 4 - Build

Implement one bounded section or component at a time. For parallel workers, send the full spec inline; do not tell a worker to "go read the docs" for missing details. Use a handoff like:

```text
TASK: build <component> from this spec.
TARGET: <file path>
SCOPE: only this component and directly required local assets.
VERIFY: run the focused typecheck/build command.
DELIVERABLE: report artifact under <active evidence root> and end with SUPERLOOPY_EVIDENCE: <artifact>.
SPEC:
<paste the component spec here>
```

After each merge or parent implementation pass:

- Run the focused validation command.
- Fix type, lint, or build errors immediately.
- Record the output as evidence.
- For verbatim-port sections, verify the original DOM/CSS/JS relationships still exist after adaptation. Do not replace them with simplified lookalikes unless the spec records approved reimplementation.

## Phase 5 - Assembly

Wire sections into the page after their components pass local validation:

- Preserve the page topology from `PAGE_TOPOLOGY.md`.
- Implement page-level scrolling, sticky layers, section transitions, and responsive layout.
- Keep real content and assets connected through props or local data.
- Preserve global behaviors such as scroll snap, smooth scroll wrappers, section theme transitions, parallax layers, and fixed overlays when present.
- Run the project build or closest available full check.

## Phase 6 - Visual QA

Do not declare completion after the build alone. Compare original and clone:

- Desktop screenshot comparison.
- Mobile screenshot comparison.
- Section crop comparison for every above-the-fold, animated, fixed, sticky, or interaction-heavy component.
- Scroll, click, hover, and timed behavior checks.
- Section-by-section discrepancy list.

For every mismatch, decide whether extraction was wrong or implementation drifted. Re-extract, update the spec, and fix the component. If an approximation remains in a complex section without recorded approval, stop and mark the task blocked. Save `VISUAL_QA.md` under the evidence root.

## What NOT to Do

- Do not similar redraw, inspired-rebuild, or "make something close" when the source section is complex. Exact extraction is the job.
- Do not build click-based tabs before testing whether the original is scroll-driven. Scroll before click.
- Do not extract only the default state. Capture every tab, slide, hover, scroll, and timed state.
- Do not miss overlay or layered images. Check children, backgrounds, masks, z-index, and absolute-positioned layers.
- Do not replace videos, Lottie, canvas, or WebGL with static cards unless the user explicitly approves the fidelity drop.
- Do not approximate CSS from utility classes when computed values are available.
- Do not dispatch builders without a spec file and full inline spec.
- Do not combine unrelated sections into one worker or exceed the 150 lines complexity budget.
- Do not mark a worker pass from a status sentence. Require artifact-backed `SUPERLOOPY_EVIDENCE`, update `superloopy loop handoff`, then reconcile with `superloopy loop fleet --json`.

## Completion Report

Report:

- Target URLs.
- Sections built.
- Components created or changed.
- Spec files written.
- Assets downloaded or recreated.
- Validation commands and results.
- Visual QA result and remaining gaps.
- Final Superloopy evidence artifact.
