# Command Playbook

This is the intent-to-action dispatch table for designer-skill. Find the verb whose intent cue matches what the user wants, then read the file(s) in its Read column before you touch anything. The Read column points only to sibling reference files in this skill; open them, do not guess from memory. One verb usually owns the task; if two fit and one intent clearly dominates, pick it and let the other's file be a secondary read — if genuinely ambiguous, ask the user once which they mean. Concrete values in the moves are starting points, not laws.

## Dispatch table

| Verb | When to invoke (intent cue) | What it does (concrete moves) | Read |
|---|---|---|---|
| build | "build / make / create" a feature, page, or component end-to-end | Detect framework/library/icons first (ask once on greenfield), set baseline (type, spacing, contrast), commit to one aesthetic language, wire motion + tokens, ship production code with real content and all states; gate stages and run the visual iteration loop (see Build gates below) | design-principles.md, aesthetic-systems.md, engineering-and-performance.md, avoid-ai-slop.md, craft-flow.md |
| plan | "plan / spec / think through" a feature before code | Run a discovery interview (see Plan protocol below), pick color strategy + a one-sentence physical scene + 2-3 named anchor references, produce a brief, present it, and stop; write no code | design-principles.md, aesthetic-systems.md |
| check | "check / review the implementation, a11y, perf, responsive" | Score accessibility, performance, theming, responsive, anti-patterns 0-4; tag findings P0-P3 with fix + suggested verb; for a11y, split automated-detectable findings from manual-review ones and never certify full WCAG conformance from automated checks alone; fix nothing | engineering-and-performance.md, avoid-ai-slop.md, refactor-and-redesign.md |
| review | "is this good? / design review / does this feel AI?" | Design-director read: hierarchy, IA, cognitive load, heuristics, emotional journey; lead with the AI-slop verdict; list 3-5 priority issues; full instrument in the Scored review protocol below | design-principles.md, avoid-ai-slop.md, visual-critique.md |
| finish | "final pass / tighten before shipping" | Align to the design system, snap spacing to scale, complete every interaction state (hover/focus/active/disabled/loading/error), fix optical alignment, 150-300ms transitions | design-principles.md, engineering-and-performance.md |
| amplify | "too safe / bland / make it pop" | Amplify hierarchy: 3-5x scale jumps, weight 900 vs 200, one color owns ~60%, break the grid; reject gradient-text/glass/neon first | aesthetic-systems.md, avoid-ai-slop.md |
| calm | "too loud / busy / aggressive" | Reduce intensity: desaturate to 70-85%, neutrals carry weight with accent ~10%, flatten cards, shorten motion to 10-20px; keep the POV | design-principles.md, aesthetic-systems.md |
| push | "extraordinary / push past limits / wow" | Highest-ambition effects (View Transitions, scroll-driven, WebGL, virtual scroll). Propose 2-3 directions, get user pick, then build with graceful fallback at 60fps | motion-and-interaction.md, engineering-and-performance.md |
| motion | "add motion / it feels static / smooth this" | Add purposeful motion: 100/300/500ms by tier, ease-out-quart, sibling stagger (not section fade), reduced-motion alternative required | motion-and-interaction.md |
| delight | "personality / memorable / charm" | Earn specific moments (success, empty, error recovery) with custom copy + micro-interactions under ~1s; never on every interaction, never generic AI filler | motion-and-interaction.md, avoid-ai-slop.md |
| layout | "fix spacing / hierarchy / it feels off" | 4pt scale (4/8/12/16/24/32/48/64/96), tight grouping vs 48-96px section gaps, flex for 1D + grid for 2D, break card-grid monotony, pass the squint test | design-principles.md |
| type | "typography / fonts / hierarchy" | Replace invisible defaults, 5-size scale at >=1.25 ratio, weight + size + space hierarchy, 65-75ch measure, font-display: swap, cap 3 families | design-principles.md |
| color | "flat / grayscale / add color" | Pick a color strategy first, OKLCH ramp, 60-30-10 weight, tinted neutrals toward the brand hue, semantic meaning consistent, body text >=4.5:1 | design-principles.md, aesthetic-systems.md |
| ship | "production-ready / edge cases / real data" | Survive long/empty/CJK/RTL/emoji text, all API error states with recovery, 30-40% i18n space budget, no fixed text widths, server-side validation | engineering-and-performance.md |
| speed | "slow / janky / perf" | Measure first, fix the actual bottleneck: LCP<2.5s, INP<200ms, CLS<0.1; image formats + lazy load, code split, transform/opacity over layout props | engineering-and-performance.md |
| simplify | "too complex / cluttered / strip it back" | Remove elements that don't earn their place: one primary goal, progressive disclosure, 1-2 colors + neutrals, flatten nesting, halve the copy | design-principles.md |
| tokens | "make reusable / tokens / design system" | Pull patterns used 3+ times with the same intent into tokens + components with a clear props API, migrate call sites, delete the old; avoid premature abstraction | engineering-and-performance.md, design-systems.md |
| brand | "brand identity / distinctive look / not generic" | Choose an aesthetic language and a named reference, run the font-selection procedure (reject training-data defaults + saturated lanes), commit a palette strategy | aesthetic-systems.md, avoid-ai-slop.md |
| responsive | "mobile / tablet / different device or context" | Rethink the experience for the target (not scale pixels): single-column reflow, 44x44px touch targets, detect pointer/hover, content-driven breakpoints, safe-area insets | engineering-and-performance.md, refactor-and-redesign.md |
| refresh | "improve / fix this existing UI without breaking it" | Audit current state, diagnose generic AI patterns and drift, run the redesign loop preserving function; image-to-code when matching a visual target | refactor-and-redesign.md, avoid-ai-slop.md |
| copy | "rewrite this error / these labels are confusing / fix the microcopy" | Verb+object button labels, what-happened/why/how-to-fix error copy, one term per concept, instructions before the field; run the Copy kit below — this file owns UX copy | avoid-ai-slop.md, command-playbook.md |
| onboard | "first run / empty states / activation / product tour" | Shortest path to first value: 5-part empty-state anatomy, the five empty-state types, skippable 3-7-step tours; run the Onboard kit below | engineering-and-performance.md |
| spec | "capture the design system / write or refresh DESIGN.md" | Scan tokens + components and generate or refresh DESIGN.md so later work stays on-brand; never overwrite without asking | refactor-and-redesign.md |
| options | "show me options / 3 versions of this hero" | Variation within identity, never three different brands: extract the identity lock, pick default vs departure mode, vary each option on a different axis | refactor-and-redesign.md, avoid-ai-slop.md |
| form | "form design / form validation / input fields / multi-step form" | Single-column layout, top-aligned labels (never placeholder-only), blur validation (not every keystroke), error message directly below the failing field, multi-step when >7 fields — name each step in the indicator; mark optional not required | interaction-design.md, engineering-and-performance.md |
| nav | "navigation / nav / sidebar / tab bar / breadcrumb / menu structure" | Match pattern to IA depth and platform: tab bar (mobile, 3-5 destinations), sidebar (desktop, many/nested), top nav (simple sites), breadcrumbs (deep hierarchies); active states distinguishable beyond color alone; never hamburger for primary nav on desktop | interaction-design.md, design-principles.md |
| states | "state machine / all states / every state / impossible state / model behavior" | Map the UI as finite states (idle/loading/success/error/empty); every state has one visual representation and at least one exit; eliminate impossible combinations (never loading + error simultaneously) | interaction-design.md, engineering-and-performance.md |
| tone | "feels flat / no personality / feels cold / humanize / feels dead / too sterile" | Name the felt state → find a physical analogue → extract a behavioral property → apply to easing, delay, copy tone, or duration; run the Copy voice by state table; motion-as-signal: ease-out lands softly, spring bounces, stiff spring = confident | interaction-design.md, motion-and-interaction.md |
| system | "design system / token architecture / theming / component library / dark mode system / naming convention" | Two-layer tokens: global primitives → semantic aliases; component specs cover all 8 states; naming {category}-{property}-{concept}-{variant}-{state}; themes override semantic tokens; dark mode reduces brightness, uses surface-elevation not shadows | design-systems.md, engineering-and-performance.md |
| setup | "bootstrap project / write PRODUCT.md / first time" | One-time project setup: discovery interview, PRODUCT.md, optional DESIGN.md, preview-mode config, recommend next commands | project-init.md |
| preview | "browser variants / iterate in the browser / live mode" | Select elements in the running app, generate HTML+CSS variants hot-swapped via HMR | live-mode.md |

## Register modifiers

The toning verbs mean different things per register (the register decision lives in SKILL.md's preflight). Read your verb's row before amplifying or calming anything:

| Verb | Brand register | Product register |
|---|---|---|
| amplify | Extreme scale, unexpected color, typographic risk | Stronger hierarchy, clearer weight contrast, one sharper accent, more committed density — amplify clarity, not drama; theatrics erode trust |
| calm | Restrain the palette, add air, keep the point of view intact | Fewer background accents, flatter cards — the tool disappears into the task |
| delight | Distributed across copy voice, transitions, discoverable details | Moments only: completion, first-time actions, error recovery, milestones |
| motion | One well-rehearsed entrance beats scattered micro-interactions | 150-250ms, state-conveying only, no page-load choreography |
| color | The palette IS the voice; dosage follows the color strategy | Semantic-first; almost always a Restrained strategy |
| layout | Asymmetry, fluid clamp, deliberate grid-breaking | Predictable grids, structural responsiveness — consistency is itself an affordance |
| type | Run the font procedure; fluid clamp, scale ratio >=1.25 | One family, fixed rem sizes, scale ratio 1.125-1.2 |

## The intensity dial

The toning verbs sit on one axis:

`calm ← simplify ← (finish / baseline) → amplify → push`

Move **right** when the design is timid, low-contrast, generic, or forgettable: `amplify` for stronger hierarchy and committed color, `push` when the brief wants a technically extraordinary moment (propose 2-3 directions and get user confirmation before building). Move **left** when the design is loud, noisy, or cluttered: `calm` *reduces intensity* (desaturate, flatten, calm the motion) while keeping every element; `simplify` goes further and *removes elements* down to the essence. `finish` is the neutral center: it refines what's there without shifting the volume in either direction.

Verbs also chain in a fixed pipeline: **evaluate (check / review) → fixing verbs → finish → ship gate**. Evaluation verbs fix nothing — they end by mapping each finding to the verb that fixes it, and suggest a re-run after fixes to watch the score move. Fixing verbs hand off to `finish` for the final pass; `finish` is always last and never runs before the thing is functionally complete.

## Plan protocol

`plan` is a discovery interview, not a form. The discipline:

- **2-3 questions per round, then wait for answers.** Run at least one real answer round before drafting unless the repo or docs directly answer; round 1 covers purpose / audience / content / visual direction, round 2 only if material gaps remain. Never synthesize a full brief from a sparse prompt and ask for blanket confirmation.
- **Assert, then confirm — don't menu.** When context makes one option obvious, "This reads as Restrained — confirm?" beats a four-option list.
- **Always ask scope:** fidelity (sketch / mid-fi / high-fi / production), breadth (one screen / a flow / the whole surface), interactivity (static / prototype / shipped), time intent (quick exploration vs polish-until-it-ships). Task-scoped — never persisted.
- **Ask about content reality:** realistic data ranges (0 / 5 / 500 items), what's dynamic, which visual assets are real content.
- **Ask the anti-goal:** what should this NOT be; the biggest risk of getting it wrong.
- **Size the brief to the ambiguity:** compact (3-5 bullets ending "confirm or override?") when the prompt + context pin everything; the full brief structure only when genuinely ambiguous or multi-screen. Don't pad to look thorough.
- **Present the brief, then STOP.** User confirmation is the gate — don't skip the pause to look efficient.
- **Decide, don't list.** If you'd write "Recommend: X" next to an open question, just decide X and assert it.

## Build gates & the visual iteration loop

For build — and any verb shipping substantial new UI:

**Step 0 — project foundation.** Detect the framework, component library, and icon set before anything else. On greenfield, ask the framework question once (a content-led brand site, an in-app product surface, and a one-shot demo each suggest different answers) — never pick silently.

**Gates.** Each stage ends with the user: brief → direction → palette → mock. Plan confirmation is not code-green; compressing gates because the brief felt complete is the dominant failure mode.

**The visual iteration loop.** Once code renders, look at what you built like a designer:

1. Screenshot at mobile / tablet / desktop minimum. If your tool returns a file path, read the image back — a screenshot you didn't read doesn't count.
2. On long pages, inspect major sections individually; full-page thumbnails hide spacing, clipping, and cascade defects.
3. Write an honest critique against the brief and the ban-lists, patch material defects, re-inspect.
4. Don't invent defects to demonstrate iteration — "first pass clean, shipping" beats a fake fix.
5. Detector or automated QA output is defect *evidence*, never proof the work is finished.

Exit bar: would this hold up in a high-end studio review? When presenting, show the primary state, summarize viewports checked and post-inspection fixes, walk the key states, explain decisions against the brief, disclose accepted deviations honestly, and ask what's working and what isn't.

## Copy kit (UX copy)

This file owns UX copy; `copy`'s moves in full.

**Button labels — verb + object, never vague:**

| Instead of | Write |
|---|---|
| OK | Save changes |
| Submit | Create account |
| Yes | Delete message |
| Cancel (in a destructive confirm) | Keep editing |
| Click here | Download PDF |

**Errors — three parts, every time:** what happened, why, how to fix it. Per-situation templates:

- Format: "[Field] needs to be [format]. Example: [example]."
- Missing required: "[Field] is required so we can [reason]."
- Permission: "You don't have access to [thing]. Ask [role] to grant it."
- Network: "Couldn't reach the server. Check your connection and try again."
- Server: "Something went wrong on our end. Try again in a moment."

Don't blame the user ("Please enter the date as MM/DD/YYYY", not "You entered an invalid date"). Never humor in errors — the user is already frustrated.

**Terminology — one word per concept, everywhere:** Delete (not Remove/Trash), Settings (not Preferences/Options), Sign in (not Log in), Create (not New/Add). Pick one and hold it across every screen.

**Voice constant, tone shifts by moment:**

| Moment | Tone |
|---|---|
| Success | Celebratory, brief |
| Error | Empathetic, concrete |
| Loading | Reassuring, expectation-setting |
| Destructive confirm | Serious, plain |

**Form copy:** placeholders are never labels (they vanish on focus); instructions go before the field, not after the mistake. **Loading copy** sets expectations — say what is happening and how long it usually takes ("Analyzing your data — usually 30-60 seconds", never bare "Loading...").

## Onboard kit (first-run & empty states)

This file owns onboarding; `onboard`'s goal is **time-to-value** — get the user to their first "aha" moment, not teach everything.

**Empty-state anatomy — all five parts:** (1) what will be here, (2) why it matters, (3) how to get started — a clear CTA, ideally with a template or sample option, (4) visual interest (not a gray void), (5) contextual help.

**The five empty-state types get different treatments:**

| Type | Treatment |
|---|---|
| First use | Full anatomy above — sell the value, offer a starting point |
| User cleared | Acknowledge or celebrate ("Inbox zero"); no tutorial |
| No results | Say what was searched; offer to broaden or fix the query |
| No permission | Say who can grant access and how to ask |
| Error | What happened + a retry path; never a bare sad face |

**Principles:** show, don't tell; everything skippable; teach the 20% that delivers 80% of the value; context over ceremony — teach at the point of use, not in a welcome lecture; track dismissals and never re-show what was dismissed.

**Tours:** 3-7 steps max, spotlight one thing at a time, always skippable, always replayable, workflow-focused ("Create your first project", not "This is the project button").

## Appendix: scored review protocol

The full instrument behind `review` — this file owns the UX-review layer; the visual/technical check table lives in refactor-and-redesign.md.

**Nielsen's 10 heuristics, scored 0-4 each (/40):** visibility of system status, match with the real world, user control & freedom, consistency & standards, error prevention, recognition over recall, flexibility & efficiency, aesthetic & minimalist design, error recovery, help & documentation. Anchors: 0 = absent or actively violated, 1 = major gaps, 2 = inconsistent, 3 = solid with minor gaps, 4 = genuinely excellent. Bands: 36-40 excellent (ship), 28-35 good, 20-27 acceptable, 12-19 poor (overhaul), 0-11 critical (redesign). Honesty calibration: a 4 means genuinely excellent — most real interfaces score 20-32.

**Cognitive-load checklist — 8 items:** single focus per screen; chunking <=4 per group; visual grouping; clear hierarchy; one decision at a time; <=4 visible options per decision point; no memory bridges between screens; progressive disclosure. Scoring: 0-1 failures = low load, 2-3 = moderate, 4+ = critical. The eight named violations, each with its one-line fix: the Wall of Options (chunk or pick a default), the Memory Bridge (carry the context forward), the Hidden Navigation (make wayfinding visible), the Jargon Barrier (use the user's words), the Visual Noise Floor (cut decoration competing with content), the Inconsistent Pattern (one pattern per job), the Multi-Task Demand (one task per screen), the Context Switch (keep the user in flow).

**Severity:** P0 blocks core tasks, P1 major friction, P2 noticeable annoyance, P3 cosmetic. Tiebreak: would a user contact support about this? If yes, it's at least P1.

**Persona walk-throughs** — pick by interface type, report what *broke for them*, not generic descriptions:

| Persona | Red flags |
|---|---|
| Alex — impatient power user | Forced tutorials, no keyboard path, unskippable animation, no batch actions, redundant confirms |
| Jordan — confused first-timer | Icon-only nav, jargon, no help, ambiguous next step, no success confirmation |
| Sam — accessibility-dependent | Click-only interactions, invisible focus, color-only meaning, unlabeled fields, timed actions |
| Riley — stress tester | Silent failures, broken error recovery, useless empty states, data loss on refresh, inconsistent behavior |
| Casey — distracted mobile user | Primary actions outside the thumb zone, no state persistence, typing where selection would do, heavy assets, tiny targets |

| Interface type | Walk it through as |
|---|---|
| Landing page | Jordan, Riley, Casey |
| Dashboard | Alex, Sam |
| Checkout | Casey, Riley, Jordan |
| Onboarding | Jordan, Casey |
| Data-heavy | Alex, Sam |
| Forms | Jordan, Sam, Casey |

**Anchoring discipline:** form your own design-review verdict **before** consulting any detector or automated checker output — deterministic findings anchor judgment. Then weave: where you and the tool agree, what it caught that you missed, which of its findings are false positives.

**Trend loop:** persist the score per target; re-run after fixes and report the trend ("24 → 28 → 32").

**Report shape:** lead with the AI-slop verdict; overall impression; 2-3 things that are working (be specific about why); 3-5 priority issues, each with what / why it matters / concrete fix / suggested next verb; minor observations; close with provocative questions ("What would a confident version of this look like?").

## Always-run gate

Every verb ends by running the avoid-ai-slop.md Anti-Slop Checklist before declaring done; it is the universal ship gate even when it is not in a row's Read column. Partial, placeholder, or truncated output is a hard failure under the output-completeness contract in avoid-ai-slop.md.
