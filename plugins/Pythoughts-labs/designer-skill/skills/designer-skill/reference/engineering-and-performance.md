# Engineering & Performance

The perf and implementation layer that makes design survive contact with real code. Motion *design* decisions — easing curves, durations, when-to-animate — live in motion-and-interaction.md. This file owns the *engineering*: what renders fast, how tokens are wired, how output stays framework-honest.

---

## Component Architecture

- **Single responsibility, composition over inheritance.** A component does one thing. Compose primitives; don't inflate one component with variant flags it doesn't own.
- **Reach for a kit primitive before inventing a class.** `.ks-button` + variant (`-primary` / `-secondary` / `-ghost` / `-disabled`) — never `.hero-cta-primary` or `.footer-cta`. One shared vocabulary stops bespoke per-page class proliferation.
- **Name state classes and data-attributes, never magic strings.** Drive variant state through `data-*` (`[data-state="open"]`, `[data-mounted]`, `data-instant`) and named state classes (`.is-animating`). Style entry purely in CSS with `@starting-style` where support allows; fall back to a `data-mounted` toggle set in `useEffect`.
- **Isolate interactivity at the leaf.** Default to Server Components for static layout; any component using Motion, scroll listeners, or pointer physics MUST be an isolated leaf with `'use client'` at the top. Wrap providers in a `'use client'` component.
- **Memoize perpetual motion.** Any infinite/perpetual animation MUST be `React.memo`-wrapped and isolated in its own microscopic Client Component — never trigger re-renders in the parent layout. Wrap dynamic lists in `<AnimatePresence>`.
- **Never track continuous input in `useState`.** Mouse position, scroll progress, pointer physics, magnetic hover → Motion's `useMotionValue` / `useTransform` / `useScroll`. `useState` re-renders the tree every frame and collapses on mobile. Import from `'motion/react'` (`framer-motion` is a legacy alias).
- **Extract only at 3+ uses with the same intent.** Two buttons that look alike but serve different purposes stay separate. Premature abstraction is worse than duplication. Components that come out of extraction get a clear props API, sensible defaults, proper variants, and accessibility built in.
- **Classify design-system deviations before fixing them.** A feature that drifts from the system fails for one of three reasons: a **missing token** (the value should exist in the system but doesn't → add the token), a **one-off implementation** (a shared component exists but wasn't used → swap to it), or a **conceptual misalignment** (the flow/IA/hierarchy doesn't match neighboring features → rework the flow). Fixing the symptom without naming the cause is how drift compounds. When a design-system principle is ambiguous, ask — never guess.

### IA & flow-shape consistency

Match the *shape* of the experience to neighboring features, not just the surface. Visual polish on a misshapen flow is wasted work.

- **Progressive-disclosure parity.** A settings page exposing 40 fields when the rest of the app reveals 5 at a time is drift, even if every field is perfectly styled.
- **Multi-step actions follow the shape of comparable flows.** Modal vs full page, inline edit vs dedicated route, save-on-blur vs explicit submit, optimistic vs pessimistic update — pick whichever the neighboring flows already use.
- **Same conceptual weight = same visual weight.** Two features of equal importance shouldn't render at different scales or prominence.
- **Content arrival, update, and exit match adjacent features** — how things appear, refresh, and disappear should feel like the same product everywhere.
- **Naming & mental-model consistency.** A "Workspace" here must not be a "Project" three screens away.

### Z-index & stacking

- **Build a semantic z-index scale, document it in a constants file.** Order: dropdown → sticky → modal-backdrop → modal → toast → tooltip. **Never** arbitrary values like `999` or `9999`. Don't spam `z-50` / `z-10` unprompted; reserve z-index for systemic layers (sticky nav, modals, overlays, grain).
- **Escape clipping containers for dropdowns.** A `position: absolute` dropdown inside `overflow: hidden`/`auto` gets clipped — the single most common generated-code bug. Fix with the native `<dialog>` / Popover API (top-layer, no z-index war), `position: fixed` + CSS Anchor Positioning, or a portal (`createPortal(dropdown, document.body)` / `<Teleport to="body">`). Anchor positioning is Chrome/Edge 125+; fall back to `position: fixed` with `getBoundingClientRect()` coords recalculated on scroll/resize.

---

## Design Tokens & CSS Variables

- **Two-layer hierarchy.** Primitive tokens (`--blue-500`) feed semantic tokens (`--color-primary: var(--blue-500)`). For dark mode, redefine **only** the semantic layer; primitives stay fixed. Theming stays surgical.
- **Name tokens by role, never by value.** `--text-body` / `--text-heading`, not `--font-size-16`. `--space-xs … --space-xl`, not `--spacing-8`. Value-named tokens lie the moment the value changes.
- **Read tokens, never hand-type values.** Reference `var(--color-primary)`, `var(--text-display-size)`, `var(--ease-out)` directly in page CSS. Declare new colors in OKLCH; hex only appears in third-party examples or imported assets.
- **No hard-coded colors.** Every color resolves through a token. Hard-coded values are the #1 theming-audit failure; they don't update on theme switch.

> **Caveat — inherited CSS variables trigger whole-subtree recalc.** CSS variables are inheritable. Changing a variable on a parent recalculates styles for **all** its children. In a drawer with many items, updating `--swipe-amount` on the container is expensive. Set the property directly on the element instead.

| ❌ Don't | ✅ Do |
|---|---|
| `element.style.setProperty('--swipe-amount', `${d}px`)` on a parent | `element.style.transform = `translateY(${d}px)`` on the element |
| `--font-size-16: 16px` | `--text-body: 1rem` |
| Heavy `rgba()`/`hsla()` everywhere | Explicit opaque overlay tokens per context (exception: focus rings, interactive see-through states) |

---

## Hardware Acceleration

**Only animate `transform` and `opacity`.** They skip layout and paint and run on the GPU compositor. Animating `padding`, `margin`, `height`, `width`, `top`, or `left` triggers all three rendering steps (layout → paint → composite) and drops frames.

| ❌ CPU-bound (reflow) | ✅ GPU-composited |
|---|---|
| `left: 100px; width: 300px` | `transform: translateX(100px)` |
| `height` / `margin` transitions | `transform: scale()` / `translateY(100%)` |

- **`will-change` discipline.** Add it sparingly, only on elements that *actually* animate, scoped to `:hover` or an `.animating` class — never preemptively page-wide. Every layer costs GPU memory; `will-change` everywhere exhausts it.
- **Framer Motion `x`/`y`/`scale` shorthand is NOT hardware-accelerated.** It runs `requestAnimationFrame` on the main thread and drops frames when the browser is busy.

  ```jsx
  <motion.div animate={{ x: 100 }} />                          // NOT accelerated — main-thread rAF
  <motion.div animate={{ transform: "translateX(100px)" }} />  // Accelerated — off main thread
  ```

  A production dashboard tab animation used Shared Layout Animations and dropped frames during page loads; switching to CSS animations (off main thread) fixed it.
- **CSS animations beat JS under load.** CSS animations run off the main thread and stay smooth while the browser loads a new page; rAF-driven JS animations stall. Use **CSS for predetermined motion**, **JS only for dynamic, interruptible motion**.
- **WAAPI for programmatic motion that needs CSS performance.** Hardware-accelerated, interruptible, no library:

  ```js
  element.animate(
    [{ clipPath: 'inset(0 0 100% 0)' }, { clipPath: 'inset(0 0 0 0)' }],
    { duration: 1000, fill: 'forwards', easing: 'cubic-bezier(0.77, 0, 0.175, 1)' }
  );
  ```
- **Use CSS transitions over keyframes for interruptible UI.** Transitions retarget mid-flight; keyframes restart from zero. For rapidly-triggered elements (toasts, toggles), transitions are smoother.
- **Bound expensive paint.** Keep blur under 20px (heavy blur is expensive, especially in Safari). Restrict `backdrop-filter` to `fixed`/`sticky` elements (navbars, overlays), never scrolling containers. Apply grain/noise only to `position: fixed; inset: 0; pointer-events: none` pseudo-elements (`z-index` ~50-60) — grain on a scrolling container forces continuous GPU repaints that destroy mobile FPS. Use `contain` to isolate independent paint regions.
- **Scroll triggers via `IntersectionObserver`, not scroll listeners.** Unobserve after a one-shot animation fires. Scroll-event listeners cause jank.
- **Never mix two animation engines in one component tree.** Motion (`motion/react`) for UI/state-change motion; GSAP + ScrollTrigger for full-page scrolltelling (isolated leaf, `useEffect` cleanup); Three.js/WebGL same isolation. GSAP/Three.js + Motion in the same tree fight over the frame loop.
- See motion-and-interaction.md for easing curves, durations, spring config, and the animation-decision framework.

---

## Responsive & Fluid

- **Mobile-first with `min-width` queries.** Base styles target mobile; layer complexity upward. Desktop-first (`max-width`) loads unnecessary styles first. Let content drive breakpoints: start narrow, stretch until the design breaks, add a breakpoint there. Three usually suffice (640, 768, 1024px); the Tailwind scale is sm 640, md 768, lg 1024, xl 1280, 2xl 1536.
- **`clamp()` for fluid type and space.** `clamp(min, preferred, max)` scales without breakpoints. Bound it: keep max ≤ ~2.5× min, or wide ratios break zoom/reflow on large screens. Add a `rem` offset to the middle value (e.g. `5vw + 1rem`) so it never collapses to 0 on small screens. See design-principles.md (Typography) for the full type-ramp and measure rules.
- **Detect input method, not just screen size.** A laptop can have a touchscreen; a tablet can have a keyboard.

  ```css
  @media (pointer: coarse) { .button { padding: 12px 20px; } }
  @media (pointer: fine)   { .button { padding: 8px 16px; } }
  @media (hover: hover)    { .card:hover { transform: translateY(-2px); } }
  @media (hover: none)     { /* use :active instead */ }
  ```
- **Flexbox for 1D, Grid for 2D.** Nav bars, button groups, component internals → flex. Page structure, dashboards, data-dense layouts → grid with `grid-template-areas` redefined per breakpoint. Use CSS Grid for column structures — **never** `w-[calc(33%-1rem)]` flex-percentage math.
- **Container queries for components, viewport queries for pages.** The same card adapts to its slot, not the viewport:

  ```css
  .card-container { container-type: inline-size; }
  @container (min-width: 400px) { .card { grid-template-columns: 120px 1fr; } }
  ```
- **`gap` for sibling spacing, not margins** (eliminates margin-collapse hacks).
- **`min-width: 0` (and `min-height: 0`) on flex/grid children** so they shrink below content size instead of overflowing.
- **Full-height: `min-h-[100dvh]`, never `h-screen` / `height: 100vh`.** `100vh` jumps as the iOS Safari address bar shows/hides. Wrap the page in `overflow-x-hidden` to kill stray horizontal scroll from off-screen animation.
- **Declare an explicit `<768px` collapse for every multi-column layout.** Collapse to single column (`width: 100%`, `padding: 1rem`, `gap: 1.5rem`). Horizontal overflow on mobile is a critical failure. Test at 375, 390, 768, 1024, 1440px.
- **Handle device safe areas.** `padding: env(safe-area-inset-*)`, with `.footer { padding-bottom: max(1rem, env(safe-area-inset-bottom)); }`. Set `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`.
- **Touch targets ≥ 44×44px** even when the visual element is smaller — expand the hit area: `.icon-button::before { content:''; position:absolute; inset:-10px; }`. **Respect the thumb zone:** on mobile, primary actions live in the bottom half of the screen, within one-handed reach — top corners are the hardest stretch.
- **Never** hide core functionality on mobile, use device detection over feature detection, or maintain separate mobile/desktop codebases. Test on a real iPhone, a real Android, and a tablet — DevTools emulation misses touch, CPU/memory, latency, and font rendering.

### Other contexts

Responsive doesn't end at viewport widths — some surfaces aren't screens at all.

- **Tablet:** master-detail (list pane + detail pane) is the canonical hybrid layout — neither a stretched phone layout nor a cramped desktop one.
- **Print:** break pages at logical points; strip nav, footer, and interactive elements; expand hidden content and print full URLs; add page numbers/headers; provide print-friendly chart variants.
- **Email:** 600px max single column, inline CSS, table-based layout, big button CTAs, no hover reliance — deep-link to the web app for anything complex.

---

## Accessibility (the engineering layer)

- **WCAG contrast minimums:** body 4.5:1 (AA) / 7:1 (AAA); large text (18px+ or 14px bold) 3:1 / 4.5:1; UI components & icons 3:1 / 4.5:1. Verify every button label and form field (input, placeholder, focus-ring, helper, error) against its background before shipping. Never put gray text on colored backgrounds. Don't rely on color alone — pair with icon/label/pattern. Full ratio table: design-principles.md (Color and contrast).
- **Never `outline: none` without a replacement.** Restore focus via `:focus-visible` (keyboard users only):

  ```css
  button:focus { outline: none; }
  button:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
  ```
  Focus ring: 2–3px thick, 3:1 contrast against adjacent colors, offset *outside* the element, consistent across all interactive elements.
- **`prefers-reduced-motion` reduces, it does not delete.** Keep opacity and color transitions that aid comprehension; drop movement and position animation:

  ```css
  @media (prefers-reduced-motion: reduce) {
    .element { animation: fade 0.2s ease; /* no transform-based motion */ }
  }
  ```
  In JS: `const reduce = useReducedMotion(); const closedX = reduce ? 0 : '-100%';`
- **Gate hover behind both queries.** `@media (hover: hover) and (pointer: fine) { .el:hover { transform: scale(1.05); } }`. Touch devices fire hover on tap, causing false positives. Never rely on hover for functionality.
- **Keyboard & semantics.** Semantic HTML (`<nav>`, `<main>`, `<article>`, `<aside>`, `<section>`) over div soup. Roving tabindex for tabs/menus/radio groups (one item `tabindex="0"`, rest `-1`; arrows move the 0, Tab leaves the group). Hidden skip link: `<a href="#main-content">Skip to main content</a>`. Trap modal focus with `<main inert>` behind it or native `<dialog>.showModal()` (focus trap + Escape-to-close for free).
- **Forms.** Visible `<label>` above the input — never placeholder-as-label (it disappears on input). Error below the field, wired with `aria-describedby`. Validate on blur, not every keystroke (exception: password strength). Never `window.alert()`.
- **Descriptive `alt` text** on meaningful images; never `alt=""` or `alt="image"`.
- **Automated checks are a first pass, not a pass.** axe, Lighthouse, and Storybook a11y catch a real but narrow slice — roughly contrast, missing labels, ARIA misuse, and landmark gaps. They cannot judge focus order, keyboard operability of custom widgets, screen-reader clarity, meaningful alt text, or whether a dialog/menu/combobox follows its WAI-ARIA APG pattern. Run the automated layer, then **manually** walk keyboard-only flow and APG conformance for every interactive component. When reporting, separate **automated-detectable** findings from **manual-review** ones, and **never certify full WCAG 2.2 AA conformance from automated output alone** — claim only what was actually verified.

---

## Core Web Vitals & Loading

Measure before and after — premature optimization wastes time. Fix the biggest bottleneck first, not micro-optimizations. Test on a low-end Android throttled to 3G, not a flagship iPhone on Wi-Fi.

| Metric | Target | Levers |
|---|---|---|
| LCP | < 2.5s | optimize hero image (`next/image priority` or preload), inline critical CSS, CDN, SSR |
| FID / INP | < 100ms / < 200ms | break up long tasks, defer non-critical JS, web workers, cut JS execution |
| CLS | < 0.1 | set image/video dimensions, reserve space with `aspect-ratio`, don't inject above existing content, avoid layout-shifting animation |

- **Images:** modern formats (WebP/AVIF), compress at 80–85% quality, `srcset` + `sizes` width descriptors for resolution, `<picture>` for art direction (different crops). `loading="lazy"` below the fold; **never** lazy-load above-fold content. Don't load a 3000px image for a 300px slot. 2× assets for retina. Reserve aspect ratio: `.image-container { aspect-ratio: 16 / 9; }`. Verify image URLs before referencing — guessed photo IDs ship as broken placeholders.
- **Prevent web-font shift.** `@font-face { font-display: swap; }` plus a metric-matched fallback (`size-adjust`, `ascent-override`, `descent-override`, `line-gap-override`). Subset with `unicode-range`. Preload only the critical weight (regular body above the fold). Variable font for 3+ weights. See design-principles.md (Typography).
- **JS bundle:** code-split (route/component), tree-shake, drop unused deps, dynamic-import large components (`const HeavyChart = lazy(() => import('./HeavyChart'))`). React: `memo()`, `useMemo`/`useCallback` for expensive work, virtualize long lists (TanStack Virtual / react-window), no inline functions in render. Motion is not tiny; Three.js is large — lazy-load both.
- **Batch DOM reads, then writes** — never alternate in a loop (forces reflow per iteration):

  ```js
  const heights = els.map(el => el.offsetHeight);   // all reads
  els.forEach((el, i) => { el.style.height = heights[i] * 2 + 'px'; }); // all writes
  ```
- **`content-visibility: auto`** for long lists; **virtual scrolling** for tens of thousands of rows.
- **Clean up to prevent leaks:** remove event listeners, cancel subscriptions, clear timers, abort pending requests on unmount. `debounce(handleSearch, 300)`, `throttle(handleScroll, 100)`.
- Progressive enhancement is non-negotiable: every effect degrades gracefully via `@supports` and JS feature detection; the CSS-only baseline still looks good. Target 60fps; simplify below 50.

---

## Hardening for Real Data

Designs that only work with perfect data aren't production-ready.

- **Long text:** truncate (`overflow:hidden; text-overflow:ellipsis; white-space:nowrap`), line-clamp (`-webkit-line-clamp:3; display:-webkit-box; -webkit-box-orient:vertical`), or wrap (`overflow-wrap:break-word; hyphens:auto`).
- **i18n:** budget 30–40% extra width (German ~30% longer than English); never fixed-width text containers — `<button className="px-4 py-2">` not `w-24`. RTL via logical properties (`margin-inline-start`, `padding-inline`, `border-inline-end`). Format with `Intl.DateTimeFormat` / `Intl.NumberFormat`; pluralize with an i18n library, never `` `${n} item${n!==1?'s':''}` ``. UTF-8 everywhere.

  | Language | Expansion vs English |
  |---|---|
  | German | +30% |
  | French | +20% |
  | Finnish | +30–40% |
  | Chinese | −30% characters, but same width per character |
- **Write translation-friendly strings.** Keep numbers separate from the sentence ("New messages: 3", not a templated mid-sentence count); ship full sentences as single strings (word order varies by language — never concatenate fragments); no abbreviations ("5 minutes ago", never "5 mins ago").
- **API status → UI:** 400 validation errors, 401 redirect to login, 403 permission, 404 not-found, 429 rate-limit, 500 generic + support. Preserve user input on form error; offer a retry button on network failure. **Never block the whole interface because one component errored** — isolate the failure, keep the rest usable.
- **Cover every state:** empty (with a next action), loading (say *what* is loading — "Saving your draft…", never bare "Loading…"; for waits beyond a few seconds, set expectations: "Analyzing your data… usually takes 30–60 seconds"), large datasets (paginate/virtualize), concurrent (disable button while loading, optimistic update with rollback), permission, browser compat (feature-detect, polyfill).
- **Validate client-side AND server-side** — never trust the client alone; sanitize all input.

**Stress-test battery — run before calling it hardened:**

- Names and titles with 100+ characters; emoji in every text field; RTL scripts (Arabic/Hebrew); CJK text.
- 1000+ items in every list.
- Click submit 10× rapidly — the double-submission race test.
- Refresh mid-workflow — is state preserved?
- Paste from Excel into every input.
- Throttle to 3G; force every API error state.
- Windows high-contrast mode.

---

## Framework-Agnostic Output Rules

- **Respect the existing pipeline.** If a framework is present (astro/next/nuxt/svelte/vite config, `package.json` deps), use it. Don't start a parallel build or introduce a second framework. Edit source files and run the project's build (`npm run build`).
- **Never write to `build/`, `dist/`, or `.next/` directly** via `cat`, heredoc, or shell redirects — that skips asset hashing, image optimization, code splitting, and CSS extraction, and produces output the dev server won't serve.
- **Verify every import against `package.json` before using it.** If a 3rd-party library (`framer-motion`, `lucide-react`, `zustand`, …) is missing, output the install command first. Hallucinated imports break the build.
- **Confirm current API syntax from live docs, not training-data memory — frameworks drift fast.** Before writing version-sensitive code (Tailwind v4 `@theme` vs v3 config, Next.js App Router `async` params, `motion/react` vs the `framer-motion` alias, shadcn registry, a named design-system package), check the *installed* version (`package.json` / lockfile) and resolve its actual API. When a live-docs MCP is available (e.g. Context7), query it for the exact version; otherwise read the package's own shipped types/`README` in `node_modules`. Never assume an API shape, prop name, or config key from memory — confirmed signatures beat confident guesses, and a wrong guess against the wrong major version silently breaks the build.
- **One icon family per project**, one strokeWidth (e.g. 1.5 or 2.0). Use the project's existing set; don't hand-roll SVG paths or introduce a second family.
- **Tailwind:** v4 default — use `@tailwindcss/postcss` or the Vite plugin, **never** the `tailwindcss` plugin in `postcss.config.js` (silently breaks v4). v3 only if `package.json` demands it; don't use v4 syntax in a v3 project.
- **Use the official design-system package when the brief names a known family** (Fluent, Material Web, Carbon, Polaris, Atlaskit, Primer, govuk-frontend, USWDS, shadcn/ui). One system per project; don't import a system's tokens then override 90%.
- **OKLCH for all new colors;** for a brand-new project with no committed brand colors, choose one brand seed hue, then compose bg/surface/ink/accent/muted around it — hold chroma/hue roughly constant and vary lightness, reducing chroma near white/black (ramp construction in design-principles.md → Color and contrast; per-system palettes in aesthetic-systems.md). Skip only if committed brand colors already exist — identity preservation wins.
- **Ship clean:** branded favicon, meta tags (`<title>`, description, `og:image`), active-nav-link styling, no commented-out dead code or debug artifacts, no inline styles fragmenting the system.
