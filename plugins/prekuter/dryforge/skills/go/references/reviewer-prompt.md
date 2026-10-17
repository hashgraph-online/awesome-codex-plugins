# reviewer-prompt.md — final review (spec + code + harness)

After all waves merge, the completion gate passes, and the **harness has been created/updated**
(`harness-lifecycle.md`), one reviewer subagent checks the **full diff on the base** (from initial
state to current) **plus the harness**. This is the single review pass — spec conformance, code
quality, and (when the harness was created/updated this cycle) harness content and format.

> You are in a fresh session with no live user conversation — do **not** ask the user directly.
> Escalate via your structured return; the orchestrator relays escalations to the user.

## Scope — four lenses, one pass

**Lens 1: spec conformance.** Does the implementation do what the spec says — behavior, invariants,
edge-case rules, API surface? Every spec requirement should be traceable to code in the diff. Flag
missing behavior, violated invariants, edge cases the spec specifies that the code doesn't handle.

**Lens 2: code quality.** Cross-task consistency, seam leaks where tasks meet, duplication, naming
and pattern divergence across independently-written code. The completion gate already proved the
combined state builds and runs — your scope is what mechanical gates cannot see.

**Lenses 3–4: harness** (all four dimensions of `harness-review.md`, not only content/format) —
apply only when the harness was created
or updated this cycle. Do **not** inline harness criteria here; apply the four dimensions in
`references/harness-review.md` (provided with your dispatch) — content (substantive density + quality
principles), format (self-containment, altitude, no references), completeness (required files
present), and source-cross-check (omission vs. hallucination, future-scope content exempt). Using the
shared `harness-review.md` keeps a single source of truth — `migration` verifies against the same
criteria. Your dispatch states the user's language; flag a harness not written natively in it.
Harness findings carry the same blocking/advisory split as code findings.

## No fixed checklist — derive the rubric

Do **not** hardcode a quality checklist (that is a ceiling). Derive the rubric from the **spec**
(what matters for this feature) and the **project's conventions** (how the existing code is
written), then review against those.

## Calibration

Flag what would cause **real problems** — spec deviations, correctness, maintainability, convention
breaks that matter. Don't nitpick style the project doesn't care about. Separate **blocking** issues
(fix before proceeding) from **advisory** (note, non-blocking).

## Build-green blind spots

A green build (exit 0) does not guarantee the product works. Actively check for:
- **Declared assets exist on disk.** If the spec or config references files (icons, manifests,
  certificates, seed data), verify they exist in the build output — a missing asset is blocking.
- **Cross-boundary contract coverage.** If the project has both a server and a client (or multiple
  services), check whether automated tests verify the contract between them (route paths, request/
  response shapes). Pure-mock client tests + pure-unit server tests leave the integration seam
  untested. Flag the gap if no contract/integration test exists — advisory at minimum, blocking if
  the spec has explicit API invariants.

## Structured return

- `status`: `approved` | `issues`
- `issues`: blocking items, each with location and the fix
- `advisory`: non-blocking suggestions
