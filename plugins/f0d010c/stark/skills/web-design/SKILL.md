---
name: web-design
description: Use for web apps, landing pages, dashboards, React/Next/Vite/Tailwind frontends, web UI reference planning, animation, motion, scrolling, GSAP, Motion, Lenis, command palettes, split panes, and frontend interaction decisions. Builds web surfaces with the right surface type, visual direction, hierarchy, motion, layout, copy, assets, and anti-slop discipline. ALWAYS choose surface type and ask which aesthetic direction first. SKIP when the target is a native desktop/mobile app.
---

# web-design — pick the direction first, then execute precisely

Goal: build web surfaces that feel specific, useful, and visually deliberate. Marketing pages can chase an Awwwards-level ceiling; dashboards, editors, docs, checkout, and agent-run UIs should prioritize product proof, scan speed, state coverage, and stable interaction before spectacle.

## Step 0 (MANDATORY) — Choose surface type, then direction

Before aesthetic direction, classify the surface using `../../references/ui-patterns/surface-taxonomy.md`:

- Marketing page
- Cinematic campaign page
- Editorial scroll story
- Product proof landing page
- Immersive brand page
- SaaS dashboard
- Editor/canvas
- Checkout/upgrade
- Agent/tool run
- Mobile task flow

Then write the `UI decision brief` from `../../references/ui-patterns/ui-decision-brief.md`. For dashboards, editors, checkouts, and agent-run UIs, preserve the UX decision brief if one exists and bias toward usable density over Awwwards spectacle.

For polished, original, memorable, high-craft, campaign, or "best-looking" requests, read `../../references/ui-patterns/creative-direction.md` before visual styling. Define a creative direction brief with world, metaphor, material language, typography personality, layout grammar, repeated motif, forbidden defaults, one tasteful risk, and restraints.

For cinematic campaign, editorial scroll story, product proof, or immersive brand pages, read `../../references/ui-patterns/cinematic-landing-system.md` before choosing motion. Define key art, art direction, typography discipline, section rhythm, and page choreography first. Motion should reveal the system, not compensate for weak composition.

Do not force an expressive landing-page composition onto a repeated-use web app. For operational surfaces, read `../../references/ui-patterns/product-quality-bar.md`, `../../references/ui-patterns/visual-hierarchy.md`, `../../references/ui-patterns/responsive-containment.md`, `../../references/ui-patterns/motion-budget.md`, `../../references/ui-patterns/interaction-techniques.md`, and `../../references/ui-patterns/ui-audit-rubric.md` before coding.

When the site needs imagery, proof visuals, icons, screenshots, typography, or references, also read `../../references/ui-patterns/asset-selection.md` and include an asset plan before code. If the user is using GPT/Codex and image generation is available, generated bitmap assets are allowed for fictional product visuals, editorial hero imagery, textures, and empty states when they support the product job.

When using shipped products, Mobbin/Figma screens, docs, or screenshots as references, read `../../references/ui-patterns/reference-analysis.md` and produce a reference extraction brief. Borrow structure, interaction, state, and responsive decisions; never copy visual identity.

When using high-craft landing pages as references, extract first-viewport composition, key-art framing, type scale, section sequence, asset reuse, and motion pacing. Do not copy the subject, exact layout, assets, copy, or trade dress.

## Step 0a (MANDATORY) — Ask the user which direction

Six distinct aesthetic directions exist. Each has its own typography, palette, motion language, copy voice, layout grammar, reference apps, ban list. **Pick before any code.** Never blend directions — that produces the AI-slop middle.

> Which direction for this site?
>
> **1. Editorial Swiss revival** — generous whitespace, asymmetric grid, neo-serif headlines, monospace metadata, italic emphasis, single accent. Refs: rauchg.com, are.na, robinrendle.com, Hayes & Co (our example). Reading-room vibe, considered restraint.
>
> **2. Tactile brutalism** — visible grids, harsh type, color clashes, raw seams, mono-driven, pure-black or hi-vis accents. Refs: werkstatt.fyi, fram.io, off-brand.work. "Human-made" reaction signal.
>
> **3. Type-as-hero** — oversized variable display fonts, scroll-morphing letterforms, no decorative imagery, type *is* the design. Refs: igloo.inc (Awwwards SOTY 2025), lehman.berlin, Lando Norris site. Maximalist typography flex.
>
> **4. Glow + grain** — multicolor glowing backdrops with tactile grain, atmospheric mesh gradients, dark-mode editorial. Refs: stripe.com/sessions, openai.com, vercel.com hero, liveblocks.io. Atmosphere-driven.
>
> **5. Industrial monospace** — Söhne Mono / JetBrains Mono everywhere, terminal references, log-driven hero, technical aesthetic, no decoration. Refs: railway.com, fly.io, raycast.com, resend.com. Dev-tool benchmark.
>
> **6. Active bento** — interactive bento tiles, expanding/morphing cards, autoplay video on hover, layered reveal. Not the static 2023 bento. Refs: linear.app/method, vercel.com/templates, arc.net. Product-led.
>
> Which? Or describe vibe (luxury vs raw vs technical vs maximalist) and I'll pick.

If the brief gives strong signal (e.g. "watch maker / luxury minimal" → 1; "AI dev tool, terminal vibe" → 5; "Awwwards SOTY ambition with massive type" → 3), state your pick + reasoning in one sentence. If ambiguous, ask.

Once picked, **load the matching direction reference** from `../../references/web-direction-{name}.md`. Each contains: typography scale, palette, layout grid, motion moves, copy voice, reference apps, direction-specific ban list.

For operational dashboards, admin tools, and editors, ask direction in a restrained way: "systematic / editorial / industrial / branded product-led" is enough. Do not ask for Awwwards direction if it would harm repeated use.

## Step 0b — Stack questions (after surface and direction picked)

Before choosing a framework, read `../../references/ui-patterns/web-implementation-tracks.md` and produce the implementation track brief. React is a first-class option for advanced interactive work, but it is not the automatic default.

Ask in one batch:
- **Framework**: static HTML/CSS/JS, Vite + React, Next, Astro, SvelteKit, Solid, Qwik, or existing project stack?
- **CSS**: Tailwind v4 default. Vanilla CSS w/ `@scope`/`@layer` if user prefers no utility classes.
- **Motion library**: choose from `../../references/ui-patterns/interaction-techniques.md`. CSS first for simple transitions, Motion for React product motion, GSAP only for timeline/pinned storytelling, Lenis only for brand scroll feel.
- **Smooth scroll**: default off. Only add if direction and surface type justify it; never add to dashboards, docs, forms, checkout, editors, or admin tools.

State stack pick at top of response in one sentence.

## Step 1 — Technique inventory (use as palette, deploy 2-4 per project)

The model has access to all of these. **Don't deploy all of them on every site** — over-motion is its own tell. Awwwards SOTY sites typically have 2-4 signature motion moments + restrained baseline.

Read `../../references/web-patterns/README.md` first to choose the right pattern family, then read the specific `../../references/web-patterns/*.md` files you will use. List below:

### Motion / Interaction
- **Letter-stagger reveal** — hero text drops in word-by-word w/ spring physics
- **Variable-font axis hover** — `font-variation-settings` shifts on hover/scroll (weight, optical size, grade)
- **Page-load curtain** — paper-colored mask slides off, contents reveal beneath
- **Custom cursor** — branded dot + label morph ("VIEW", "READ", "PLAY") on hoverable elements
- **Magnetic CTAs** — buttons attract cursor within radius
- **Scroll-pinned section** — pin viewport, content advances frame-by-frame as scroll progresses
- **Scroll-driven CSS** — `animation-timeline: view()` / `scroll()` for native scroll-tied animation
- **View Transitions API** — `document.startViewTransition()` for SPA route changes + shared element transitions
- **Layered parallax** — multiple z-layers scroll at different speeds for depth
- **3D tilt card** — perspective + rotateX/Y on cursor position
- **Marquee band** — horizontal scrolling text band
- **Connected animation** — `layoutId` (Motion) for hero element morph between pages
- **Mesh gradient** — multi-stop SVG/CSS radial gradients, animated
- **Lenis smooth scroll** — eased momentum scroll
- **GSAP ScrollTrigger** — for complex timeline-driven effects
- **Scroll-snapping** — section-by-section CSS scroll-snap
- **Symbol cycling** — text that cycles through related symbols/glyphs on hover

### Typography techniques
- **Variable font axis play** — wght / opsz / grade hover transitions
- **Italic emphasis within headline** — `<em class="italic">word</em>` for selective italic
- **Monospace caps eyebrow** — `font-mono text-[10px] tracking-[0.32em] uppercase`
- **§ section markers** — Manifesto-style `§ 01` `§ 02` numbering
- **Scroll-tied letter spacing** — `letter-spacing` shifts as scroll advances
- **Type-as-image** — text as primary visual, no decorative imagery
- **Mixed scripts** — Latin display + Greek/Cyrillic/CJK accents for international voice
- **Drop caps** — first letter of paragraph sized 4-6× body
- **Hanging punctuation** — `hanging-punctuation: first` for editorial polish

### Layout
- **Asymmetric grid** — content offset from center, alternating sides
- **Sticky § markers** — left rail with `sticky` `§ 01` numerals
- **Magazine spread** — multi-column body, generous line-height
- **Hero + rail** — hero takes 7-8 cols, supporting nav/meta in 2-3 col rail
- **Pinned scroll-tied** — sticky + scroll-driven content swap
- **Asymmetric featured grid** — hero tile + smaller tiles, varying sizes
- **Magazine masthead title bar** — wordmark + accent + tagline in mono caps

### Color
- **Single hero accent** — one signature color, used like a weapon
- **Warm off-white** — never pure `#fff` (try `#FAF8F3`, `#F1ECE2`, `#FBF6EB`)
- **Warm-tinted near-black** — never pure `#000` (try `oklch(0.18 0.02 280)`)
- **Mesh gradient atmospheres** — multi-stop radial gradients layered
- **Mix-blend-mode** — `mix-blend-mode: difference` / `multiply` for dramatic interaction

### Asset generation
- **CSS-rendered illustration** — gradients + shapes for hero visuals
- **SVG illustration** — geometric, abstract, layered (see `../../references/web-svg-illustration.md`)
- **Generated bitmap image** — use GPT/Codex image generation when available for specific hero imagery, product concept art, textures, realistic scenes, or empty-state illustrations
- **Generated text glyphs** — large characters as image substitute
- **Mesh gradient as hero** — full-bleed atmospheric backdrop
- Read `../../references/web-svg-illustration.md` for full asset-generation strategies

## Step 2 — Always do these (non-negotiable baseline)

Every web output, regardless of direction:

- **Real custom typography** — never Inter / Space Groteske / Roboto / system-ui as primary face. Pick from `../../references/web-fonts.md`.
- **Real semantic copy** — no "Lorem ipsum", no "Built for modern teams", no "10x faster". Read `../../references/web-copy-voice.md`.
- **Real visual content** — generate SVG / CSS art, never `<img src="placeholder.png">` or `via.placeholder.com`.
- **Asset plan** — decide icons, screenshots, references, generated images, typography, and attribution before adding assets.
- **Reference extraction** — if using real product references, extract job, IA, hierarchy, state coverage, interaction, recovery, responsive behavior, and asset use; do not copy visuals.
- **Accessibility baseline** — semantic HTML, focus-visible rings, WCAG AA contrast, `prefers-reduced-motion` respected.
- **Performance discipline** — lazy-load below-fold, no layout thrashing in scroll motion, font-display: swap.
- **Surface-fit baseline** — marketing pages may be spacious and expressive; dashboards, editors, checkouts, and agent-run UIs must preserve task density, stable controls, and state visibility.
- **Responsive containment** — nav rows, dense tables, toolbars, inspectors, and long labels must wrap, collapse, or scroll inside their own region; never leave mobile/tablet page-level horizontal overflow.
- **Quality bar note** — for public-facing or "make it better" work, state the specific job, proof surface, required states, scan-speed decision, and memorable anchor before implementation.
- **Creative direction** — for original/high-craft work, state the world, metaphor, material language, repeated motif, forbidden defaults, tasteful risk, and restraints.
- **Implementation track** — choose static, Vite React, Next, Astro, or existing stack by actual interaction needs and dependency risk.
- **Interaction decision** — when motion/scrolling is non-trivial, state budget, techniques, library choice, why it fits, reduced-motion behavior, and rejected techniques.
- **Cinematic system** — for campaign-style pages, state the mode, key art, art direction, typography system, page rhythm, and repeated motif before implementation.

## Step 3 — Deploy 2-4 signature motion moments

Pick from technique inventory above. Examples per direction:

- **Editorial**: letter-stagger hero + scroll-driven `reveal-on-scroll` + variable-font hover + Lenis smooth scroll
- **Brutalist**: instant page render (no curtain) + cursor-following snap + marquee + `mix-blend-mode: difference` highlight
- **Type-as-hero**: scroll-pinned headline morph + variable-axis cursor-Y hover + page-load curtain + mesh gradient atmosphere
- **Glow + grain**: page-load curtain + mesh atmosphere + scroll-driven glow shift + magnetic CTAs
- **Industrial mono**: terminal-style typewriter intro + log-stream marquee + monospace number tickers + cursor swap
- **Active bento**: layoutId connected animations + tile-expand on hover + scroll-snap sections + custom cursor "VIEW"
- **Cinematic campaign**: giant composed title + key-art parallax + one pinned craft/proof moment + collection/gallery transition

Don't deploy all 17 techniques. Pick 2-4 that reinforce the direction.

Before adding GSAP, Lenis, native scroll-driven CSS, custom cursors, pinned scroll, parallax, or view transitions, check `../../references/ui-patterns/interaction-techniques.md`. If the surface is a dashboard, docs, checkout, editor, admin panel, or form-heavy workflow, default back to subtle/functional interaction.

## Step 4 — Anti-slop ban list (always enforced)

Read `../../references/web-bans.md` for full list. Top tells of AI-generated UI:

- `from-purple-500 to-pink-500` gradients (top tell)
- Inter / Space Grotesk as primary face
- Three feature cards w/ Lucide icons + "Built for modern teams"
- Hero: H1 + sub + indigo button + ghost button (universal SaaS)
- `rounded-2xl` everywhere uniformly
- Default shadcn theme untouched
- `bg-slate-950` + `text-slate-300` + indigo accent (VS-Code-as-product)
- Centered everything, no asymmetry
- `<img src="placeholder">` / via.placeholder.com / unsplash random
- Lorem ipsum copy
- Identical 80px section padding throughout (kills rhythm)
- "Powered by AI" sparkle badges
- Emoji bullets

## Step 5 — Forbidden combinations (anti-patterns)

Within direction-aware design, certain combos are wrong:
- **Editorial Swiss + Material shadows** → use rules + warm paper, never elevation
- **Brutalist + soft springs** → snappy timing only (`cubic-bezier(0.85,0,0.15,1)`)
- **Glow+grain + pure white background** → atmosphere needs depth
- **Industrial mono + serif body** → mono-everywhere or paired w/ extreme grotesque
- **Active bento + static cards** → must move/expand
- **Type-as-hero + decorative imagery** → type IS the image

## Step 6 — Self-audit before shipping

Ask before delivering output:

1. Did I pick a real direction + commit to it?
2. Did I choose the right surface type and density?
3. Did I avoid every item on `web-bans.md`?
4. Real custom typeface (not Inter / Space Grotesk)?
5. Real copy (not lorem / "Built for modern teams")?
6. Real visual content (no `<img placeholder>`)?
7. Motion budget matches the product type?
8. Direction-specific reference apps fit-check passed?
9. Accessibility baseline (semantic HTML, focus rings, AA contrast, reduced-motion)?
10. Layout breaks the wrong template for this surface type?
11. Dark mode (if applicable) has warmth/coolness, not just inversion?
12. Mobile/tablet has no page-level horizontal overflow?
13. Does the design show product proof instead of only making claims?
14. Did I choose an interaction budget and reject the wrong motion libraries for this surface?
15. For cinematic pages, did I define key art, section rhythm, typography discipline, and repeated motifs before motion?
16. Did the implementation track fit the interaction model, and did I avoid adding React/dependencies when static code would be enough?
17. Did the design include one tasteful risk plus restraints, instead of random creativity?

If any "no" — restart that choice, don't ship near-misses.

## Step 7 — Quality bar reference points

Default to fitting alongside one of these. Read `../../references/awwwards-ceiling.md` for direction-grouped refs.

- linear.app — fast, dark, precision
- stripe.com / stripe.com/sessions — gradient mastery
- vercel.com — animated build log hero
- raycast.com — dark craft, micro-interactions
- resend.com — type-driven dev tool benchmark
- liveblocks.io — Awwwards-tier motion
- arc.net / browser.company — consumer feel
- studiofreight.com / lusion.co — interactive studio ceiling
- igloo.inc — 3D Awwwards SOTY-tier
- werkstatt.fyi — brutalist editorial

## Read also

- `../../references/design-philosophy.md` — core thesis
- `../../references/web-patterns/*.md` — copy-paste pattern library
- `../../references/ui-patterns/reference-analysis.md` — structure extraction from shipped references
- `../../references/ui-patterns/creative-direction.md` — original art direction, tasteful risk, and constraints
- `../../references/ui-patterns/interaction-techniques.md` — motion, scroll, and interaction decision system
- `../../references/ui-patterns/cinematic-landing-system.md` — campaign page/key art/page rhythm system
- `../../references/ui-patterns/web-implementation-tracks.md` — static/React/Next/Astro stack decisions and dependency safety
- `../../references/web-direction-*.md` — per-direction full implementation
- `../../references/web-fonts.md` — type pairings
- `../../references/web-bans.md` — anti-slop list
- `../../references/web-motion.md` — motion library docs
- `../../references/web-copy-voice.md` — editorial copy patterns
- `../../references/web-svg-illustration.md` — no-image asset generation
- `../../references/web-layouts.md` — layout pattern catalog
- `../../references/awwwards-ceiling.md` — quality bar refs grouped by direction
