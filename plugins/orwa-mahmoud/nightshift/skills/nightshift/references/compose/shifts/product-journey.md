# Product journey — finite — reproducible user-route gaps from explicit journey evidence

Use when the owner names a persona, goal, starting state, and route to exercise. Fix reproducible
gaps the journey surfaces and retest. Error experience, responsive/cross-browser behavior, and
accessibility observations are modes on this entry — not separate catalog items.

Write receipts from `$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/receipts/cycle-specialist-evidence.md`.
The model writes the receipt. Unparsed tool output is `unavailable`, never "no findings".

Supported on projects with a local app, static preview, or browser evidence the owner supplies.
Never select this entry in artifact mode. Do not `git init` a notes folder to make journey evidence
commitable. Never claim whole-product usability or accessibility certification from one script.

## Evidence modes

Product journey runs in exactly one evidence mode per shift (or a declared combination when the
owner supplies multiple observation surfaces). Discovery records the mode before findings are drafted.

### Journey (default)

Exercise the named route from starting state through each step's expected state. Write a
`mode: journey-map` receipt carrying persona, goal, starting state, steps, and the browser evidence
actually available. Record unavailable surfaces explicitly; never claim a platform or
browser behavior that was not observed.

### Error experience

Requires expected error and recovery states on affected steps. Record `mode: error-experience` and
carry each step's expected error and recovery state. Fix reproducible error-handling gaps; park
copy, legal, or product-policy tradeoffs.

### Responsive / cross-browser

Requires browser evidence and responsive targets. Record `mode: responsive-cross-browser` with the
targets declared. Record layout or behavior differences per target; never claim cross-browser
parity when browser evidence is unavailable.

### Accessibility journey

Keyboard, focus, and journey observations supplement — never replace — automated checks. Record
`mode: accessibility-journey`. Route objective scanner violations to accessibility-repair; keep
judgment-dependent surfaces in the gap report for human review. Never certify WCAG compliance from
automation or one journey alone.

```text
- [ ] **Product journey — exercise a named route and fix reproducible gaps.**
  - Never select this entry when work mode is artifact.
  - Discovery: record persona, goal, starting state, steps, expected/error/recovery states,
    responsive targets, keyboard/accessibility observations, and available browser evidence in the
    mode's receipt from `receipts/cycle-specialist-evidence.md` before drafting fixes.
    Write unavailable browser/platform surfaces as explicit rows — never estimate them.
  - Work one reproducible gap cluster per cycle. Fix only gaps the receipt records as reproduced
    and fixable in the repository; park product, legal, or assistive-technology judgments with
    evidence.
  - After each cluster, replay the same route and record the retest in the receipt. Rerun the
    project's configured checks when a fix touches UI code.
  - Review first writes the journey map and gap report only. Direct mode may apply small,
    reversible fixes after the map names them; it never deploys, publishes, or claims certification.
  - Never claim whole-product usability, WCAG, or cross-browser certification from one script or
    unavailable browser evidence.
  - Dedupe against snag-log.md (ALL seen — fixed and rejected).
  - Ends when every reproducible gap is fixed and retested, or every remaining gap is parked with
    evidence and required human review.
  - Verify: the item gate is green at every commit; the scoped route replays end to end in the
    recorded mode, and every remaining gap carries a disposition.
```
