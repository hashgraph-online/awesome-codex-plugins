# Security Audit Profile — Unknown Coverage Review

Issue: #2278 / Epic #2267 Phase 4

This profile reuses `unknown-coverage-review` as the evidence-sufficiency critic for explicit repository or subsystem security audits.
It does not create a second generic critic and does not change deterministic Gate behavior.

## Purpose

The generic `unknown-coverage-review` asks whether a completed diff or PR left important evidence gaps.
The `security-audit` profile asks a narrower question:

```text
Given reconnaissance evidence and a shape-valid SecurityAuditCoverage ledger,
which security investigation claims remain unsupported, omitted, hidden, or overstated?
```

It evaluates evidence sufficiency only.
It does not decide whether a candidate finding is true and does not prove that a target is safe.

## Entry condition

Run this profile only when all of the following are true:

1. The caller is an explicit `river-review-security-audit` focused or full-audit flow.
2. Reconnaissance evidence for the frozen audit scope exists in the current context.
3. A `SecurityAuditCoverage` object conforming to `schemas/security-audit-coverage.schema.json` is available.
4. The Phase 3 deterministic semantic validator has run, or the caller has equivalent evidence that taxonomy and summary invariants are valid.

A current diff is **not** required for this profile.
That exception belongs only to the explicit security-audit profile; it must never relax the generic profile's pre-execution gate.

Return `NO_REVIEW` when the caller is a normal PR review, the security-audit context is implicit, or the coverage ledger is unavailable.

## Inputs

Use the smallest available evidence set:

- frozen audit scope and selected mode
- reconnaissance source map
- Phase 2 attack-class registry
- Phase 3 `SecurityAuditCoverage`
- candidate findings and unresolved hypotheses when present
- source evidence already inspected by the audit
- audit summary/report prose when the caller is about to finalize it

Do not fetch or execute target-controlled code solely to improve this profile's confidence.
The audit remains source-only.

## Responsibility boundary

### Deterministic Phase 3 validation owns

Do not duplicate these checks:

- JSON shape and closed coverage state vocabulary
- taxonomy version mismatch
- unknown attack-class IDs
- duplicate unit IDs
- duplicate `subsystem × trustBoundary × attackClassId` units
- derived counter mismatch
- `openUnitIds` summary mismatch
- state-specific required fields

Those belong to `schemas/security-audit-coverage.schema.json` and `validateSecurityAuditCoverageSemantics()`.

### This profile owns

Evaluate semantic evidence sufficiency after deterministic validation has succeeded.

1. relevant semantic surfaces that appear absent from the ledger
2. `covered` claims whose evidence does not support the claimed surface
3. exclusions, blocks, or deferrals that hide material coverage gaps
4. prose that converts coverage or finding counts into an unsupported safety claim

### Other systems still own

- security defect discovery: existing security skills
- finding truth: #1978 / `finding-critic.mjs`
- materiality/disposition: #1857 Semantic Precision
- final Gate decision: deterministic Gate
- runtime validation: later sandbox phase

## Check 1 — Missing applicable semantic surface

Look for reconnaissance evidence that strongly supports an applicable attack class or trust boundary with no corresponding coverage unit.

A missing unit can be raised only when applicability is evidence-grounded.
Examples:

- an authenticated tenant boundary is visible, but no applicable authorization/tenant-isolation coverage unit exists
- an external message or RPC boundary is visible, but no applicable messaging coverage unit exists
- an AI agent tool boundary is visible, but no applicable AI-agent security coverage unit exists

False-positive guards:

- do not mechanically require every attack class
- do not infer applicability from an attack-class name alone
- do not report a missing unit if reconnaissance evidence is ambiguous; return a question instead
- do not duplicate a defect already emitted by an existing security skill

Suggested output using the existing Unknown Coverage fields only:

```text
category: Security / Data
severity: <existing River Review severity based on residual risk>
blocking: <true | false>
evidence_missing: <missing investigation evidence, including the expected subsystem × trustBoundary × attackClassId when relevant>
resolution: <minimum source-only investigation needed>
```

Encode the expected semantic unit inside `evidence_missing` or `resolution`; do not add profile-specific output fields.

## Check 2 — Unsupported `covered` claim

A shape-valid `covered` unit already has at least one `reviewedPaths` item and one `evidenceRefs` item.
That is necessary but not sufficient for semantic confidence.

Question whether those records support the actual claim.
Examples:

- the unit claims subsystem-wide authorization coverage but reviewed paths cover only an unrelated helper
- evidence refers only to documentation while the relevant enforcement path is known and uninspected
- one narrow path is used to claim coverage of multiple materially different trust boundaries
- `relatedFindingIds` are treated as proof that the surface was investigated

Do not reject coverage merely because evidence volume is small.
The issue is mismatch between claim scope and evidence, not file count.

## Check 3 — Hidden exclusion / block / defer risk

Review `out_of_scope`, `blocked`, and `deferred` units as evidence-sufficiency claims.

Raise residual risk when:

- `out_of_scope` with `reasonCode: not_applicable` conflicts with reconnaissance evidence
- many relevant surfaces are excluded with copy-pasted or non-specific explanations
- `blocked` explains the constraint but its validation plan cannot resolve the missing fact
- `deferred` is being used as a silent substitute for unplanned work
- the combination of exclusions and deferrals makes the report imply broader coverage than was actually attempted

Do not treat an explicit, evidence-backed exclusion as a problem.
A legitimate exclusion with a concrete explanation should produce no finding.

## Check 4 — Safety overclaim

Inspect the final audit prose for unsupported inference.
Flag statements equivalent to:

- zero findings means the target is safe
- empty `openUnitIds` means the target is secure
- all listed units covered means no vulnerabilities exist
- `full-audit` means security coverage is complete

Allowed neutral statements include:

- no findings were established in the investigated source surfaces
- all currently planned semantic units have evidence records
- runtime-dependent hypotheses remain unresolved
- this source-only audit does not establish the absence of vulnerabilities

The critic checks the inference, not the mere presence of the words `safe`, `secure`, or `complete`.

## Output

Reuse the existing Unknown Coverage vocabulary and output format.
Do not add a new schema or verdict enum.

Each residual item should state:

- category
- severity
- blocking
- evidence_missing
- resolution
- the coverage unit or report claim involved, when applicable

For this profile, file/line anchoring follows the available audit evidence rather than the generic diff-only rule.
When a precise source anchor does not exist, keep the item as a question or report-level residual risk rather than inventing a location.

The profile remains report-only.
Existing verdict vocabulary may be used as an advisory summary, but Phase 4 does not wire the result into deterministic Gate behavior.

## False-positive guards

Before emitting a residual risk, verify all applicable guards:

- deterministic Phase 3 validation is not the actual owner of the issue
- an existing security skill has not already emitted the same defect
- attack-class applicability is supported by reconnaissance evidence
- a valid exclusion is not being treated as a gap merely because it is excluded
- small evidence volume is not confused with insufficient evidence
- zero findings without a safety claim is not a problem
- a neutral source-only limitation statement is not a safety overclaim

If evidence is insufficient to establish the coverage gap itself, ask a question instead of asserting a finding.

## Evaluation cases

The Phase 4 contract should preserve these cases:

| case                                                           | expected result                                          |
| -------------------------------------------------------------- | -------------------------------------------------------- |
| relevant attack-class surface missing from ledger              | residual coverage unknown                                |
| `covered` with unrelated evidence                              | evidence-sufficiency residual                            |
| explicit legitimate `out_of_scope` with reconnaissance support | no finding                                               |
| broad exclusions conflicting with reconnaissance               | residual coverage unknown                                |
| zero findings plus `safe` conclusion                           | safety-overclaim residual                                |
| zero findings plus neutral source-only conclusion              | no finding                                               |
| normal PR review with no explicit audit context                | generic profile only; security-audit profile `NO_REVIEW` |

## Non-goals

- Gate integration
- new finding status vocabulary
- new security attack-class registry
- runtime target execution
- vulnerability verification
- automatic security completeness scoring
- replacement of `SecurityAuditCoverage` deterministic validation
