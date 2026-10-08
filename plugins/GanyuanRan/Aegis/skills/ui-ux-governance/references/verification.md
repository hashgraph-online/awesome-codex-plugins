# UI/UX Verification

Read only sections selected by `SKILL.md`. Use existing project tools and
verification records. No particular browser product, framework, host API, or
new test harness is required by this reference.

## Select evidence by claim

Map the affected user task and accepted criteria to checks that could expose a
failure. Choose the smallest sufficient set; unrelated screens need no sweep.

| Claim | Relevant evidence | Scope limit |
| --- | --- | --- |
| Interface behavior and recovery | Rendered interaction through the relevant state/API seam | Unit logic alone may not reach the user's observed result |
| Layout/visual consistency | Inspect the actual page with representative content and relevant viewport/theme conditions | One screenshot establishes one captured condition |
| Visual regression | Compare an accepted reference in a controlled rendering environment | An unchanged image does not establish usability; baseline changes need review |
| Keyboard/accessibility behavior | Relevant automated checks plus manual focus, keyboard, and applicable assistive-technology checks | A clean scan covers only automatically detectable issues |
| Responsive behavior | Exercise affected layout and actions at supported narrow/wide conditions | An emulated viewport does not establish every physical-device condition |
| Waiting/performance experience | Task observations and measurements under stated data/network/device conditions | A fast build or optimistic feedback does not establish actual task latency |
| Reduced user effort | Comparable task observations with relevant users and outcome/error/recovery measures | Click count or an agent preference is a hypothesis, not measured usability |

Record what was actually checked: task/page/state, relevant environment and
data, result, evidence reference, and uncovered scope. Use existing acceptance,
review findings, and completion evidence slots; do not create a parallel report.

For changed UI behavior, prefer evidence at the rendered seam reaching the
user, with related regression checks proportionate to risk. For a label-only
edit, a targeted wording/accessible-name/fit check can suffice; do not require
a new end-to-end suite for reversible low-impact wording.

## Compare user effort

Compare alternatives that achieve equivalent accepted outcomes, accessibility,
control, and safeguards. Include correcting errors, cancellation, and recovery.

- Select relevant users and representative tasks; use comparable data and
  conditions. Distinguish first-time/occasional learning from repeat-use speed.
- Observe success, completion time, mistakes, backtracking, repeated input,
  recovery, and help needs where they affect the choice. Use only measures
  useful to this decision; no universal weighted friction score is required.
- A design inspection can expose likely unnecessary burden. State its basis,
  proposed change, preserved constraints, and a concrete acceptance check.
- Label untested effort reduction as expected/provisional. Claim measured
  improvement only when task evidence supports it; do not extrapolate from a
  small convenience sample to every user or from another project's benchmark.

## Missing evidence and delivery

- If browser/device tooling is unavailable, use an available manual or other
  relevant check and record its actual result. Never report proposed manual
  steps as checks already performed.
- If no adequate execution is possible, preserve the implementation and state
  the exact unverified criteria and reproducible next check. Do not build a new
  harness unless its necessity and scope are established by the task owner.
- Passing unit tests/builds supports those scopes. Screenshots support captured
  visual conditions. Neither silently covers interaction recovery, mobile,
  accessibility, or user-effort requirements.
- Deliver the known results and gaps through `verification-before-completion`.
  Work completed, requirements verified, and release readiness are distinct
  claims. Evidence gaps lower confidence; authorized acceptance remains with
  the existing project authority.

## Source references

Read these only when exact tool or evaluation scope matters:

- [W3C accessibility evaluation](https://www.w3.org/WAI/test-evaluate/)
- [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots)
- [Playwright accessibility testing](https://playwright.dev/docs/accessibility-testing)
