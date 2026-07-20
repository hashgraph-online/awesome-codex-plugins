---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Execute

→ Bug? Test failure? Unexpected behavior? → **Find root cause first. No fixes without evidence.**
  1. Isolate: read error → reproduce → check git diff → drill upward through diagnostic layers:
     L1 symptom → L2 logic → L3 system → L4 architecture →
     L5 cross-system contract → L6 platform constraint → L7 spec gap.
     Stop when no deeper "why" remains OR terminal unactionable (T1-T4).
  2. Identify owner: compare with working code → locate canonical owner → flag duplicate owners as a finding
  3. Before fixing, run Patch-Shape Triage and Ripple Signal Triage if the candidate fix touches shared/core/cross-module behavior, contract, source-of-truth, fallback, adapter, duplicate owner, producer+consumer, or consumer-side patching. Surface Change Necessity for any new source-code path and non-trivial fixes. Run Minimality Check when the candidate fix adds a new branch, fallback, owner, adapter, or compatibility path. Also run Pre-Edit Complexity Check when the candidate fix touches an overloaded owner or may worsen source complexity.
  4. Prove: one hypothesis → smallest reproduction or verification → iterate. A failing test first is required only under explicit `TDD Route: strict`. 3+ failed fixes = question architecture, do not attempt another code fix.
     After fix, if any symptom persists → differential diagnosis (Phase 4 Step 4bis).
   5. Fix: minimal code at canonical owner → targeted verification → Reflection + architecture review → repair + retirement track
      If the user asks for white-box auditability, include `Trace Digest` after
      evidence is collected; do not expose raw chain-of-thought or let trace
      replace root-cause, rule-effect, and verification evidence.
→ Done when: confidence ≥ B, both tracks explicit, DeeperCause answered "no" with evidence, no H-class hard signal still active.

# Systematic Debugging

## Overview

Find root cause. Fix the bug class at its canonical owner; close repair and
retirement. This is not the smallest textual diff.

## When to Use

Any technical issue: test failures, bugs, unexpected behavior, performance problems, build/integration failures.

Especially under time pressure, when "just one quick fix" seems obvious, after multiple failed fixes, or when duplicate owners / fallback chains may be involved.

## Quick bug lane

For low-risk, single-owner bugs, keep the report compact: `Symptom`,
`Reproduction`, `Root Cause`, `Aegis Visibility`, `Change Necessity`, `Fix Boundary`, and
`Verification`. Quick bug lane must surface Change Necessity before source edits and before any new source-code path. Still collect root-cause evidence before editing; one compact sentence is enough when it names the user-visible
need, no-change / non-code option, why code change is necessary, minimum change
boundary, and an explicit decision token such as `Decision: code-change`;
minimum-boundary wording is not a substitute for the decision. If fallback,
duplicate owner, consumer-side patching, contract risk, shared logic, or
cross-module behavior appears, escalate to the full workflow.

`Aegis Visibility` for this workflow names how root-cause evidence,
canonical-owner selection, patch-shape triage, or verification discipline
changed the repair path. Use a natural stage transition when moving from
diagnosis to repair and from repair to verification.

This debugging report is a diagnosis/repair surface, not a separate completion
receipt. Before claiming the bug is fixed, pass root cause, avoided misfix,
fix boundary, verification, complexity, and residual risk to
`verification-before-completion` so the user-facing closeout uses the unified
Aegis impact/safety receipt.

## The Four Phases

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings — they often contain the exact solution
   - Read stack traces completely; note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably? What are the exact steps? Does it happen every time?
   - If not reproducible → consult `feedback-loop-construction.md` to build an automated reproduction loop; don't guess
   - Record baseline: inputs, environment, version, logs, success/failure criteria

3. **Check Recent Changes**
   - What changed that could cause this? Git diff, recent commits, new dependencies, config changes, environmental differences

   Non-trivial bugs passively use relevant active `CONTEXT.md` terms. If
   authority/glossary/code/tests differ, code is evidence; compose
   `establishing-project-context` rather than silently rewrite meaning.

4. **Gather Evidence in Multi-Component Systems**
   - Instrument each component boundary: log what enters and exits
   - Run once to see where data breaks, then focus investigation there

5. **Trace Data Flow** (when error is deep in call stack)
   - Where does bad value originate? What called this with bad value?
   - Keep tracing up until you find the source. Fix at source, not at symptom.
   - For the complete backward tracing technique, see `root-cause-tracing.md`.

6. **Drill Upward Through Diagnostic Layers**

   Start at L1. Exhaust all "why" questions at each layer before moving upward.
   The chain is open-ended — architecture is not the endpoint.

   ```
   L1 Symptom:     what failed? where? exact reproduction?
   L2 Logic:       which branch, invariant, or state transition is wrong?
   L3 System:      which component boundary, dependency, or ownership seam?
   L4 Architecture: what design choice, duplicated owner, or fallback chain?
   L5 Cross-system: which API / SLA / timing contract between systems?
   L6 Platform:    what runtime / OS / framework constraint?
   L7 Spec gap:    who never defined correct behavior for this case?
   ```

   Hard signal definitions (H/T/D) are in the Quality Gate — apply them there,
   not during initial investigation.

   When the stop layer is not obvious, the user asks where the diagnosis
   stops, the issue crosses component/system boundaries, or a user-provided
   fact falsifies the current layer, expose a compact `Layer Stop Card` before
   fixing:

   ```text
   Layer Stop Card:
   - Current Stop Layer: L1 Symptom | L2 Logic | L3 System | L4 Architecture | L5 Cross-system Contract | L6 Platform | L7 Spec Gap | T-class boundary
   - Checked Path:
   - Evidence For Stop:
   - Excluded Layers:
   - Falsifier:
   - User Intervention Point:
   - Next Action:
   ```

   The card is an advisory readback of the diagnostic stop point. It is not a
   `GateDecision`, `PolicySnapshot`, or completion authority.

7. **Patch-Shape Triage Before Editing**

   Treat the first obvious fix as evidence, not clearance to edit. If the
   candidate fix shape matches any item below, continue upward before changing
   code unless you can prove the local layer is the canonical owner:

   - keyword, phrase, regex, negation-word list, or sample-text exception
   - local guard, extra conditional, `try`/`catch`, early return, or one-off branch
   - fallback, adapter, compatibility branch, prompt branch, or legacy path expansion
   - consumer/caller/readiness/presentation-layer patch
   - downstream re-parsing of raw text when typed intent, normalized state,
     contract, or another source-of-truth already exists
   - artifact/download/export/readback/cache patch that does not first locate
     the producer and source-of-truth owner
   - duplicate parsing, duplicate owner, or "keep both for now" reasoning
   - fix that only names the observed sample instead of the bug class

   Required output before editing when this gate fires:

   ```text
   PatchShape:
   CanonicalOwner:
   UpwardDrillSignal:
   Decision: fix owner | continue investigation | escalate
   ```

   After this gate fires, a locally green test does not erase it. Existing
   checkpoint prose retains `PatchShape`, `CanonicalOwner`,
   `UpwardDrillSignal`, `Decision`, outcome, and one bounded evidence ref.
   Before an unplanned repair, compare invariant, owner seam, patch shape, and
   topology; a renamed carrier is not a new direction.

   If the tempting fix is "just add a small guard/fallback", also run:

   ```text
   Minimality Check:
   - Smallest textual diff:
   - Existing owner / reuse path:
   - Correct owner:
   - Bug class fixed:
   - New branch/fallback added:
   - Existence proof for new path:
   - Old path retired or scheduled:
   - Verdict: sufficient repair | local patch | needs first-principles review
   ```

   `local patch` is a mitigation, not a sufficient repair, unless it is the
   canonical owner and includes a retention reason plus retirement trigger.
   For candidate additions that are not ordinary repair code, run an
   `Existence Check` using `docs/current/AEGIS_MINIMALITY_REFERENCE.md` before
   editing. This is behavior-triggered: if the candidate repair adds a fallback,
   adapter, branch, or new owner, the check runs even when the user asked for
   that fallback directly.

   ```text
   Existence Check:
   - Proposed new surface:
   - Existing owner / reuse candidate:
   - Why existing surface is insufficient:
   - Creation proof:
   - Entropy / retirement impact:
   - Decision: reuse-existing | add-with-proof | defer | reject | needs-first-principles-review
   ```

   If the repair or retirement boundary depends on deleting old paths,
   retaining compat for a proven external dependency, or stopping on
   persistent-state risk, compose `anti-entropy-governance` before editing. It
   decides the path; it does not grant destructive authority.

8. **Change Necessity**

   After root cause and canonical owner are identified, but before repair code,
   make the code-change decision visible. This is the "should code change at
   all?" check; it is not a new artifact and does not belong in the
   `using-aegis` hot path.

   This is behavior-triggered, not prompt-triggered. If the next step adds any
   new source-code path or makes a non-trivial source edit, expose a natural
   readback even when the user did not ask for it. A tiny helper, small guard,
   new branch, fallback, adapter, or owner is not exempt. Example: "Code
   necessity check: a non-code path is insufficient because <reason>; the
   minimum change boundary is <canonical owner/files>, so the decision is
   code-change."

   ```text
   Change Necessity:
   - User-visible need:
   - No-change / non-code option:
   - Why code change is necessary:
   - Minimum change boundary:
   - Decision: no-change | docs/config-only | code-change | needs-clarification
   ```

   In quick bug lane, keep `Decision:` explicit even when using natural prose.

   If the decision is `no-change`, do not edit source code. If the decision is
   `docs/config-only`, narrow the fix to that surface and verify it. If the
   decision is `needs-clarification`, pause before repair. If the decision is
   `code-change`, carry the minimum boundary into `Fix Boundary`,
   `Minimality Check`, and verification.

9. **Pre-Edit Complexity Check**

   After root cause and canonical owner are identified, check whether the fix
   adds complexity to the wrong or overloaded place:

   Use `using-aegis/references/complexity-governance.md` for shared pressure
   signals and the meaning of `over-budget`.

   ```text
   Pre-Edit Complexity Check:
   - Target edit file:
   - Existing pressure signal:
   - Owner fit:
   - Safer edit boundary:
   - Decision: edit-in-place | extract helper | add owner file | split task | pause for plan update

   Pre-Edit Owner-Fit Decision:
   - Edit intent: wiring-only | move-out / extract-first | local-fix-without-new-responsibility | new-responsibility | emergency / compatibility patch
   - Owner fit:
   - Safer edit boundary:
   - Decision: edit-in-place | extract helper | add owner file | split task | pause for plan update
   ```

   If the safer boundary changes the implementation shape, pause and update the
   plan/spec.

   If the likely repair would grow an already oversized maintained artifact and
   the slice cannot govern that growth immediately, do not present the repair as
   a completed fix boundary. Escalate with a plan update or a visible follow-up
   requirement.

   When the target edit file is over-budget or mixed-purpose, classify edit
   intent before source edits. `new-responsibility` must not be added in place
   by default. `wiring-only`, `move-out / extract-first`, and
   `local-fix-without-new-responsibility` may proceed only when they do not add
   a new responsibility and the verification boundary is clear. `emergency /
   compatibility patch` requires residual risk and a retirement trigger.

### Phase 2: Pattern Analysis

1. **Find working examples** in the same codebase — what works that's similar?
2. **Compare against references** — read completely, don't skim
3. **Identify differences** between working and broken — list every difference
4. **Understand dependencies** — config, environment, assumptions
5. **Locate the canonical owner** — which file/module should own this? Multiple owners = a finding, not normality

### Phase 3: Hypothesis and Testing

1. **Form single hypothesis**: "I think X is the root cause because Y" — be specific
2. **Prove minimally**: use the smallest reproduction or verification, one
   variable at a time. Prefer instrumentation over code edits while still
   proving the cause. A failing reproduction may be useful evidence, but it is
   not a RED gate or a prerequisite for production edits unless an explicit
   `TDD Route: strict` says so.
3. **Verify**: worked? → Phase 4. Didn't? → Form NEW hypothesis. Don't stack fixes.
4. **When you don't know**: say "I don't understand X", don't pretend
5. **Run Reflection** at the end of each loop:
   - **Goal** | **DeeperCause** (yes/no/uncertain) | **Evidence** | **Risk/Unknown** | **Decision** (exit/iterate/escalate)
   - If DeeperCause = uncertain → continue or escalate. Only exit when root cause is deep enough and evidence is sufficient.

### Phase 3.5: Pre-Claim Gate

Before claiming a root cause and entering Phase 4, check whether the
Pre-Claim Gate applies. It applies whenever any Patch-Shape Triage signal is
active (candidate fix is a guard, fallback, consumer/caller patch,
artifact/cache patch, or sample-only naming — i.e. H1 / H3 / H8 / H10 / H11 /
H13), or whenever the diagnosis crosses a component or system boundary, or a
previous fix left a residual symptom.

When it applies, do not state a root cause or edit code until the five
mechanical checks below pass. See `root-cause-claim-contract.md` for the full
rationale, the six-topology table, and a worked example.

1. **Causal Closure** — every causal edge from symptom to claimed root has an
   evidence anchor (file:line, test, log, reproduction). One "probably" edge
   leaves the chain open.
2. **Falsifier Checked** — state "if X were not the root cause, observable F
   would appear," and confirm F was checked and absent.
3. **Adversarial Self-Refutation** — generate the strongest single argument
   that this root cause is wrong, and show why it does not hold.
4. **Causal Topology Gate** — classify the topology explicitly; do not default
   to single-root. Topology and the anti-disguise check are in Phase 4 Step
   4bis and in `root-cause-claim-contract.md`.
5. **Layer Ceiling Proof** — if the claim stops at L?, show why L?+1 is
   unreachable by concrete constraint, not by omission.

Required output before entering Phase 4 when the gate fires:

```text
Pre-Claim Gate Pass:
Topology: single-root | single-root-multi-symptom | chain | independent-compound | conjunctive-cluster | disjunctive-or
CausalClosure: closed | open-edge: <edge>
Falsifier: <if not-X then F; F checked: yes/no>
SelfRefutation: <strongest objection> -> <why it does not hold>
LayerCeiling: <L?> -> <why L?+1 unreachable>
Verdict: pass | fail-<which-gate>
```

This gate is advisory method-pack discipline. It is not a `GateDecision`,
`PolicySnapshot`, evidence sufficiency authority, or completion authority. It
turns a self-judged stop ("I think this is deep enough") into a checkable,
falsifiable claim ("here is the evidence chain, the falsifier I checked, the
objection I survived, and the ceiling I reached"). The quick bug lane is
exempt when no Patch-Shape signal fires and the bug is single-owner at the
canonical owner.

### Phase 4: Implementation

**Fix the root cause, not the symptom:**

1. **Choose Reproduction and Verification**
   - Under explicit `TDD Route: strict`, create the smallest failing test before production code.
   - With `TDD Mode: off` and no strict route, do not require a failing test
     first or RED / GREEN. A pre-change failing reproduction is permitted when
     it helps diagnosis, but label it as evidence rather than a production-edit
     gate; keep the smallest reproducible regression proof and targeted
     verification that fit the fix.

2. **Implement Single Fix**
   - Address the root cause identified. ONE change at a time.
   - No "while I'm here" improvements. No bundled refactoring.
   - Prefer changing the canonical owner instead of stacking more logic into a fallback path.
   - If Change Necessity, Patch-Shape Triage, Ripple Signal Triage, or
     Pre-Edit Complexity Check fired, carry its owner, downstream, contract,
     source-of-truth, fallback, retirement, edit-boundary, minimum-boundary, and
     verification findings into the fix boundary before editing code.

3. **Verify Fix**
   - Does the selected verification pass? No other relevant tests broken? Issue actually resolved?
   - Verify the intended compatibility boundary still holds.
   - Verify you did not silently move authority to the wrong layer.

4. **If Fix Doesn't Work**
   - STOP. Count: How many fixes have you tried?
   - If < 3: Return to Phase 1, re-analyze with new information.
   - **If ≥ 3: STOP and question the architecture (step 6 below)**. DON'T attempt Fix #4 without architectural discussion.

4bis. **Post-Fix Differential Diagnosis**

   After applying a fix, if ANY symptom persists:

   **STOP. Do NOT attempt another fix without diagnosis.**

   1. Isolate the residual symptom precisely — what exactly remains?
   2. Trace its causal chain independently (fresh Phase 1 run).
   3. Compare with the causal chain of the fixed symptom:

   | Residual pattern | Diagnosis | Action |
   | --- | --- | --- |
   | Same reproduction conditions as fixed symptom | Fix is incomplete | Continue upward drilling from same source |
   | Different reproduction conditions, chains converge to same source | Fix was at wrong depth | Drill upward again from the shared source |
   | Different reproduction conditions, chains diverge | Compound root cause (≥2 independent roots) | Each root needs its own fix |
   | Same symptom, reduced but not eliminated | Fix was a downstream patch | Drill upward again from source |

   4. If uncertain whether convergent or divergent: **escalate. Do not guess.**

   **Compound root cause forms (legacy shorthand):**
   - True compound — ≥2 independent bugs surfaced together
   - Single-root multi-symptom — 1 root, ≥2 symptom paths → fix root, all resolve
   - Chain causal — A causes B causes C → fix A, B and C auto-resolve

   **Causal Topology Gate (full form, used by the Pre-Claim Gate):** the three
   legacy forms above are a shorthand. Before claiming any root — single or
   compound — classify the topology explicitly. The default is `unknown`; you
   must actively exclude the multi-root topologies before collapsing to a
   single-root claim. See `root-cause-claim-contract.md` for the full table,
   member necessity/sufficiency tests, and the anti-disguise check.

   | Topology | Structure | Stop condition | Repair shape |
   | --- | --- | --- | --- |
   | `single-root` | A → symptom | Layer Ceiling Proof at A | fix A |
   | `single-root-multi-symptom` | A → B, C, D | Layer Ceiling Proof at A | fix A; symptoms self-resolve |
   | `chain` | A → B → C → symptom | Layer Ceiling Proof at A | drill to A, fix A |
   | `independent-compound` | A → symptom, Y → symptom, A ⊥ Y | each root passes Gate 1/2/5; no shared upstream | fix A **and** Y; missing one leaves symptom |
   | `conjunctive-cluster` | A ∧ B ∧ C → symptom (each necessary, none sufficient) | enumerate members, necessity test each, sufficiency test the set, anti-disguise check | fix **all** members; missing one leaves symptom |
   | `disjunctive-or` | A ∨ B → symptom (any one suffices) | enumerate all disjuncts | fix one to stop symptom; enumerate rest for defense-in-depth |

   **Member proof (cluster / compound):** each claimed member must pass a
   necessity test ("if this member alone were removed, would the symptom still
   occur?" — if yes, it is not a member). The set must pass a sufficiency test
   (together the members explain every observed manifestation). Necessity
   tests here are conceptual proofs, not empirical runs — a method-pack
   ceiling; state this honestly when the cluster has many members.

   **Anti-disguise check (most often skipped):** before accepting
   `conjunctive-cluster`, ask whether members X and Y share a deeper common
   cause Z, such that X and Y are merely two manifestations of Z. If yes, the
   topology collapses to `single-root-multi-symptom` or `chain` rooted at Z —
   drill to Z. The reverse check protects `independent-compound`: if two
   divergent chains share upstream Z, they are not independent and Z is the
   root.

5. **If 3+ Fixes Failed: Question Architecture**

   **Pattern indicating architectural problem:**
   - Each fix reveals new shared state/coupling/problem in different place
   - Fixes require "massive refactoring" to implement
   - Each fix creates new symptoms elsewhere

   **STOP and question fundamentals.** Discuss with your human partner before attempting more fixes.
   This is NOT a failed hypothesis — this is a wrong architecture.

6. **Deliver Dual-Track Closure**

   For bug fixes, refactors, contract changes, or governance cleanup, always produce:

   **Repair track** — root cause, canonical owner, smallest necessary change, compatibility boundary, verification method.

   **Retirement track** — old owner / fallback / patch, whether it is still active on the main path, the only reason to keep it (if any), trigger for deletion, verification needed before removal.

   Never add a new owner, fallback, prompt branch, or adapter path without stating what happens to the old one.

## Quality Gate

Before you claim debugging is complete:

0. **Workspace record for non-trivial debugging** — if this is medium+ complexity
   or it writes `docs/aegis/` records, initialize/check through configured
   Aegis workspace support when available:

   ```bash
   python <aegis-workspace-helper> init --root <target-project-root>
   python <aegis-workspace-helper> new-work --root <target-project-root> ...
   python <aegis-workspace-helper> add-evidence --root <target-project-root> --work <YYYY-MM-DD-slug> ...
   python <aegis-workspace-helper> check --root <target-project-root>
   ```

   Fast bug fix or quick bug fix pressure does not skip this: if Ripple Signal
   Triage fires, do the triage before editing and expand verification to the
   canonical owner plus affected downstream path.

   These records are method-pack evidence trails only. They do not grant
   authoritative completion.

1. **Stop-when review** — re-read the diagnostic layer where you stopped. Did you reach "no deeper why remains" or a T-class terminal boundary? If the chain ended at L1-L2 and the evidence is conclusive, that is a valid endpoint. If there are still unexplained "why" questions, continue upward drilling before claiming done.
   - Use a `Layer Stop Card` when the stop point affects the fix boundary,
     contract owner, spec/product decision, or user correction path. Keep
     simple fast-path explanations cheap; do not emit the card for ordinary
     factual Q&A about the skill itself.
2. **Hard signal check** — apply these countable facts, not judgments:

   Must continue upward drilling (H-class — ANY hit = NOT done):
   - **H1** — fix added a conditional branch (`if` / `switch` / `catch` / `try`)
   - **H2** — fix touched multiple sites but only 1 covered by the selected regression proof
   - **H3** — fix is at consumer/caller, not canonical owner
   - **H4** — same bug pattern exists elsewhere in repo (grep for it)
   - **H5** — original reproduction still produces any anomaly
   - **H6** — `git log --grep` shows this symptom was "fixed" before → Read that commit's diff. Understand why it failed. Do not repeat the same patch pattern.
   - **H7** — candidate fix adds keyword, phrase, regex, negation-word list, or sample-text exception
   - **H8** — candidate fix adds a local guard, one-off branch, early return, fallback, adapter, compatibility branch, prompt branch, or legacy path expansion
   - **H9** — candidate fix patches a consumer/caller/readiness/presentation layer while an upstream owner could own correctness
   - **H10** — downstream logic re-parses raw text or re-infers action/state while typed intent, normalized state, contract, or another source-of-truth exists
   - **H11** — candidate fix patches artifact/download/export/readback/cache symptoms without proving the producer and source-of-truth owner
   - **H12** — candidate fix keeps duplicate owners active, moves authority silently, or says "keep both for now" without a retirement trigger
   - **H13** — candidate fix names only the observed sample wording/input instead of proving the bug class
   - **H14** — topology is `conjunctive-cluster` or `independent-compound` but the member set is not enumerated, or a member was not necessity-tested
   - **H15** — topology was declared `conjunctive-cluster` or `independent-compound` without running the anti-disguise check (a shared upstream Z may collapse the cluster/compound to a single root)

   Terminal unactionable (T-class — any hit = stop drilling, switch to mitigation):
   - **T1** — required change is outside this repo's boundary
   - **T2** — would break published API contract with no migration path
   - **T3** — root is undefined spec behavior (nobody defined correctness)
   - **T4** — required permission or information is unavailable
   → On T-class: record root cause + system boundary + architecture review: what boundary vulnerability did this expose? can the system be made more resilient to this class of external failure?

   Depth sufficient (D-class — ALL must pass before claiming done):
   - **D0** — fix eliminated ≥1 code path (paths after ≤ paths before)
   - **D1** — fix eliminated ≥1 conditional branch (not added a fallback)
   - **D2** — fix is at canonical owner
   - **D3** — original reproduction steps no longer trigger any anomaly
   - **D4** — no same-pattern occurrences remain unaddressed in repo
   - **D5** — Minimality Check verdict is `sufficient repair`, or the local
     patch is explicitly bounded with retention reason and retirement trigger
   - **D6** — Causal topology is explicitly classified (not defaulted to
     single-root); if `conjunctive-cluster` or `independent-compound`, every
     member is enumerated and necessity-tested, and the set is sufficiency-tested
   - **D7** — anti-disguise check has been run for any `conjunctive-cluster`
     or `independent-compound` classification (a shared upstream Z was sought)

3. **Reflection** — re-run Goal / DeeperCause / Evidence / Risk/Unknown / Decision
4. **Confirm** the fix addressed the source, not just the sample
5. **Retirement surface** — did it shrink, stay, or grow?
6. **Confidence**:
   - `A` = direct evidence and regression coverage support the root-cause conclusion
   - `B` = strong evidence, limited coverage or some bounded unknowns remain
   - `C` = partial evidence only; do not present as fully resolved

If confidence is not at least `B`, do not speak as if the issue is fully closed.

## Red Flags - STOP and Follow Process

If you catch yourself thinking:

- "Quick fix for now, investigate later"
- "Let me just try changing X and see if it works" (ignoring evidence, error messages, or hard signals)
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "I don't fully understand but this might work"
- Diagnosing by intuition — "It's probably X", listing fixes without investigation, proposing solutions before tracing data flow
- "One more fix attempt" (when already tried 2+)
- "Let's just add another fallback" instead of finding root cause
- "We can keep both owners for now" without a retirement condition
- Accepting a partial fix without differential diagnosis

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (see Phase 4 Step 5)
**If symptoms persist after fix:** Run differential diagnosis (see Phase 4 Step 4bis)

## Human Partner Signals

If you hear "Is that not happening?", "Will it show us...?", "Stop guessing", "Ultrathink this" → STOP. Return to Phase 1.

## When Process Reveals "No Root Cause"

If investigation reveals the issue is truly environmental, timing-dependent, or external:
document what you investigated, implement appropriate handling (retry, timeout, error message),
add monitoring.

## Supporting Techniques

See `root-cause-tracing.md`, `defense-in-depth.md`, `condition-based-waiting.md`, `feedback-loop-construction.md`, and `root-cause-claim-contract.md` in this directory for deeper guidance on specific diagnostic scenarios.
