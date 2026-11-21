# No-Missed Quality Gates

Use this reference when Suede work touches public copy, visual design, design
systems, reference-site restyling, page visibility, launch packaging, or
agent-team delivery. These gates add quality pressure without replacing the
existing Suede rules for creator ownership, programmable IP, rights,
provenance, registry-backed media, royalty routing, licensing readiness, agent
commerce, mobile and product surfaces, SEO/AEO/AI EO, public evidence integrity, WIP
protection, and evidence handoff.

## Preservation Gate

Before adding or tightening a workflow, list the current Suede features that
must survive the edit:

- target skill trigger and description;
- Suede-specific language around rights, provenance, royalties, licensing,
  agent commerce, and creator ownership;
- product screenshots, mobile onboarding, paywall, and app-shell support
  when already present;
- SEO, AEO, AI EO, GitHub Pages, Google, Gemini, AI search, metadata, FAQ,
  schema, sourceable proof, and internal-link behavior;
- Suedify reference-site capture, token distillation, safe translation, and
  screenshot comparison behavior;
- design-system quality of life artifacts, state coverage, accessibility, and
  responsive QA;
- agent-team lanes, WIP protection, release lock, recovery, and handoff loops;
- evidence boundaries and the ban on invented metrics, partners, payouts,
  registry writes, clearance, rankings, pricing, testimonials, or release
  promises.

If an edit would weaken one of those features, stop and choose an additive
shape instead.

## Copy Gate

Run this gate before public copy is accepted.

- Cut throat-clearing, filler transitions, emphasis crutches, business jargon,
  adverbs, softeners, vague declarations, rhetorical questions, performative
  intensity, fake stakes, and meta-commentary about the writing.
- Avoid formulaic structures: binary setup lines, negative lists that define
  the product by what it is not, dramatic fragments, three-part cadence by
  reflex, obvious contrast pairs, and quote-bait lines that sound detached from
  the product.
- Prefer active voice with a human or product actor. Replace inanimate subjects
  that pretend to act with the real user, team, system, page, file, or action.
- Put the reader in the room: name the concrete artifact, state, action, risk,
  link, command, workflow, or proof that makes the claim believable.
- Do not begin most lines with `What`, `When`, `If`, `This`, or `It` when a
  direct actor and verb would be clearer.
- Keep one idea per sentence. Vary sentence length without using em dashes.
- Do not sand off Suede specificity. Preserve rights, provenance, registry,
  royalty, licensing, agent commerce, creator ownership, mobile product, and
  discoverability language when it is relevant and true.

Score meaningful public copy:

```text
Directness: /10
Rhythm: /10
Trust: /10
Specificity: /10
Authenticity: /10
Search/AI readability: /10
Density: /10
Total: /70
```

Revise below 58/70. For launch, homepage, GitHub, product listing, public
explainer, or investor-adjacent copy, aim for 62/70 or higher.

## Design Gate

Run this gate before major visual work, reusable UI, public launch surfaces,
Suedify work, product screenshot assets, or design-system passes.

Preserve the existing product brand, deliberate style and authorized scope.
A read-only review reports findings and proposed fixes without editing files;
approved copy, claims and assets remain unchanged unless their revision is
authorized. Distinguish standards for accessibility and correctness from
context-dependent conventions and stylistic suggestions. A deliberate departure
from a convention is not a defect without a concrete task or usability impact.

- Name the subject, audience, page job, primary action, launch stage, and
  register before making visual decisions.
- Pick the register deliberately:
  - **Brand:** can carry a sharper point of view, signature image, distinctive
    type pairing, stronger color commitment, and one memorable subject-native
    move.
  - **Product:** should feel earned, efficient, state-rich, predictable, and
    compact enough for repeated work.
  - **Docs:** should favor scannability, sourceable proof, install clarity,
    durable headings, and citation-friendly structure.
- Write the physical scene: who uses this, where, under what pressure, what is
  on screen, and what they need to do next.
- Choose a color strategy before values: restrained, committed, full palette,
  or drenched. Start from existing tokens and semantic roles; assess contrast,
  state distinctions and color meaning. OKLCH and tinted neutral palettes are
  optional techniques, not requirements to replace an approved palette.
- Use typography as product voice: deliberate pairing, clear roles, body copy
  that fits the reading task, and hierarchy that remains legible across states
  and viewports. Evaluate type steps, measure, tracking and fluid sizing in the
  actual product; do not impose a fixed ratio or remove approved fluid type.
- Make the structure explain the product. Evaluate cards, nested groups,
  repeated grids, glass, gradients and modal interactions against the task,
  content hierarchy and accessibility. Name the concrete failure before
  recommending a structural or stylistic replacement.
- Give emphasis to the product's important action or information. An approved
  Suede surface may use a rights passport, waveform ledger, provenance receipt,
  chain-of-title map or studio console; other products keep their own vocabulary
  and deliberate visual identity.
- Motion must serve state or comprehension and respect reduced motion. Inspect
  animation performance and interaction feedback; stylistic motion choices
  need a contextual reason, not a blanket prohibition.
- Self-critique before build: name the generic default this could fall into,
  then state the specific product choice that prevents it.

## Design-System Gate

For a major surface or component family, scan existing source before inventing
tokens. Capture the smallest useful artifact set:

- token map for color roles, typography, spacing, radii, shadows, motion,
  z-layers, charts, statuses, and semantic states;
- component inventory for navigation, controls, cards, lists, forms, media,
  paywalls, proof modules, rights/provenance modules, loading, empty, errors,
  and permission states;
- state matrix for default, hover, focus, active, disabled, loading, empty,
  success, warning, error, offline, unauthenticated, and permission-denied
  states where relevant;
- preview gallery or reproducible screenshot contract with seeded synthetic
  content representative of the target product;
- asset register for logos, app icons, product images, screenshots, crop rules,
  attribution, and export sizes;
- migration notes that name what old patterns remain and what not to rewrite.

Score design-system work across ten lanes:

```text
Color consistency: /10
Typography hierarchy: /10
Spacing rhythm: /10
Component consistency: /10
Responsive behavior: /10
Dark/light behavior: /10
Motion restraint: /10
Accessibility: /10
Information density: /10
Polish: /10
Total: /100
```

Use the score to direct fixes, not as a vanity metric.

## Visual QA Gate

For source-to-implementation comparison, use the source visual target and the
rendered implementation together in the same comparison pass. Do not compare
one from memory.

Source-only inspection never establishes a rendered visual pass. Mark unavailable
renders and states as not observed, with the exact limitation. Before executing
a component preview, establish import, module and server isolation as required
by the component workflow; browser request interception alone is insufficient.

- Match viewport, device, state, theme, auth state, route, content, seeded data,
  and interaction state.
- Capture full-view evidence first, then focused-region evidence for typography,
  spacing, icons, logos, imagery, charts, buttons, forms, and hard-to-read
  details.
- Compare these fidelity surfaces: typography, spacing/layout, colors/tokens,
  image and asset fidelity, copy/content, interaction states, accessibility,
  responsive behavior, and motion where relevant.
- Treat replacement of target assets, logos, illustrations, icons, product
  imagery, or screenshot content with CSS shapes, emoji, placeholder divs,
  improvised SVGs, or text approximations as a blocking defect unless the user
  explicitly asked for that substitution.
- Save the QA artifact named by the relevant skill, usually
  `visual-qa-report.md` or `suedify-visual-qa.md`, with source truth,
  implementation evidence, viewport/state, findings, patches, caveats, and
  `final result: passed` or `final result: blocked`.

Finding format:

```text
Severity:
Location:
Evidence:
Impact:
Fix:
```

## Agent-Team Loop Gate

Use the smallest useful loop, but make quality measurable:

1. Scout current truth, WIP, source files, live/rendered surfaces, and no-touch
   boundaries.
2. Plan atomic lanes with file ownership and observable acceptance criteria.
3. Execute only non-colliding lanes in parallel.
4. Review with at least two lenses when stakes are high: one for intended
   behavior, one for failure modes.
5. Verify the done signal with commands, screenshots, live/API readback, or
   saved QA artifacts.
6. If the same failure repeats, freeze broad work, isolate the failing unit,
   reduce scope, patch only the authorized gap, and rerun the failed check.
   For interface validation, reproduce, make the authorized fix, recapture the
   matched state, and inspect until the scoped outcome is verified or a concrete
   blocker is identified. A fixed pass count cannot substitute for evidence.
   Read-only interface reviews report findings without making application edits.
   For other workflows, allow up to three genuinely different fixes per failing
   check; stop early when the same root cause repeats and hand the call to the
   user.
7. End with evidence: changed files, commands, screenshots or URLs, caveats,
   status, and exact next action.
