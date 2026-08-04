---
name: systematic-debugging
description: "Use when encountering a bug, test failure, or unexpected behavior, before proposing fixes"
---

# Execute

Bug, failure, or unexpected behavior:

1. **Isolate** — read error, reproduce, inspect the diff, and drill upward through diagnostic layers:
   L1 symptom → L2 logic → L3 system → L4 architecture → L5 cross-system
   contract → L6 platform → L7 spec gap. Stop only when causal proof accounts
   for the recurrence generator or reaches a T-class boundary.
2. **Identify owner** — compare working behavior, trace the bad value, locate the
   canonical owner, and treat duplicate owners as a finding.
3. **Decide before editing** — Before fixing, run Patch-Shape Triage and Ripple Signal Triage when shared logic,
   contracts, fallbacks, adapters, producer/consumer seams, or source-of-truth
   boundaries are involved. Surface Change Necessity for any new source-code
   path or non-trivial source edit. Run Minimality Check for a new branch,
   fallback, adapter, owner, or compatibility path, and Pre-Edit Complexity
   Check for an overloaded owner or complexity growth.
4. **Prove** — test one hypothesis with the smallest reproduction or
   verification. A failing test first is required only by an explicit
   `TDD Route: strict`; with `TDD Mode: off`, do not require a failing test or
   RED/GREEN cycle. Three failed fixes means stop and question architecture.
5. **Repair and close** — fix minimally at the canonical owner, verify in
   proportion to risk, review architecture, and close both repair and
   retirement tracks. If any symptom remains, stop and diagnose it separately.

Done: confidence ≥ B, causal status matches recurrence evidence or an external
terminal, tracks explicit, no H signal, and required D evidence passes.

## Core invariant

Find root cause and fix the bug class at its canonical owner. A minimal fix is
not the smallest textual diff; it is the smallest sufficient owner-level repair.

## Quick bug lane

For a low-risk, reproducible, single-owner bug with no patch-shape signal, keep
the readback compact: `Symptom`, `Reproduction`, `Root Cause`, `Change
Necessity`, `Fix Boundary`, and `Verification`. Skip the causal card only when
the causal-proof owner's `Quick Exit Proof` passes.
Quick bug lane must surface Change Necessity before source edits. One sentence
may cover the user-visible need, no-change/non-code option, why code must
change, minimum boundary, and an explicit decision token such as
`Decision: code-change`. If shared logic, a contract, fallback, duplicate
owner, consumer patch, or cross-module behavior appears, leave this lane.

`Aegis Visibility` names the evidence/owner/patch-shape/verification effect.
Pass root cause, avoided misfix, boundary, evidence, complexity, and risk to
`verification-before-completion`; no separate receipt.

## Diagnose before repair

1. Read the complete error/stack and record inputs, environment, versions, and
   success criteria.
2. Reproduce consistently. If reproduction is not stable, read
   `feedback-loop-construction.md` **only when evidence shows intermittent or
   timing-dependent reproduction** and build a bounded automated loop.
3. Inspect recent changes and compare a working example. Code is evidence; if
   authority, glossary, code, and tests disagree, compose
   `establishing-project-context` rather than silently redefining a term.
4. Instrument component boundaries, then trace the bad value toward its source.
   Read `root-cause-tracing.md` **only when the observed bad value is several
   calls or components downstream from its origin**.
5. State one hypothesis and falsify it with one-variable evidence. Do not stack
   speculative fixes. End each loop with `Goal | DeeperCause | Evidence |
   Risk/Unknown | Decision`.

### Canonical-owner and patch-shape gate

Before editing, continue upward unless evidence proves the local site is the
canonical owner when the candidate is any of these signals:

- keyword, phrase, regex, negation-word list, or sample-text exception;
- local guard, extra conditional, `try`/`catch`, early return, or one-off branch;
- fallback, adapter, compatibility branch, prompt branch, or legacy path expansion;
- consumer/caller/readiness/presentation-layer patch;
- downstream logic re-parses raw text or re-infers action/state while typed intent, normalized state, contract, or another source-of-truth exists;
- artifact/download/export/readback/cache patch without producer/owner proof.

```text
PatchShape:
CanonicalOwner:
UpwardDrillSignal:
Decision: fix owner | continue investigation | escalate
```

A locally green test does not erase triage. Before unplanned repair, compare
invariant, owner, patch shape, and topology; a renamed carrier is not a new direction.

If the diagnosis crosses L3, a patch-shape signal fires, a user disputes the
root claim, a prior fix leaves a symptom, compound/root topology is plausible,
or an upstream producer/config/default/contract/spec remains unexcluded, read
`root-cause-claim-contract.md` **before claiming a root cause**. It is the sole
owner of the Pre-Claim Gate, causal-closure/falsifier proof, layer-ceiling
proof, and Causal Topology Gate.

### Change Necessity

This decision is behavior-triggered, not prompt-triggered. It applies to any new source-code path. Before that path or a non-trivial source edit, expose:

```text
Change Necessity:
- User-visible need:
- No-change / non-code option:
- Why code change is necessary:
- Minimum change boundary:
- Decision: no-change | docs/config-only | code-change | needs-clarification
```

`no-change` blocks source edits; `docs/config-only` narrows them;
`needs-clarification` pauses; `code-change` carries the minimum boundary into
repair and verification.

### Minimality and owner fit

For any proposed branch, fallback, adapter, compatibility path, or new owner:

```text
Minimality Check:
- Existing owner / reuse path:
- Correct owner and bug class:
- New path and existence proof:
- Old path retired or scheduled:
- Verdict: sufficient repair | local patch | needs first-principles review
```

A `local patch` needs a retention reason and retirement trigger. For a new
non-ordinary repair surface, run the `Existence Check` in
`docs/current/AEGIS_MINIMALITY_REFERENCE.md`. If retirement involves old code,
external compatibility, or persistent-state risk, compose
`anti-entropy-governance`; it chooses the retirement path but never grants
destructive authority.

Before editing an overloaded or mixed-purpose owner:

```text
Pre-Edit Complexity Check:
- Target edit file:
- Existing pressure signal:
- Owner fit and safer boundary:
- Decision: edit-in-place | extract helper | add owner file | split task | pause for plan update

Pre-Edit Owner-Fit Decision:
- Edit intent: wiring-only | move-out / extract-first | local-fix-without-new-responsibility | new-responsibility | emergency / compatibility patch
- Owner fit and safer boundary:
- Decision: edit-in-place | extract helper | add owner file | split task | pause for plan update
```

Use `using-aegis/references/complexity-governance.md` for pressure signals.
Do not add `new-responsibility` in place by default. If the safer boundary
changes the approved shape, update the plan/spec first.

## Repair and proportional verification

Implement one owner fix; no bundled “while here” work. Under strict TDD, create
the smallest failing test first. With TDD off, a reproduction is diagnostic
evidence, not a RED gate or a prerequisite for production edits.

Verification must match the risk:

- local single-owner repair: original reproduction plus focused regression;
- shared/contract/cross-module repair: canonical owner plus affected consumers
  and compatibility boundary;
- fallback/owner retirement: main-path, lingering-reference, negative, and
  boundary checks;
- timing/concurrency repair: read `condition-based-waiting.md` **only when
  evidence identifies polling, sleeps, or race timing as part of the cause**;
- invalid state crossing several trusted boundaries: read
  `defense-in-depth.md` **only after the root repair is known and evidence shows
  a second independent validation boundary is required**.

Read `advanced-debugging-governance.md` **before another fix** for failed/
persistent / divergent repair or three failures; for unclear/disputed stop /
Layer Stop Card / intervention; or plausible compound root. Closeout triggers:
repair-added patch-shape; multi-site/one-regression;
remaining pattern/anomaly/duplicate/wrong-owner/downstream repair;
uninspected same-symptom fix; open recurrence/unsupported root status;
missing compound topology-specific member/anti-disguise proof;
outside-repo authority; unmigrated
published-contract break; undefined spec; missing permission/info. They route H/T/D;
detail is not causal proof.

For non-trivial debugging with configured workspace support:

```bash
python <aegis-workspace-helper> init --root <target-project-root>
python <aegis-workspace-helper> new-work --root <target-project-root> ...
python <aegis-workspace-helper> add-evidence --root <target-project-root> --work <YYYY-MM-DD-slug> ...
python <aegis-workspace-helper> check --root <target-project-root>
```

Fast bug fix or quick bug fix pressure does not skip this: if Ripple Signal
Triage fires, record it before editing and verify the canonical owner plus
affected downstream path. Records are advisory, not completion authority.

## Closure

Always report:

- **Repair** — cause, owner, smallest change, compatibility, verification.
- **Retirement** — old path status, retention reason/trigger, removal check.

Confirm the reproduction, same-pattern handling, authority, complexity, and
retirement. Confidence: A = direct regression evidence; B = strong evidence
with bounded unknowns; C = partial and not resolved.

`Trace Digest` may summarize audit evidence; never expose chain-of-thought or
replace root-cause, rule-effect, and verification evidence.
