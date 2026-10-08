# Variant Prototyping

When a design decision is genuinely open — two or more directions a stakeholder must choose between — build variants and let them be compared side by side. Prototypes answer questions; they are not a way to avoid deciding. Time-box them, diverge them deliberately, and clean them up after the decision.

## Diverge on a named axis

Each variant must differ on one **named axis**: the specific decision under test (navigation pattern, content density, empty-state strategy, pricing emphasis, onboarding step count). Variants that drift apart on unrelated dimensions answer nothing — the reviewer cannot tell which difference caused which reaction. State the axis before building:

- "Axis: how bulk actions are revealed (toolbar vs selection banner vs contextual menu)" — three variants, same data, same visual language.
- Keep everything not on the axis identical across variants, down to copy and spacing, so the comparison isolates the decision.

Two to four variants is the useful range. Fewer than two is not a comparison; more than four fragments attention and invites arbitrary picking.

## Shippable, not throwaway

Every variant should be built well enough to ship: real tokens, real components, accessible markup, the states the comparison touches. A variant built with placeholder shortcuts biases the review — a broken-feeling variant loses for the wrong reason. "Shippable" does not mean finished: exclude states and surfaces outside the axis deliberately, and say so.

## Keep the prototype surface isolated

Prototyping never authorizes changes to production files. Options, in order of preference:

1. A story, test page or development-only route explicitly excluded from the production build. An unlinked route can still ship and be reached directly; verify build exclusion and keep production side effects disconnected.
2. A dedicated prototype directory or branch the user agreed to.
3. A standalone page reusing the project's real components and tokens (still isolated from shipped surfaces).

Mark prototype-only behavior visibly in the surface itself (a small banner or label) so a half-built variant is never mistaken for a shipped screen. Never wire a prototype into production navigation "temporarily".

## The comparison step

Give the reviewer one surface that switches between variants without losing their place — a query-param toggle, a segmented control, or consecutive routes keyed by variant name. Record, per variant, what a good outcome looks like before showing it (which metric or behavior answers the axis). Collect the decision in terms of the axis, not general preference: "variant B — selection banner — because bulk actions stayed visible with one-handed reach", then record the decision with the direction record when one exists (`commit_design_direction`, `mode` per its schema).

## Promotion and cleanup

Promote one variant into the production surface as ordinary authorized work (the usual gates apply: it is an edit like any other). Then remove the prototype surface, its toggle, and any fixture switches — a leftover variant switcher in production is a defect, and an unremoved prototype directory invites stale-code drift. If the decision is deferred, remove the prototypes anyway and keep only the written findings; rebuilding a variant later is cheaper than maintaining three half-live surfaces.
