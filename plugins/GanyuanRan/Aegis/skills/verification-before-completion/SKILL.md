---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, passing, verified, release-ready, or ready to commit, merge, publish, or hand off.
---

# Execute

→ About to claim "done", "passing", "fixed", "complete"? → **Run the verification command first. Then claim.**
  1. Identify: what command proves the claim?
  2. Run: full command, fresh, complete
  3. Read: output, exit code, failures
  4. Verify: output confirms claim? → state claim WITH evidence. Doesn't? → state actual status.
→ Done when: exact command run, output confirms, residual risk stated, confidence graded.
  Non-trivial code changes → also report Complexity Delta and Complexity Governance Suggestion.
  Governance/retirement work → also close Repair Track + Retirement Track + Residual Risk.

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency. Evidence before claims, always.

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## When To Apply

Before ANY success/completion claim, expression of satisfaction, commit, PR, task completion, or delegation. Applies to exact phrases, paraphrases, and implications.

## QA Closure

Before any success claim, include the required evidence semantic slots. Natural
prose, localized headings, or compact cards are all valid when the slots remain
explicit and auditable.

```text
Required evidence slots, one allowed card rendering:
- Evidence action / check performed:
- Result / exit status:
- Covered scope:
- Uncovered scope:
- Residual risk:
- Confidence grade: A | B | C
```

Semantic Slots:
- Required governance fields may appear as localized headings, natural prose, or
  compact cards when they remain explicit and auditable.
- Natural Surface is valid when natural user-facing wording preserves the
  semantic slots; natural expression is not a reason to drop evidence,
  uncovered scope, residual risk, confidence, retirement, baseline, or
  architecture fields.
- In short: natural expression is valid only when it preserves semantic slots.
- Governance Receipt is the compact closeout form for Aegis-shaped non-trivial
  work. It names the boundary held, evidence, covered and uncovered scope,
  residual risk, confidence, and any triggered governance closure.

TDD Completion Boundary:
- A passing GREEN cycle proves local behavior only.
- Final completion must compare any available `Slice Card`, `TaskIntentDraft`,
  and parent plan/spec acceptance against the claim being made.
- If only the slice goal is satisfied, do not claim whole-task `done`; state
  covered and uncovered scope and downgrade to `needs-verification` unless the
  parent acceptance is also satisfied.

1. **Remove/Restore**: side effects? temp instrumentation restored?
2. **Evidence Bundle**: exact command, scope, exit status, key output. State what's covered and what's not. Include target test and related regression evidence. When automation is blocked, provide reproducible manual verification steps.
3. **Prompt Hygiene**: when external output shaped judgment → state whether summaries or raw excerpts were used. Name large payloads not loaded. If summary insufficient → read back excerpt or lower claim. Include Evidence Used / Not Loaded / Next Evidence boundary when relevant.
4. **Confidence**: A (direct + regression, no unknowns) | B (direct, bounded risk) | C (partial only, not closed)
5. **Authority**: verified evidence ≠ authoritative completion. Keep distinct.
6. **Goal Closure**: when `goal-framing` or optional `TaskIntentDraft` goal
   fields shaped the work, explicitly check the goal before claiming completion:

   Evidence precedence for completion judgment:
   1. `Slice Card` Goal / Verification / Stop for the current slice, when present
   2. `TaskIntentDraft` Goal / Success evidence / Non-goals, when present
   3. Parent plan/spec acceptance, when present

   ```text
   Goal Closure:
   - Goal status: satisfied | blocked | needs-verification | scope-exceeded
   - Success evidence:
   - Stop state: done | blocked | needs-verification | scope-exceeded
   - Non-goals respected:
   ```

   Use `done` only when success evidence is satisfied. Use `blocked` when a
   dependency, permission, or required fact is missing. Use `needs-verification`
   when implementation exists but evidence is insufficient. Use
   `scope-exceeded` when continuing would exceed the goal or non-goals.
7. **Long-Task**: re-read checkpoint, confirm every todo has status, no drift check unresolved.
8. **Workspace Integrity**: if the task created or modified a target project's
   `docs/aegis/` workspace and configured Aegis workspace support is available,
   run
   `python <aegis-workspace-helper> bundle --root <target-project-root> --work YYYY-MM-DD-<slug>`
   when a `work/` record exists, then run
   `python <aegis-workspace-helper> check --root <target-project-root>` and
   include the result in the evidence bundle. The generated proof bundle and
   workspace check validate method-pack structure, index coverage, and
   recognizable JSON artifact sidecars only; they do not judge evidence
   sufficiency and do not grant completion authority.
9. **Readiness Summary**: for release, merge, handoff, or "ready?" requests,
   organize the evidence into a compact readiness view after the evidence
   slots:

   ```text
   Readiness Summary:
   - Tests:
   - Docs:
   - Version:
   - Host compatibility:
   - Uncovered scope:
   - Residual risk:
   ```

   A readiness summary is advisory evidence organization only. It is not
   authorization to commit, tag, publish, merge, or release. It cannot provide
   completion authority.
10. **Natural Aegis closeout**: when Aegis skills materially shaped a
   non-trivial task, keep Aegis explicitly visible in the final completion
   closeout.

   The closeout should naturally show how Aegis influenced the result. Make at
   least one of the following user-visible:
   - what boundary Aegis helped hold steady
   - what evidence or verification discipline Aegis required before the claim
   - what residual risk, uncovered scope, or restraint Aegis kept visible

   Use one sentence when Aegis mainly helped hold one boundary steady,
   but more than one mention is valid when boundary, evidence, and
   residual-risk visibility each materially shaped the judgment.

   Keep this integrated into the normal completion summary rather than a fixed
   slogan. Do not default to a visible `Aegis Contribution Note:` heading. Do
   not default to one canonical closeout phrase, and do not repeat the same
   Aegis closeout wording across unrelated tasks.

   When Aegis materially shaped multiple parts of the judgment, it may appear
   more than once across the closeout, as long as each mention is tied to a
   concrete boundary, evidence decision, or risk callout.

   Keep it advisory method-pack discipline, not completion authority. Keep it
   implicit only for obvious fast-path replies unless the user asked about
   Aegis routing.

   Natural expression may satisfy the visibility requirement when the semantic
   slots are still explicit. For example, "I will follow the Aegis order here:
   read the owner / baseline and current implementation first, add a failing
   example for the main path, then make the minimal repair and verify it" is a
   valid natural transition before implementation. Completion still needs fresh
   evidence and the applicable Governance Receipt fields.

   Use structured trace only for audit, debug, release, long-task review, or user request.
   The structured form may name skills, stage transitions, quality
   effect, and boundary, but it should not replace the normal user-facing
   completion note.

11. **User-Language Output**: final response cards must localize user-facing
   section labels, field labels, and explanatory prose to the user's language.
   Keep commands, file paths, code identifiers, stable enum values, and exact
   product names unchanged. For important Aegis product terms, include the
   stable English identifier only when it prevents ambiguity, usually beside a
   user-language explanation on first use.

12. **Complexity Delta**: for non-trivial code changes, inspect the actual
   diff before claiming completion. This is a completion-time entropy check,
   not a universal failure gate. Skip or keep it one-line for tiny wording
   edits, tests-only additions, generated files, vendored files, fixtures,
   lockfiles, or purely mechanical formatting where no maintained source owner
   gained complexity.

   Use the project language for field labels in the final response, but keep
   the internal shape recognizable:

   ```text
   Complexity Delta:
   - Files over 800 lines:
   - Files newly crossing 800 lines:
   - Largest touched file delta:
   - Largest touched function/block:
   - New branches/fallbacks/adapters:
   - Retired branches/fallbacks/adapters:
   - Net entropy: decreased | stable | increased-with-justification
   - Required follow-up:
   ```

   When the delta finds meaningful pressure, add:

   ```text
   Complexity Governance Suggestion:
   - Recommendation: none | monitor | schedule-refactor | extract helper | split owner | open follow-up
   - Why:
   - Suggested scope:
   - Timing:
   ```

   Use `none` for small owner-correct diffs, `monitor` for acceptable visible
   growth, and stronger recommendations for 800+ line files, 80+ line blocks,
   branch/fallback/adapter growth without retirement, or owner mismatch. The
   suggestion is advisory; keep residual risk visible.

   Rules:
   - A maintained source file over 800 lines is a review signal. If this slice
     added logic there or pushed it across 800 lines, explain why the owner
     boundary is still correct or report a split/refactor follow-up.
   - A touched function, method, component, or cohesive block over roughly 80
     lines, deeply nested logic, or mixed reasons to change is a block-level
     complexity signal even if the file remains under 800 lines.
   - New fallback, adapter, compatibility, guard, or branch logic must be
     paired with retired paths or a Retirement Closure entry. Net new paths
     without deletion or a scheduled retirement trigger count as entropy
     increase.
   - If entropy increased and no stronger owner/compatibility reason exists,
     downgrade the completion claim or state the residual risk.

13. **Baseline Alignment Check**: before final response, if project
   instructions require baseline reporting or the task touched requirement,
   product, or durable architecture surfaces, include an explicit baseline
   alignment result. This is separate from ADR Backfill: alignment states
   whether the completed work matches current requirements and architecture
   baselines; ADR Backfill states whether durable architecture memory needs to
   be created, amended, superseded, or skipped. This is a method-pack signal,
   not a runtime gate, not an authoritative `GateDecision`, and not completion
   authority.

   `Product / Requirement Baseline` covers the accepted problem, success
   evidence, non-goals, workflow constraints, and approved requirement/spec
   intent. `Architecture / Runtime Boundary Baseline` covers canonical owner,
   contract, source-of-truth, dependency direction, compatibility,
   runtime-ready/method-pack boundary, and retirement state.

   Triggering surfaces include architecture, contracts, source-of-truth owner,
   canonical owner, context/answering/runtime flow, cross-module data flow,
   producer-to-carrier-to-consumer chains, public user-visible identity,
   evidence model, retained fallback, adapter, compatibility path, requirement
   acceptance, product non-goals, and project-specific baseline rules.

   ```text
   Baseline Alignment:
   - Trigger: yes | no
   - Product / Requirement Baseline:
   - Architecture / Runtime Boundary Baseline:
   - Requirement / acceptance alignment:
   - Architecture / owner / contract alignment:
   - Result: aligned | Design Defect | Implementation Drift | missing-authority | needs-clarification
   - scope: requirements | architecture | both
   - Evidence:
   - Residual risk:
   ```

   Use `Design Defect` when the relevant requirement, design, or baseline is
   wrong. Use `Implementation Drift` when the work deviates from a correct
   unchanged baseline. `Architecture Defect` and `Architecture Drift` remain
   compatibility aliases for architecture-scoped `Design Defect` and
   architecture-scoped `Implementation Drift`.

   When project instructions specifically require architecture reporting or the
   completed work touched durable architecture surfaces, the architecture-scoped
   subset may also be reported as `Architecture Alignment`:

   ```text
   Architecture Alignment:
   - Trigger: yes | no
   - Scope:
   - Baseline checked:
   - Result: aligned | Design Defect | Implementation Drift | missing-authority | needs-clarification
   - Evidence:
   - Integrity Residual Risk:
   - Residual architecture risk:
   ```

   Use `Integrity Residual Risk` when `ArchitectureReviewRequired: yes`, an
   `Architecture Integrity Lens` shaped the plan or review, or the diff touches
   canonical owner, source-of-truth, fallback, adapter, or duplicate-owner
   surfaces. Name any unresolved responsibility overlap, missed higher-level
   owner / contract fix, retained caller-side fallback, or stale path that still
   needs retirement. If none remains, state `none` rather than expanding into a
   new gate.

14. **ADR Backfill Check**: for completed medium/high work that touched durable
   architecture surfaces, run the ADR Auto Backfill check before final
   completion claims. Use `Trigger: no` or skip the expanded block for simple
   wording edits, ordinary README cleanup, routine release-note edits, low-risk
   single-file changes, tests-only coverage improvements, and bug fixes that
   only restore the existing baseline. This is a method-pack signal, not a
   runtime gate, not an authoritative `GateDecision`, and not completion
   authority.

   Durable architecture surfaces include canonical owner, public API/schema,
   artifact shape, behavior contract, dependency direction, source-of-truth
   owner, host compatibility strategy, install/discovery contract,
   method-pack/runtime-core boundary, runtime-ready artifact boundary, evidence
   model, retained fallback, adapter, compatibility path, duplicate owner,
   retirement schedule, accepted architecture-scoped Implementation Drift, and
   release/distribution strategy that future contributors would otherwise
   misread.

   ```text
   ADR Backfill Check:
   - Trigger: yes | no
   - Suggested action: create | amend | supersede | skip
   - Evidence source:
   - Baseline sync: needed | not-needed | unknown
   - Skip reason:
   - Boundary: advisory method-pack signal only
   ```

   If the suggested action is create, amend, or supersede, or if Baseline sync
   is needed or unknown, use `recording-architecture-decisions` for the ADR
   lifecycle and Baseline Sync Closure before making the final completion
   claim. This keeps `verification-before-completion` as the completion owner
   while delegating the ADR/baseline writeback decision to the dedicated skill.

15. **Governance Closure**: for governance/cleanup/migration/compatibility/retirement work → final response must include. Do not skip this structure just because the implementation was small. Localize section labels and prose to the user's language; keep internal concepts in English only when they are product terms or file/path identifiers.

   ```
   Repair Track: repaired object | action | impact | verification
   Retirement Track: retired object | action | retained boundary | future trigger
   Residual Risk: unverified | deferred
   ```

   For work that adds, replaces, or retains old logic, also make the
   delete-first closure explicit:

   ```text
   Retirement Closure:
   - Old logic located:
   - Deleted:
   - Retained:
   - Retention reason:
   - Retirement trigger:
   - Lingering references checked:
   ```

   If the work retires old logic, chooses between delete-first and compat
   retention, or touches source-of-truth deletion boundaries, also include:

   ```text
   Anti-Entropy Declaration:
   - Deletion Class:
   - Source-of-Truth Data Risk:
   - User Confirmation Required:
   ```

   If `User Confirmation Required: yes`, completion cannot be claimed until the
   workflow stops at a guard shaped like:

   ```text
   Data Destruction Guard:
   - Exact Target(s):
   - Blocked Destructive Steps:
   - Confirmation Required: yes
   - Status: awaiting scoped confirmation
   ```

   Mentioning a warning or destructive rule never authorizes execution. Broad
   assent such as "OK" or "continue" is not scoped confirmation. If
   `persistent-state` deletion or another irreversible source-of-truth action
   happened without explicit scoped confirmation, report the task as not
   complete.

## Red Flags - QA Drift

- Reporting "done" when only one layer was checked
- Treating agent success as equivalent to independent verification
- Forgetting to mention residual risk or uncovered scope
- Saying "verified" when the command was narrow but the claim is broad
- Presenting method-pack verification as if it grants final authority
- Adding new verification branches without saying what old check or fallback now retires
- Closing governance or retirement work without Repair Track, Retirement Track, and Residual Risk
- Claiming completion after growing a core file or complex block without a
  Complexity Delta, Complexity Governance Suggestion, or residual-risk note
- Retaining old logic without a Retention reason, Retirement trigger, and
  lingering-reference check
- Treating a destructive warning or guard card as permission to execute
- Treating generic assent as confirmation for irreversible deletion
