# Expanded Closeout Detail

This advisory reference grants no authoritative `GateDecision`, `PolicySnapshot`, evidence sufficiency, or completion authority.

Read this file only when a trigger in `SKILL.md` applies. It supplies detail to
the one `Aegis Impact and Safety Receipt`; no card here is a second final owner.
Add only triggered cards and keep untriggered ceremony out.

## Readiness Summary

For release, merge, publish, handoff, or "ready?" requests, organize fresh
evidence for tests, documentation, version, supported-host compatibility,
uncovered scope, and residual risk. Readiness does not authorize commit, tag,
publish, merge, or release; report missing authority or evidence explicitly.

## Trace Digest

Use only for an explicit audit/debug/release/long-task review or user request.
Summarize the bounded execution and evidence chain, retrieval chain, static
rules and effects, triggered/skipped relevant skills, command/verification
trace, stability/value signals, host capabilities, unavailable fields,
redaction, and confidence. Label claims `measured`, `observed`, `inferred`,
`declared`, or `unknown`. Never expose raw chain-of-thought.

## Goal Closure

When goal framing or a durable task boundary shaped work, match the claim to
the highest proven boundary. For expanded/audited closure show:

```text
Goal Closure:
- Goal status: done | blocked | needs-verification | scope-exceeded
- Success evidence:
- Stop state:
- Non-goals respected:
```

Whole-task, current-task, and slice evidence are distinct; a lower boundary
cannot silently satisfy a higher one.

## Context Impact

Use only when project/domain semantics changed or were acceptance evidence.
Name affected context/terms, evidence grade, fact-versus-decision authority,
and action. For `unchanged`, verify no context write occurred. Compose
`establishing-project-context` for an unresolved semantic delta.

## Workspace Integrity

Use only after the main-file helper hot path when the target project's
configured Aegis workspace was created or changed. Report the work record,
bundle/check results, target root, and structural-only boundary. A successful
structure check does not prove evidence quality, semantic correctness, or
completion.

## Baseline and ADR Closure

For product/requirement or durable architecture work, use
`docs/current/AEGIS_PROCESS_BASELINE.md` §3.0e and §16. Record:

```text
Baseline Alignment:
- Product / Requirement Baseline:
- Architecture / Runtime Boundary Baseline:
- Result: aligned | Design Defect | Implementation Drift | missing-authority | needs-clarification
- scope: requirements | architecture | both
```

`Architecture Alignment` is the architecture-scoped compatibility alias, not a
second default card.

For completed medium/high durable architecture work, run `ADR Backfill Check`
against `docs/current/AEGIS_ADR_AUTO_BACKFILL.md`. If the action is create,
amend, supersede, or baseline sync is needed/unknown, use
`recording-architecture-decisions` before the final claim.

## Governance and Retirement Closure

For governance, cleanup, migration, compatibility, namespace cutover, public release, deprecation, policy boundary, or retirement work, keep this dual track
visible even when implementation was small:

```text
Governance Closure:
- Repair Track:
- Retirement Track:
- Residual Risk:
```

When work adds, replaces, retains, or removes old logic, also record the old
owner/path found, deleted or retained status, retention reason, retirement trigger,
and lingering-reference check. A retained internal owner means bounded
mitigation/debt, not clean retirement.

Use `anti-entropy-governance` to choose delete-first, a proven external
compatibility exception, or confirmation-first. Its decision surface feeds the
receipt; it does not become another completion report.

## Destructive-Action Cards

For code retirement, record:

```text
Anti-Entropy Declaration:
- Deletion Class:
- Old Path/Object:
- New Canonical Owner:
- Expected Preserved Behavior:
- Expected Retired Behavior:
- External Boundary Touched: no | yes
- Source-of-Truth Data Risk: none | possible | confirmed
- User Confirmation Required: no | yes
```

If the target is persistent state or another irreversible source-of-truth
object, use confirmation-first and stop at:

```text
Data Destruction Guard:
- Target Class:
- Exact Target(s):
- Environment:
- Why Irreversible:
- Backup / Rollback Note:
- Allowed Read-Only Next Steps:
- Blocked Destructive Steps:
- Confirmation Required: yes
- Status: awaiting scoped confirmation
```

Broad assent such as "OK", "continue", or "sounds good" is not scoped confirmation.
If scope changes, request fresh confirmation. Until then, only read-only analysis
is allowed and the closeout status remains incomplete.

## Expanded Complexity Detail

When complexity pressure is material, state `Complexity Delta`, `Complexity Closure`,
`Completion-Time Complexity Repair Decision`, `Complexity Governance Suggestion`,
or `Major Complexity Alert` as applicable. Maintained test source
is not a cheap tests-only exception. Pair new fallback/adapter/compatibility
logic with the retirement evidence above.
