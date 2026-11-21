# Fix Playbook

Load only the entry that matches a confirmed finding. Preserve the brief, content, data shape, semantics, and behavior before optimizing visual distinctiveness.

## Gradient headline

1. Confirm whether the brief, brand tokens, or explicit reference requires gradient typography.
2. If required, `preserve` and record the exception.
3. Otherwise replace it with the existing primary ink or a confirmed solid accent token.
4. Check contrast and the resulting hero hierarchy in a rendered view. Without rendering, report hierarchy as unverified.

## Purple gradient

1. Resolve colors to named project tokens where possible.
2. Preserve documented brand gradients.
3. For unsupported gradients, prefer an existing solid surface/accent or a brief-aligned restrained combination; do not invent a new palette.
4. Verify contrast, dark mode, and neighboring state styles.

## Decorative orb, pill, dot, label, or proof

1. Check content, interaction, state, semantic, brand, analytics, and layout roles.
2. Remove only when no role is found and source/DOM/brief evidence is high-confidence.
3. Preserve meaningful accessible names and status signals.
4. After removal, inspect spacing, pointer events, contrast, layout shift/LCP implications, and responsive fit.

## Three equal feature cards

1. Confirm whether there are genuinely three peers or an explicit comparison requirement. If yes, preserve the cardinality.
2. If cards merely repeat value propositions, review alternatives in this order: one primary feature plus supporting list; two-column zig-zag; asymmetric grid; typographic list; intentional carousel only when overflow is part of the interaction.
3. Preserve copy, links, actions, reading order, semantics, and data mapping.
4. Verify desktop/mobile layout, keyboard order, CTA placement, and detector output.

## Card in card

1. Identify which boundary carries real grouping, interaction, or elevation meaning.
2. Remove only redundant presentation wrappers; do not flatten semantic groups or clickable regions.
3. Keep padding and focus treatment on the boundary that remains.
4. Check DOM nesting, hit targets, focus visibility, and mobile spacing.

## `transition-all`

1. Enumerate the properties that actually change in hover/focus/active/state styles.
2. Replace `all` with only composited or intended properties, such as `color`, `background-color`, `border-color`, `opacity`, or `transform`.
3. Do not transition focus-ring appearance when it delays visible focus.
4. Verify interaction states and reduced-motion behavior.

## Layout-property animation

Prefer transform/opacity only when the same behavior and reading order remain. If changing mechanics risks state or layout correctness, report and ask rather than auto-rewriting choreography.

## Placeholder copy or unsupported metrics

1. Search local product sources, fixtures, CMS/data wiring, and brief for provenance.
2. If clearly placeholder decoration and not a functional fixture, remove the unsupported block rather than invent replacement claims.
3. Never fabricate a metric, testimonial, logo, customer, or product promise.
4. If the copy participates in tests, localization, data contracts, or legal review, preserve and ask.

## Fake browser/phone/IDE chrome

Preserve when it frames a real screenshot or communicates product context. Otherwise remove only decorative controls while keeping the real asset, caption, alt text, and layout semantics. Verify the remaining asset still communicates its purpose.

## Missing focus/reduced motion/alt

Treat these as quality guards, not aesthetic slop. Use project accessibility conventions and observable behavior. Determine whether an image is informative or decorative before choosing descriptive or empty alt. Do not claim full accessibility from source inspection alone.

## Repeated section scaffolds, glow, grid, monospace, pulse, or heading skip

1. Confirm the pattern is not an explicit sequence, code/data/state treatment, documented elevation/material system, or brand commitment.
2. Read `replacement-patterns.md` before proposing a structural alternative; preserve data, actions, semantics, focus order, and responsive behavior.
3. Treat `candidate` exception as preservation evidence. Do not suppress the finding or modify adjacent brand/data choices.
4. For heading order, inspect component composition before changing levels. For pulse/motion, preserve state communication and reduced-motion behavior.
5. Report static-only limitations unless a validated rendered handoff confirms viewport/state/locator facts.

## Baseline, waiver, and rendered handoff

1. A baseline compares detector v2 findings only; it never approves a design choice. Read `rules/waivers-and-baselines.md` before `--only-new`.
2. Validate an optional waiver with `validate-waivers.sh`. It must be narrow, reasoned, and sourced; it cannot hide a P0 or protected contract.
3. Validate supplied browser facts with `collect-rendered-evidence.sh`. Use only the captured viewport/state/locator observations.
4. Do not install tooling or write a consumer config file to obtain any of these inputs.

## Sources

> Claims checked 2026-09-21. No external source was used in this file.

The remediation steps are this package's own guidance, derived from the anti-pattern catalog and the safe-editing rules. No external design or accessibility source was consulted.
