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
  Non-trivial code changes → also report Complexity Delta, Complexity Governance Suggestion, and Major Complexity Alert when triggered.
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
- Aegis Visibility in this workflow ties the final claim to the boundary held,
  evidence discipline added, and residual risk or uncovered scope kept visible.
  If another owner workflow already surfaced visibility earlier, reconcile that
  trail in the closeout instead of replacing it with a used-skills list.
- For non-trivial Aegis-shaped work, final closeout must include one
  task-specific sentence about the boundary, evidence, or residual risk; concise
  final answers still keep one natural Aegis sentence and must not drop this
  slot. Do not replace it with a used-skills list.
- If required entry visibility was omitted, final response must include a
  retrospective visibility recovery line and name the omission as a visibility
  gap. This recovery does not make the earlier omission compliant.
- Trace Digest is the on-demand white-box closeout for audit, debug, release,
  long-task review, or explicit user request. It summarizes execution trace,
  evidence chain, retrieval chain, static rules evaluated, rule effects,
  triggered skills, skipped relevant skills, tool / command trace,
  verification trace, stability signals, value signals, host capability gaps,
  unavailable fields, and redaction. Confidence labels are `measured`, `observed`, `inferred`, `declared`, or `unknown`.
- Trace Digest may summarize decision rationale, but it must not expose raw
  chain-of-thought or turn Aegis output into runtime authority.

TDD Completion Boundary:
- Judge the completion claim against the highest available explicit boundary.
- Parent plan/spec acceptance decides whole-task completion; `TaskIntentDraft`
  decides current-task completion; `Slice Card` decides slice completion only.
- `Execution Readiness View`, when present, constrains the implementation /
  verification readback for intent, scope, baseline, compatibility, retirement,
  test obligations, review gates, drift / rewind rules, and required evidence.
  It does not decide completion by itself.
- Match the boundary to the claim being made, and keep any higher open boundary
  explicit.
- If only slice-level evidence exists, do not claim whole-task `done`.
- A completed task or slice means the authorized execution / verification
  boundary reached its stop condition. It does not mean the underlying
  requirement is accepted.
- `Requirement accepted` requires the relevant Product / Requirement Baseline
  item and acceptance / verification criteria to be satisfied, or an explicit
  authorized risk acceptance.
- If no explicit boundary exists and atomicity is not clear, downgrade to
  `needs-verification` or return to framing/planning.

1. **Remove/Restore**: side effects? temp instrumentation restored?
2. **Evidence Bundle**: exact command, scope, exit status, key output. State what's covered and what's not. Include target test and related regression evidence. When automation is blocked, provide reproducible manual verification steps.
3. **Prompt Hygiene**: when external output shaped judgment → state whether summaries or raw excerpts were used. Name large payloads not loaded. If summary insufficient → read back excerpt or lower claim. Include Evidence Used / Not Loaded / Next Evidence boundary when relevant.
4. **Confidence**: A (direct + regression, no unknowns) | B (direct, bounded risk) | C (partial only, not closed)
5. **Authority**: verified evidence ≠ authoritative completion. Keep distinct.
6. **Goal Closure**: when `goal-framing` or optional `TaskIntentDraft` goal
   fields shaped the work, explicitly check the goal before claiming completion:

   Available boundary check for completion judgment:
   1. Parent plan/spec acceptance for whole-task completion, when present
   2. `TaskIntentDraft` Goal / Success evidence / Non-goals for the current
      task, when present
   3. `Slice Card` Goal / Verification / Stop for the current slice, when
      present

   ```text
   Goal Closure:
   - Goal status: satisfied | blocked | needs-verification | scope-exceeded
   - Success evidence:
   - Stop state: done | blocked | needs-verification | scope-exceeded
   - Non-goals respected:
   ```

   Use `done` only when success evidence is satisfied; `blocked` for missing
   dependency/permission/fact; `needs-verification` for insufficient evidence;
   `scope-exceeded` when continuing would exceed goal or non-goals.
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

   Advisory only. It does not authorize commit, tag, publish, merge, or release, and it does not provide completion authority.
   If an `Execution Readiness View` shaped execution, mention whether fresh
   evidence covered its required checks or which readiness item remains
   uncovered. Do not treat the view itself as verification evidence.
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

   If an Aegis skill was loaded for non-tiny work, closeout is not optional:
   concise final answers still keep one natural Aegis sentence tied to boundary,
   evidence, or residual risk.

   Natural expression may satisfy the visibility requirement when the semantic
   slots are still explicit. For example, "I will follow the Aegis order here:
   read the owner / baseline and current implementation first, add a failing
   example for the main path, then make the minimal repair and verify it" is a
   valid natural transition before implementation. Completion still needs fresh
   evidence and the applicable Governance Receipt fields.

   Use structured trace only for audit, debug, release, long-task review, or user request.
   The structured form may name task stage, triggered skills, skipped relevant
   skills, rule effects, quality effect, and boundary, but it should not
   replace the normal user-facing completion note.

   On request, use this compact shape:

   ```text
   Aegis Trace Digest:
   - traceLevel:
   - hostCapabilities:
   - taskStage:
   - triggeredSkills:
   - skippedRelevantSkills:
   - evidenceChain:
   - retrievalChain:
   - staticRulesEvaluated:
   - ruleEffects:
   - toolCommandTrace:
   - verificationTrace:
   - stabilitySignals:
   - valueSignals:
   - confidenceLabels: measured | observed | inferred | declared | unknown
   - unavailableFields:
   - redactionApplied:
   - boundary: advisory trace, not runtime authority or completion authority
   ```

11. **User-Language Output**: final response cards must localize user-facing
   section labels, field labels, and explanatory prose to the user's language.
   Keep commands, file paths, code identifiers, stable enum values, and exact
   product names unchanged. For important Aegis product terms, include the
   stable English identifier only when it prevents ambiguity, usually beside a
   user-language explanation on first use.

12. **Complexity Delta**: for non-trivial code changes, inspect the actual
   diff before claiming completion. This is a completion-time entropy check,
   not a universal runtime gate. Skip or keep it one-line for tiny wording
   edits, generated files, vendored files, fixture-data-only updates,
   lockfiles, or purely mechanical formatting where no maintained artifact
   gained complexity. Do not treat maintained test source files as a cheap
   `tests-only` exception.

   Use `using-aegis/references/complexity-governance.md` for shared artifact
   classes, pressure-signal interpretation, and major-complexity follow-up
   semantics.

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

   Also report completion-time closure of the planned complexity budget:

   ```text
   Complexity Closure:
   - Budget status: within-budget | exceeded-and-governed | exceeded-unresolved
   - Governed now:
   - Deferred follow-up:
   - Completion impact: complete | needs-follow-up | not-complete
   ```

   If completion-time complexity is over budget, classify whether the overrun
   can be governed inside the current authorized slice before doing additional
   owner extraction or scope expansion:

   ```text
   Completion-Time Complexity Repair Decision:
   - Overrun:
   - Authorized slice boundary:
   - Decision: govern-now | follow-up-required | not-complete
   - Why:
   - Verification:
   ```

   `govern-now` may continue with owner extraction, helper extraction, or old
   path deletion only when the repair is inside the current authorized scope,
   reduces or stabilizes complexity, and has a clear verification boundary.
   `follow-up-required` reports residual risk and suggested scope without
   expanding the current task. `not-complete` means the overrun blocks the
   requested completion claim.

   If a maintained artifact is materially oversized or crosses a major pressure
   boundary, make the follow-up explicit:

   ```text
   Major Complexity Alert:
   - Trigger:
   - Why it matters:
   - Visible follow-up:
   ```

   When the delta finds meaningful pressure, add:

   ```text
   Complexity Governance Suggestion:
   - Recommendation: none | monitor | schedule-refactor | extract helper | split owner | open follow-up
   - Why:
   - Suggested scope:
   - Timing:
   ```

   Rules:
   - Keep residual risk visible.
   - New fallback, adapter, compatibility, guard, or branch logic must be
     paired with retired paths or a Retirement Closure entry. Net new paths
     without deletion or a scheduled retirement trigger count as entropy
     increase.
   - If entropy increased and no stronger owner/compatibility reason exists,
     downgrade the completion claim or state the residual risk.
   - If `Complexity Closure` is `exceeded-unresolved`, do not claim the task is
     complete. State the task as `needs-follow-up` or `not-complete`.

13. **Baseline Alignment Check**: before final response, if project
   instructions require baseline reporting or the task touched requirement,
   product, or durable architecture surfaces, include an explicit baseline
   alignment result. This is separate from ADR Backfill and remains advisory
   method-pack output only.

   Use `docs/current/AEGIS_PROCESS_BASELINE.md` §3.0e and §16 for the canonical
   meaning of `Product / Requirement Baseline`, `Architecture / Runtime
   Boundary Baseline`, `Design Defect`, `Implementation Drift`, and their
   compatibility aliases.

   ```text
   Baseline Alignment:
   - Trigger: yes | no
   - Product / Requirement Baseline:
   - Architecture / Runtime Boundary Baseline:
   - Requirement Ready Check:
   - Requirement / acceptance alignment:
   - Architecture / owner / contract alignment:
   - Requirement acceptance boundary: task-or-slice-done | requirement-verified | requirement-accepted | risk-accepted | not-accepted | unknown
   - Result: aligned | Design Defect | Implementation Drift | missing-authority | needs-clarification
   - scope: requirements | architecture | both
   - Evidence:
   - Residual risk:
   ```

   Use the requirement acceptance boundary to avoid overstating completion:
   passing tests or a completed task / slice can support
   `requirement-verified`, but only confirmed acceptance criteria or authorized
   acceptance can support `requirement-accepted` or `risk-accepted`.

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
   completion claims. Advisory method-pack signal only.

   Use `docs/current/AEGIS_ADR_AUTO_BACKFILL.md` for canonical trigger
   criteria, durable-surface interpretation, create/amend/supersede/skip
   selection, and baseline-sync rules. When that baseline would not trigger,
   use `Trigger: no` or skip the expanded block here.

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
   When that dedicated skill chooses target-project `docs/aegis/adr/` as the
   owner surface, route file writes through `<aegis-workspace-helper> new-adr`,
   `<aegis-workspace-helper> amend-adr`, or
   `<aegis-workspace-helper> supersede-adr`, then run
   `<aegis-workspace-helper> check --root <target-project-root>` before the
   final completion claim.

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
- Treating task or slice completion as accepted requirement satisfaction
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
