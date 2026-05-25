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
  3. Before fixing, run Patch-Shape Triage and Ripple Signal Triage if the candidate fix touches shared/core/cross-module behavior, contract, source-of-truth, fallback, adapter, duplicate owner, producer+consumer, or consumer-side patching. Also run Pre-Edit Complexity Check when the candidate fix touches an overloaded owner or may worsen source complexity.
  4. Prove: one hypothesis → minimal test → iterate. 3+ failed fixes = question architecture, do not attempt another code fix.
     After fix, if any symptom persists → differential diagnosis (Phase 4 Step 4bis).
  5. Fix: failing test → minimal code at canonical owner → verify → Reflection + architecture review → repair + retirement track
→ Done when: confidence ≥ B, both tracks explicit, DeeperCause answered "no" with evidence, no H-class hard signal still active.

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Symptom fixes are failure.

This skill is the canonical debugging workflow. Use it to move from symptom to
root cause, then to the smallest sufficient stable repair and retirement plan.
Smallest repair means correct owner + bug class fixed + bounded entropy, not the smallest textual diff.

## When to Use

Any technical issue: test failures, bugs, unexpected behavior, performance problems, build/integration failures.

Especially under time pressure, when "just one quick fix" seems obvious, after multiple failed fixes, or when duplicate owners / fallback chains may be involved.

## Quick bug lane

For low-risk, single-owner bugs, keep the report compact: `Symptom`,
`Reproduction`, `Root Cause`, `Fix Boundary`, and `Verification`. Still collect
root-cause evidence before editing. If fallback, duplicate owner, consumer-side
patching, contract risk, shared logic, or cross-module behavior appears,
escalate to the full workflow.

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

   If the tempting fix is "just add a small guard/fallback", also run:

   ```text
   Minimality Check:
   - Smallest textual diff:
   - Correct owner:
   - Bug class fixed:
   - New branch/fallback added:
   - Old path retired or scheduled:
   - Verdict: sufficient repair | local patch | needs first-principles review
   ```

   `local patch` is a mitigation, not a sufficient repair, unless it is the
   canonical owner and includes a retention reason plus retirement trigger.

8. **Pre-Edit Complexity Check**

   After root cause and canonical owner are identified, check whether the fix
   adds complexity to the wrong or overloaded place:

   ```text
   Pre-Edit Complexity Check:
   - Target edit file:
   - Existing pressure signal:
   - Owner fit:
   - Safer edit boundary:
   - Decision: edit-in-place | extract helper | add owner file | split task | pause for plan update
   ```

   Use this for 800+ line files, 80+ line blocks, generic owners,
   fallback/adapter/guard paths, or unclear root-cause ownership. Advisory only:
   if the safer boundary changes the implementation shape, pause and update the
   plan/spec.

### Phase 2: Pattern Analysis

1. **Find working examples** in the same codebase — what works that's similar?
2. **Compare against references** — read completely, don't skim
3. **Identify differences** between working and broken — list every difference
4. **Understand dependencies** — config, environment, assumptions
5. **Locate the canonical owner** — which file/module should own this? Multiple owners = a finding, not normality

### Phase 3: Hypothesis and Testing

1. **Form single hypothesis**: "I think X is the root cause because Y" — be specific
2. **Test minimally**: smallest possible change, one variable at a time. Prefer instrumentation over code edits while still proving the cause.
3. **Verify**: worked? → Phase 4. Didn't? → Form NEW hypothesis. Don't stack fixes.
4. **When you don't know**: say "I don't understand X", don't pretend
5. **Run Reflection** at the end of each loop:
   - **Goal** | **DeeperCause** (yes/no/uncertain) | **Evidence** | **Risk/Unknown** | **Decision** (exit/iterate/escalate)
   - If DeeperCause = uncertain → continue or escalate. Only exit when root cause is deep enough and evidence is sufficient.

### Phase 4: Implementation

**Fix the root cause, not the symptom:**

1. **Create Failing Test Case**
   - Simplest possible reproduction. One-off test script if no framework.
   - MUST have before fixing.

2. **Implement Single Fix**
   - Address the root cause identified. ONE change at a time.
   - No "while I'm here" improvements. No bundled refactoring.
   - Prefer changing the canonical owner instead of stacking more logic into a fallback path.
   - If Patch-Shape Triage, Ripple Signal Triage, or Pre-Edit Complexity Check
     fired, carry its owner, downstream, contract, source-of-truth, fallback,
     retirement, edit-boundary, and verification findings into the fix
     boundary before editing code.

3. **Verify Fix**
   - Test passes now? No other tests broken? Issue actually resolved?
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

   **Compound root cause forms:**
   - True compound — ≥2 independent bugs surfaced together
   - Single-root multi-symptom — 1 root, ≥2 symptom paths → fix root, all resolve
   - Chain causal — A causes B causes C → fix A, B and C auto-resolve

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
   - **H2** — fix touched multiple sites but only 1 covered by failing test
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

See `root-cause-tracing.md`, `defense-in-depth.md`, `condition-based-waiting.md`, `feedback-loop-construction.md` in this directory for deeper guidance on specific diagnostic scenarios.
