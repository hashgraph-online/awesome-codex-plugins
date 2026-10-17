# Web Site Redesign Protocol

This is the Web-only protocol for redesigning a living site. Native and embedded-shell redesigns use the shared UX and claim-triggered visual/spatial overlays plus their platform and composition references; they do not inherit the browser, SEO, analytics, or real-browser rules below.

Greenfield rules applied to a living site are how redesigns go wrong: the model overwrites a working brand with its own taste, breaks applicable discovery contracts, and silently renames things analytics depends on. A redesign is evidence-first work — audit what exists, classify the mode, then change the least that satisfies the brief. Apply this protocol only when a visual Web redesign is actually in scope; a narrow nonvisual change does not require a redesign audit, design artifact, anti-slop pass, or visual capture.

## Mode detection (first action)

- **Greenfield** — no existing site, or a full restart is explicitly approved. Normal skill flow applies.
- **Preserve** — modernize without breaking the brand. Audit the existing authoritative design source first and evolve it gradually; do not move ownership into a new file.
- **Overhaul** — new visual language over existing content. Treat visuals as greenfield; preserve content and information architecture unless a separate IA change is actually in scope and explicitly approved from the recorded audit.

If the mode is a material unknown that cannot be resolved from the brief, repository, and current surface, ask whether to preserve the existing brand or start visually from scratch. Ask the minimum necessary questions and batch independent material unknowns instead of forcing a separate one-question round trip. Otherwise state the evidence-based mode, assumption, and confidence.

## Audit before touching (recorded as evidence)

Write `REDESIGN_AUDIT.md` under the evidence root before proposing changes, covering:

- **Brand tokens** — primary/accent colors, type stack, logo treatment, radii, and their authoritative repository owner. In preserve mode that existing owner remains the starting contract; `DESIGN.md` is used only when already established or as a synchronized scoped mapping/receipt.
- **Information architecture** — page tree, primary nav, key conversion paths.
- **Content blocks** — what exists, what is doing work, what is filler.
- **Patterns to preserve** — signature interactions, a recognizable hero, the copy voice.
- **Patterns to retire** — anti-slop tells, broken layouts, dead links, generic stock imagery, performance traps.
- **Visual-direction reading of the existing site** — record how far its visual language departs from the established system, the quantity and complexity of motion, and its information and spacing density. Ground each description in concrete evidence such as component variation, transition count and duration, content per viewport, and whitespace rhythm; this observed reading, not a greenfield preset, is the starting point.
- **Discovery baseline** — for the current crawlable public Web target, or a distinct deployed public Web target in scope, record ranking pages, meta titles, structured data, and share metadata. For authenticated, private, native-only, or embedded-only delivery without a distinct public deployment, record `SEO: N/A` with the concrete deployment reason; visual Web technology alone does not make SEO applicable.

Evidence availability is part of the audit. When analytics, Search Console, ranking history, or another source is unavailable, mark that field **unavailable and unverified, never guessed**. State whether the missing source blocks a named success criterion; otherwise continue with the observable repository/browser evidence and preserve the unknown contract conservatively.

## Preservation rules

- **Information architecture stays by default.** Page slugs, anchor IDs, primary nav labels, and conversion paths remain stable for discovery and muscle memory. Change broken IA only when information architecture is actually in scope, the audit identifies the concrete failure and downstream impact, and the user explicitly approves that IA change; a visual overhaul alone is not approval.
- **Extract brand colors before applying the anti-slop palette bans.** A brand that is already purple stays purple — that is the named override path, not a violation.
- **Copy voice is preserved** unless a rewrite is requested; visual modernization is not a content rewrite.
- **Existing accessibility wins never regress** — focus states, alt text, keyboard nav, contrast.
- **Analytics contracts hold** — do not rename tracked buttons, form field names, or section IDs without locating and updating the downstream contract.

## Never change silently (explicit user approval required)

URL structure and route slugs; primary nav labels; form field names; the brand logo or wordmark; legal, consent, and cookie copy. Treat field order separately: inspect analytics, autofill, validation, and task flow, then get approval when reordering changes one of those contracts.

## Modernization levers (apply in order, stop when the brief is satisfied)

1. **Typography refresh** — the biggest visual lift per unit of risk.
2. **Spacing and rhythm** — section padding, vertical rhythm.
3. **Color recalibration** — desaturate, unify neutrals, keep the brand accent.
4. **Motion layer** — evidence-backed micro-interactions that fit the preserved visual direction and existing components (`references/motion-core.md`, plus `references/motion.md` only for Web implementation).
5. **Hero and key-section recomposition** — restructure the top of the funnel.
6. **Full block replacement** — only when a block is unsalvageable.

## Decision tree

- IA, content, and SEO are sound → **targeted evolution** (levers 1–4): most of the value at a fraction of the risk.
- Visual debt is structural (for example incoherent or unowned visual semantics or broken supported-target adaptation) → **full visual redesign** with strict content and information-architecture preservation. Broken IA is a separate change: include it only when it is actually in scope and explicitly approved from the audit. The absence of a formal design-system document alone is not structural failure.
- The brand itself is changing → treat as **greenfield**.

For an actual redesign, completion preserves the project's authoritative design source and uses `DESIGN.md` only when it is established or a synchronized scoped mapping. Run anti-slop only for its declared marketing/editorial or approved new-visual-direction scope. Capture real-browser visual QA across the target-derived browser/OS/input and breakpoint matrix, exercise the affected and adjacent journeys, and retain the evidence record plus `REDESIGN_AUDIT.md` proving the before-state was read rather than guessed. SEO proof remains limited to the current crawlable public Web target or a distinct deployed public Web target in scope.

Selected redesign mechanisms were adapted under MIT from Taste Skill; see `references/upstream-notice.md`.
