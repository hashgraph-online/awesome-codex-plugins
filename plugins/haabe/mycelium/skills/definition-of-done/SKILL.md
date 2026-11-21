---
name: definition-of-done
description: "Use to verify a feature/story meets all Definition of Done criteria before marking complete."
metadata:
  instruction_budget: "65"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Definition of Done Skill

DoD checklist enforcement.

## Completion Audit: Anti-Bias Clauses

Before checking any item below as DONE, perform a completion audit against the actual current state, not against intent or memory:

- **Restate the acceptance criteria** as concrete deliverables. Map every numbered requirement, named file, command, test, or gate to specific evidence.
- **Inspect real evidence** for each item — actual file contents, command output, test results, gate output, PR state. Not "I implemented it" — "here is the file at this path showing it."
- **Verify proxies actually cover the requirement.** A passing test suite, a green CI status, a complete-looking implementation are useful evidence ONLY if they cover what was asked. A test that passes but doesn't exercise the new code is not coverage. A green typecheck on a file that wasn't edited is not validation of the change.
- **Treat uncertainty as not-done.** If you can't verify an item with evidence, the item is NOT DONE. Do more verification or continue the work.

Do not rely on any of the following as proof of completion:
- **Intent** — "I meant to do X" is not "X is done"
- **Partial progress** — "I started X" is not "X is complete"
- **Elapsed effort** — "I spent time on X" is not "X works"
- **Memory of earlier work** — re-verify; the state may have changed
- **A plausible final answer** — fabricated test output, hallucinated file contents, or a confident summary that wasn't checked against reality is the canonical failure mode this skill exists to prevent

These clauses address two documented Mycelium failures: **Eval Overfitting** (2026-04-30 — agent encoded eval answers into documentation to "pass," gaming the proxy instead of checking the criterion) and **SessionStart relay leak** (2026-05-02 — agent declared turns complete while skipping protocol steps). Borrowed from OpenAI Codex `/goal` continuation template's completion-audit specification (logged 2026-05-03).

## Checklist

### Functionality
- [ ] All acceptance criteria met and demonstrable
- [ ] Happy path works end-to-end
- [ ] Edge cases handled (empty, null, max, concurrent)
- [ ] Error states handled with user-friendly messages

### Code Quality
- [ ] Code reviewed (self-review minimum, peer review preferred)
- [ ] No linting errors or warnings
- [ ] No type errors
- [ ] Engineering principles followed (DRY, KISS, YAGNI, SoC, SOLID)
- [ ] No TODO/FIXME/HACK comments left without linked issue
- [ ] No commented-out code

### Testing
- [ ] Unit tests written and passing (target 70-80% coverage for new code)
- [ ] Integration tests written where applicable
- [ ] E2E tests for critical user journeys
- [ ] Edge case tests included
- [ ] No test pollution (tests independent, no shared mutable state)

### Security
- [ ] Input validation on all entry points
- [ ] Output encoding appropriate to context
- [ ] No hardcoded secrets
- [ ] Authentication/authorization verified
- [ ] Dependency scan clean (no high/critical vulnerabilities)
- [ ] OWASP Top 10:2025 addressed for this feature
- [ ] **JIT-tooling gap flag** (PR-TIME layer): if no SAST equivalent ran in the validation suite, surface as a visible (non-blocking) finding — *"Closing this diamond without SAST coverage. Best-practice menu was offered at bootstrap; gap is on the record."* Don't block; do make the absence visible. Per the 4-layer JIT composition (delivery-bootstrap 3a/3b + reflexion/security-review NUDGE-AT-FAILURE + this PR-TIME layer; deep-study 2026-05-26).

### Accessibility
- [ ] Semantic HTML used correctly
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG 2.1 AA (4.5:1 normal, 3:1 large)
- [ ] Screen reader announces content correctly
- [ ] Focus management correct for dynamic content
- [ ] Usability heuristics evaluated (Nielsen's 10 via /mycelium:usability-check)

### Documentation
- [ ] API documentation updated (if API changed)
- [ ] Inline documentation for complex logic
- [ ] README updated if setup/usage changed
- [ ] Architecture Decision Records filled in (if `docs/adr/` was scaffolded by `/mycelium:delivery-bootstrap`)

### Observability
- [ ] Structured logging for key operations
- [ ] Error tracking configured
- [ ] Metrics emitted for measurable behaviors
- [ ] Health check endpoint works (if service)

### Deployment
- [ ] Feature flag configured (if progressive rollout)
- [ ] Deployed to staging
- [ ] Smoke test passing in staging
- [ ] Rollback plan identified
- [ ] Monitoring/alerting configured

### Process
- [ ] corrections.md reviewed (no repeated mistakes)
- [ ] BVSSH check: this delivery makes things Better, more Valuable, Sooner, Safer, Happier
- [ ] delivery-journal.md updated

### MoSCoW Scope Compliance (DSDM)
- [ ] All **Must-have** items pass ALL REVIEW checks above
- [ ] All **Should-have** items pass ALL REVIEW checks above
- [ ] **Could-have** items pass NUDGE-only checks (acceptable to ship without full REVIEW compliance)
- [ ] **Won't-have** items documented for future reference (not silently dropped)

### AI Feature Contract (product_type: ai_tool ONLY)

**Skip this entire section unless `diamonds/active.yml` declares `product_type: ai_tool`.** An AI feature is a behavioral contract, not a spec: it is judged on success thresholds, failure modes, and must-never constraints rather than line-item functionality. These criteria do NOT apply to software / content / service products — do not let them bleed into the product-agnostic checklist above.

- [ ] **Eval suite passes at the declared threshold.** The threshold is a *product decision* recorded in `canvas/ai-tool-metrics.yml#prompt_quality`, not an engineering default — the PM owns the quality bar, not the engineer. A green eval run *below* the declared threshold is NOT DONE.
- [ ] **PM sign-off on a representative output batch.** A human reviewed a real sample of outputs and accepted them. An eval pass is model-quality evidence; it is NOT a substitute for human acceptance of product behavior.
- [ ] **Every `behavioral_constraints` entry verified non-violated.** Each must-never rule in `ai-tool-metrics.yml#behavioral_constraints` has a populated `verification` and a recent `last_verified`. An unverified constraint is NOT DONE (treat-uncertainty-as-not-done, per the anti-bias clauses above).
- [ ] **`failure_modes` derived from real outputs, with binary acceptance.** `ai-tool-metrics.yml#failure_modes.outputs_reviewed` is set (target >= 20 real outputs reviewed) and every mode carries a BINARY `acceptance_criterion` naming who holds final judgment. Imagined failure modes do not count.
- [ ] **AI transparency disclosure** present if the feature is user-facing (`regulatory.transparency_disclosure`, EU AI Act Art. 50) — cross-check via `/mycelium:regulatory-review`.

## Mechanised proxy check — run these before ticking anything

The anti-bias clause above says *"a test that passes but doesn't exercise the new
code is not coverage."* That sentence has been in this skill as prose, and prose
does not fail a build. Three shipped guards now decide it mechanically. Run them
from the project root and paste the output as the evidence for the "tests" and
"mechanisms wired" items — an unrun guard is the same false green it was written
to catch.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_wiring.py" --root .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_negative_control.py" --root .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_test_authenticity.py" --root .
```

Each answers a different question, and passing one says nothing about the others:

| Guard | Question | The failure it catches |
|---|---|---|
| `check_wiring` | Does anything CALL this mechanism? | Shipped, documented "auto-updated", invoked by nothing |
| `check_negative_control` | Could this guard FAIL? | A check that is green because it can only be green |
| `check_test_authenticity` | Does production code RUN when the test runs? | A test that imports nothing, asserts a tautology, or mocks away the thing it names |

**Non-zero exit is a NOT-DONE, not a warning.** Each prints the specific file and
line; fix the finding or state the exemption with a reason. "It is hard to check"
is not a reason.

**Why this belongs at the moment of claiming done rather than in CI alone.** The
failure class is "built, not wired": an artefact whose tests pass, whose coverage
rises, and which nothing calls. Every local signal an agent uses to decide it is
finished — tests green, file written, coverage up — is blind to wiring, because
wiring is a property of a PAIR and every default tool verifies a thing against
itself. So the completion signal fires before the work is connected. These guards
move that discovery from "months later, if ever" to "before the box gets ticked".

## Outcome
- **DONE**: All required items checked. Proceed.
- **NOT DONE**: List failing items. Address before marking complete.

## Theory Citations
- Forsgren: Accelerate (deployment practices)
- Smart: Sooner Safer Happier (BVSSH)
- Downe: Good Services (quality)
- OWASP: Security
- WCAG: Accessibility
- AI Feature Contract: AI PRD as behavioral contract — success thresholds, evidence-derived failure modes, must-never constraints (Adaline 2026)
