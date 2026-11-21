# Build delivery and system records

Read this for an authorized new surface, system build, significant restyle or
build handoff. It holds the detailed contract and reporting templates so a
read-only review need not load them. Reviews use `interface-review.md`; audit
artifacts stay outside application files. No template expands the authorized
scope or replaces the iterative render/recapture checks in the entry point.

## Delivery contract

Before a new surface, a significant redesign, a component family, or a system
pass, lock:

```text
Objective (user-visible outcome):
Surface (repo, route, live URL, branch):
Audience and primary action:
Register:
Reference or visual target:
Done signal (screenshot, build, test, deploy readback):
Constraints (WIP to keep, routes not to touch, unapproved claims):
Spacing, grid, breakpoints:
Color roles, states, contrast, dark and light behavior:
Type roles, hierarchy limits, measure, truncation:
Interface vocabulary (buttons, empty, loading, error, success):
Assets, logo use, motion rules:
Acceptance checks (desktop, mobile, accessibility, render evidence):
```

For a narrow fix, compress to target, route, primary action, and done signal.
Work is done when the done signal has been checked, or the remaining gap is
named.

## System audit

For an authorized system build, produce at the smallest useful fidelity
(during an audit, report these in evidence without editing application files): a token map (color roles, type scale, spacing, radii,
shadows, motion, z-layers, semantic states) in `DESIGN.md` or
`design-tokens.json`; a state matrix (default, hover, focus, active, disabled,
loading, empty, success, warning, error, permission-denied); an interface
vocabulary; a screenshot contract with seeded demo data; an accessibility pass
(contrast, focus order, touch targets, keyboard paths, reduced motion); and
migration notes.

Raise a system issue when a token, component, spacing pattern, or state repeats
three or more times or controls a high-visibility surface. Name the drift cause:
token missing, token ignored, component gap, content pressure, platform
convention, or legacy debt.

```text
Color consistency: /10      Typography hierarchy: /10
Spacing rhythm: /10         Component consistency: /10
Responsive behavior: /10    Dark/light behavior: /10
Motion restraint: /10       Accessibility: /10
Information density: /10    Polish: /10
Total: /100
```

These optional scores summarize observed evidence, not objective certification.
Do not infer severity from an arbitrary score. Rank demonstrated user impact;
uninspected dimensions are not scored. Fix only the authorized scope.

## Ship gate

For launch pages, app shells, public marketing surfaces, store assets, or
high-visibility dashboards, end with:

```text
Surface:
Mode:
Done signal:
Evidence (screenshots, commands):
Copy gate (suede-copy score if new copy shipped):
Search gate (H1, direct answer, metadata, crawlable text):
Design system gate (score or drift notes):
Visual QA gate (passed | blocked):
Blockers:
Accepted caveats:
Next action:
Status: ship | ship-with-caveats | hold
```

Recommend `hold` when a core path is broken, claims are false, screenshots do
not match the build, an accessibility issue blocks the primary action, or the
live route cannot be verified. `ship-with-caveats` needs every P0 resolved and
each caveat named and non-critical. Name all relevant unresolved critical
findings; offer options only when a concrete user decision is needed. Missing
render evidence remains unverified, not an automatic product defect.

For restyles, add: reference URL, target URL, target source, fidelity, depth,
unmatched reference signals, and legal or brand caveats.

## Output

Findings lead, rationale follows. Name the file and line. For builds, state
what changed and show render evidence. Do not narrate internal steps
(preflight, mode routing) to the user, and do not praise the existing design
in place of findings. After meaningful work, add a one-paragraph plain
explanation, then:

```text
Changed:
Design QA:
Screenshots or render notes:
Design-system drift:
P0/P1/P2 blockers:
Verification:
Caveats:
Status: ship | ship-with-caveats | hold
```
