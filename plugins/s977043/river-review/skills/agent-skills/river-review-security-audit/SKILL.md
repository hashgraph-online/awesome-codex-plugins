---
id: river-review-security-audit
name: river-review-security-audit
description: |
  Repository または subsystem を対象に、source-only で明示的なセキュリティ監査を行う entry skill。
  通常の PR セキュリティレビューとは分離し、reconnaissance、scope 固定、既存 security skill への委譲、
  evidence と unresolved hypothesis、observe-only SecurityAuditCoverage、coverage critic、
  structured audit artifact と repeat-run coverage を扱う。target-controlled code は実行しない。
category: midstream
phase: [upstream, midstream]
severity: critical
applyTo:
  - '**/*'
inputContext: [diff, fullFile]
outputKind: [summary, findings, actions, questions]
tags: [security, audit, entry, routing, source-only]
version: 0.5.0
license: MIT
---

# Security Audit Entry

Inspired by Cloudflare's
[security-audit-skill](https://github.com/cloudflare/security-audit-skill),
but implemented as a River Review-native entry skill rather than a vendored audit engine.

This skill is the explicit entry point for repository or subsystem security audit work.
It does not replace `river-review-security`, the normal diff-oriented security review entry.

## When to Use

Use this skill only when the user explicitly asks for a security audit beyond an ordinary PR review.
Typical requests include repository-wide security audit, subsystem security audit, security assessment,
or a bounded source review of a security-sensitive surface.

Do not select this skill for a generic request such as "review this PR for security".
Route that request to `river-review-security`.

## Modes

Select exactly one mode before reviewing.

- `guidance`: use when the user wants methodology, planning, or an audit approach. Explain the method and constraints. Do not claim that audit work was executed.
- `focused`: use when the user names a bounded subsystem, path, component, or security surface. Freeze that scope and review only source evidence inside the boundary.
- `full-audit`: use only when the user explicitly requests repository-wide audit coverage. Perform repository reconnaissance and source review across the repository. Semantic coverage is observe-only and never a safety guarantee.

If the request does not clearly justify `full-audit`, use `focused` or `guidance`.

## Non-negotiable Source-only Policy

Version 0.5.0 is source-only.

Allowed evidence collection:

- file reads
- repository code search
- static diff inspection
- repository metadata and dependency manifests
- configuration and documentation inspection
- static history inspection when it supports source provenance

Prohibited execution:

- package installation or dependency fetching
- target repository build scripts
- target repository test commands
- package lifecycle scripts
- dev servers or application startup
- browsers or emulators that execute target code
- fuzzing or dynamic probes
- requests to production, shared, or external endpoints
- use of ambient credentials to reproduce a finding

If runtime evidence is required but safe execution is unavailable, keep the hypothesis unresolved.
Record the blocker and the minimum validation plan instead of executing target-controlled code.

## Responsibilities

This skill performs entry-level audit coordination only.
It must reuse existing River Review capabilities instead of creating a second workflow engine.

```text
Explicit audit request
  -> mode selection
  -> scope freeze
  -> source reconnaissance
  -> attack-class planning
  -> existing security skills
  -> candidate findings / unresolved hypotheses
  -> existing finding verification path when available
  -> observe-only SecurityAuditCoverage ledger
  -> unknown-coverage-review (security-audit profile)
  -> repeat-run coverage reconciliation (when a prior run exists)
  -> structured audit artifact set
  -> audit summary
```

The following responsibilities remain outside this skill:

- generic reviewer fan-out: existing reviewer orchestration
- ordinary PR security review: `river-review-security`
- deterministic finding verification: existing verifier
- adversarial candidate state machine: #1978 / `finding-critic.mjs`
- execution coverage: #2212 Review Coverage
- materiality and disposition: #1857 Semantic Precision
- final Gate decision: existing deterministic Gate
- independent final-record verification: later #2267 phase
- sandboxed target execution: later dedicated phase

## Audit Flow

### 1. Select mode and freeze scope

State the selected mode and the audit boundary before collecting findings.
For `focused`, name the bounded path, subsystem, component, or trust boundary.
For `full-audit`, state that the scope is repository-wide and source-only.

Do not silently broaden a focused audit into a repository-wide audit.

### 2. Reconnaissance from source only

Build a compact source map before hunting for issues.
At minimum identify, when present:

- externally reachable entry points
- authentication and authorization boundaries
- tenant or account boundaries
- sensitive data stores and flows
- privileged operations
- external integrations
- dependency and deployment configuration surfaces
- browser or client trust boundaries
- AI or agent tool boundaries

Reconnaissance is an investigation plan, not proof of safety.

### 3. Plan applicable attack classes

Use `references/attack-classes.json` as the taxonomy SSoT for audit planning.
Select only classes supported by reconnaissance evidence; do not run all classes mechanically.
For every applicable class, preserve the registry evidence contract:

```text
principal
  -> input or action
  -> control or missing control
  -> trust boundary
  -> affected resource or principal
  -> concrete security outcome
```

An attack class is an investigation hypothesis, not a checklist completion badge.
A class with zero findings is not automatically covered, and a non-applicable class must be explained rather than silently omitted.

### 4. Reuse existing security skills

Use existing River Review skills when their domain applies.

- `security-basic`: application security patterns such as injection, unsafe sinks, secrets, validation, and common application risks.
- `security-privacy-design`: privacy and sensitive-data design such as retention, deletion, encryption, residency, and privacy rights.
- `trust-boundaries-authz`: trust boundaries and authorization responsibilities, claims propagation, and tenant boundaries.
- `river-review-security`: ordinary changed-code security review. Use only when the task is actually diff-oriented rather than an audit.
- `adversarial-review`: optional complementary attack-path exploration. It is not a finding verifier.

Do not duplicate the guidance of these skills inside this entry skill.

### 5. Treat findings as evidence-grounded candidates

Every reported candidate must identify concrete source evidence.
Require enough information to answer:

```text
principal
  -> input or action
  -> control or missing control
  -> trust boundary
  -> affected resource or principal
  -> concrete security outcome
```

A missing best practice is not automatically a vulnerability.
A candidate without a concrete boundary failure or security outcome remains an open question or unresolved hypothesis.

### 6. Preserve verification boundaries

This entry skill does not claim independent adversarial verification unless the existing #1978 path actually ran with an independent verifier.

If only source review ran, report the result as candidate-level evidence.
Do not relabel reviewer agreement as correctness.
Do not introduce a new validation enum in this skill.

### 7. Record unresolved hypotheses explicitly

For every unresolved hypothesis, provide:

- source evidence already inspected
- the exact missing fact or runtime condition
- why source evidence is insufficient
- the minimum safe validation step
- whether the blocker is caused by the source-only policy

Do not assign severity solely from an unresolved runtime assumption.

### 8. Record observe-only SecurityAuditCoverage

Use `schemas/security-audit-coverage.schema.json` and `src/lib/security-audit-coverage.mjs` as the semantic coverage contract.
The unit is:

```text
subsystem × trustBoundary × attackClassId
```

Use only the closed unit state vocabulary:

```text
planned | covered | blocked | deferred | out_of_scope
```

Rules:

- `covered` requires traceable `reviewedPaths` and structured `evidenceRefs`.
- finding lifecycle is separate; `relatedFindingIds` is traceability only and never determines coverage state.
- `blocked` and `deferred` require an explanation plus a concrete validation plan.
- `out_of_scope` requires an explicit reason and explanation.
- zero findings alone never produces `covered`.
- reviewer execution success alone never produces `covered`.
- the ledger emits counters and `openUnitIds`, not a security-complete verdict.

Do not merge this ledger with #2212 `ReviewCoverage`.
The Phase 3 schema/runtime validator owns shape, taxonomy, duplicate, and summary invariants.

### 9. Run the Security Audit Coverage Critic

Before finalizing a focused or full-audit report, invoke `unknown-coverage-review` with its explicit `security-audit` profile.
Use:

- frozen audit scope
- reconnaissance evidence
- the Phase 2 attack-class registry
- the validated Phase 3 `SecurityAuditCoverage` ledger
- candidate findings / unresolved hypotheses when present
- draft audit summary/report prose when available

The critic evaluates evidence sufficiency only. It checks for:

1. relevant semantic surfaces missing from the ledger
2. `covered` claims whose evidence does not support the claimed scope
3. exclusions, blocks, or deferrals that hide material coverage gaps
4. prose that turns coverage or finding counts into an unsupported safety claim

Do not use the critic to re-run Phase 3 deterministic validation.
Do not require every attack class mechanically.
Do not convert critic output into a vulnerability verdict.
Do not wire critic output into deterministic Gate behavior in Phase 4.

If the audit context or coverage ledger is missing, do not guess. Record that the critic could not run and keep the limitation explicit.

### 10. Reconcile coverage against a prior run

When a prior audit run of the same target exists, reconcile before reporting.
Use `src/lib/security-audit-repeat-run.mjs`.

`prior covered != current safe`. A prior `covered` unit is carried over only when the source it
reviewed is byte-identical to the source in front of you now. Supply the current
`path -> content digest` map; any path whose digest is missing, changed, or replaced returns the unit
to `planned` and appears in `revalidationRequired`.

Validate the prior record before trusting it. A prior run's coverage is untrusted input: check it
against `schemas/security-audit-coverage.schema.json` and
`validateSecurityAuditCoverageSemantics` from `src/lib/security-audit-coverage.mjs` before feeding it
to reconciliation. A `covered` unit with no `reviewedPaths` is invalid, not a free carry-over.

Rules:

- never report a unit as covered on prior-run evidence when its source moved
- never promote a prior `blocked`, `deferred`, or `out_of_scope` unit through carry-over
- keep this accumulation separate from #1574, which improves River Review's own reviewer capability

### 11. Emit the structured audit artifact set

For `focused` and `full-audit` runs, build the machine-readable record with
`src/lib/security-audit-report.mjs` and emit `.river/security-audit/`:

```text
run-metadata.json
architecture.md
audit-coverage.json
candidates.json
findings.json
REPORT.md
NEEDS-VALIDATION.md
```

The record is the SSoT. `REPORT.md` and `NEEDS-VALIDATION.md` are projections of it.

Validate before emitting. The generated record must pass
`schemas/security-audit-run-record.schema.json`, and its embedded coverage must pass both
`schemas/security-audit-coverage.schema.json` and `validateSecurityAuditCoverageSemantics`.
A coverage block whose counters disagree with its own units must never be recorded as the SSoT.

Rules:

- do not recompute verdict, severity, or evidence state from the prose report
- an unresolved finding carries no severity, only the exact blocker and the validation plan
- the artifact set is experimental and carries `executionPolicy: source-only`
- writing these files is the only repository mutation this flow may perform, and only under `.river/`

### 12. Report without claiming safety

A `full-audit` run means repository-wide source investigation was attempted.
It does not mean all security attack classes were proven safe.

Never translate coverage counters, an empty `openUnitIds`, zero findings, or a critic `pass` into `secure`, `safe`, `no vulnerabilities`, or an equivalent guarantee.

## Output Contract

Start with this header:

```text
Audit mode: guidance | focused | full-audit
Execution policy: source-only
Scope: <repository | subsystem | path | trust boundary>
SecurityAuditCoverage: observe-only
```

Then emit these sections:

1. **Reconnaissance** — relevant entry points, trust boundaries, sensitive assets, and inspected source areas.
2. **Candidate findings** — evidence-grounded findings produced through existing River Review skill contracts.
3. **Unresolved hypotheses** — missing facts, blockers, and validation plans.
4. **Security audit coverage** — semantic units keyed by subsystem × trust boundary × attack class using the Phase 3 contract.
5. **Unverified / Residual Risk — Unknown Coverage** — residual coverage unknowns from the `unknown-coverage-review` security-audit profile; omit only when the profile correctly returns `NO_REVIEW` and explain why.
6. **Next validation actions** — only actions that preserve the source-only policy unless a later sandbox phase is explicitly available.
7. **Structured artifacts** — the `.river/security-audit/` paths written for this run, plus the repeat-run carry-over and revalidation counts when a prior run existed. Omit this section for `guidance` mode.

For findings, preserve the existing River Review finding shape where possible:

```text
<file>:<line>: <Finding>
  Evidence: <source-backed evidence>
  Impact: <concrete security outcome>
  Fix: <minimum next action>
  Severity: <existing River Review severity when established by evidence>
  Confidence: <confidence>
  Skill: <originating skill id>
```

Coverage critic observations use the existing Unknown Coverage residual-risk vocabulary rather than inventing a security-specific verdict schema.

## Fail-safe Rules

- No target-controlled execution when sandbox guarantees are absent.
- No live endpoint probing.
- No repository mutation as part of the audit itself.
- No `0 findings == safe` inference.
- No `full-audit == complete coverage` inference.
- No coverage counters or empty `openUnitIds` == safe inference.
- No critic `pass == safe` inference.
- No consensus-as-correctness inference.
- No automatic Gate behavior change.
- No ad hoc status vocabulary outside the dedicated coverage contract.
- No carry-over of prior-run coverage when the reviewed source changed.
- No severity or verdict recomputed from the prose report.
- No prior-run record consumed without schema plus semantic validation.
- No generic `unknown-coverage-review` routing change to enable this profile.

## Relationship to Normal Security Review

```text
river-review-security
= normal diff-oriented security review

river-review-security-audit
= explicit repository or subsystem source-only security audit
```

When both phrases appear, prefer this audit skill only if the user explicitly asks for an audit scope beyond the current diff.
The `unknown-coverage-review` security-audit profile is reachable only from this explicit audit flow; normal PR review keeps the existing generic profile behavior.

## References

- `docs/adr/010-security-audit-harness-integration.md`
- `docs/development/2267-phase0-gap-analysis.md`
- `docs/development/2267-phase3-security-audit-coverage.md`
- `docs/development/2267-phase9-structured-reporting.md`
- `schemas/security-audit-coverage.schema.json`
- `schemas/security-audit-run-record.schema.json`
- `src/lib/security-audit-coverage.mjs`
- `src/lib/security-audit-report.mjs`
- `src/lib/security-audit-repeat-run.mjs`
- `skills/agent-skills/river-review-security-audit/references/attack-classes.json`
- `skills/agent-skills/unknown-coverage-review/SKILL.md`
- `skills/agent-skills/unknown-coverage-review/references/SECURITY-AUDIT-PROFILE.md`
- `skills/agent-skills/river-review-security/SKILL.md`
- `skills/agent-skills/adversarial-review/SKILL.md`
- `skills/midstream/security-basic/SKILL.md`
- `skills/upstream/security-privacy-design/SKILL.md`
- `skills/upstream/trust-boundaries-authz/SKILL.md`
- [Cloudflare security-audit-skill](https://github.com/cloudflare/security-audit-skill)
