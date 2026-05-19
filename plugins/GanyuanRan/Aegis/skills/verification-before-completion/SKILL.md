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

Use this compact evidence shape before any success claim:

```text
Evidence Card:
- Command / Check:
- Exit Status:
- Covered:
- Not Covered:
- Residual Risk:
- Confidence: A | B | C
```

1. **Remove/Restore**: side effects? temp instrumentation restored?
2. **Evidence Bundle**: exact command, scope, exit status, key output. State what's covered and what's not. Include target test and related regression evidence. When automation is blocked, provide reproducible manual verification steps.
3. **Prompt Hygiene**: when external output shaped judgment → state whether summaries or raw excerpts were used. Name large payloads not loaded. If summary insufficient → read back excerpt or lower claim. Include Evidence Used / Not Loaded / Next Evidence boundary when relevant.
4. **Confidence**: A (direct + regression, no unknowns) | B (direct, bounded risk) | C (partial only, not closed)
5. **Authority**: verified evidence ≠ authoritative completion. Keep distinct.
6. **Goal Closure**: when `goal-framing` or optional `TaskIntentDraft` goal
   fields shaped the work, explicitly check the goal before claiming completion:

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
9. **User-Language Output**: final response cards must localize user-facing
   section labels, field labels, and explanatory prose to the user's language.
   Keep commands, file paths, code identifiers, stable enum values, and product
   terms in English when that preserves precision. For important Aegis product
   terms, prefer first-use bilingual labels such as
   `架构对齐（Architecture Alignment）`; later references may use the user's
   language alone.

10. **Architecture Alignment Check**: before final response, if project
   instructions require architecture reporting or the task touched durable
   architecture surfaces, include an explicit architecture alignment result.
   This is separate from ADR Backfill: alignment states whether the completed
   work matches current baselines; ADR Backfill states whether durable
   architecture memory needs to be created, amended, superseded, or skipped.
   This is a method-pack signal, not a runtime gate, not an authoritative
   `GateDecision`, and not completion authority.

   Triggering surfaces include architecture, contracts, source-of-truth owner,
   canonical owner, context/answering/runtime flow, cross-module data flow,
   producer-to-carrier-to-consumer chains, public user-visible identity,
   evidence model, retained fallback, adapter, compatibility path, and
   project-specific baseline rules.

   ```text
   Architecture Alignment:
   - Trigger: yes | no
   - Scope:
   - Baseline checked:
   - Result: aligned | architecture drift | architecture defect
   - Evidence:
   - Residual architecture risk:
   ```

11. **ADR Backfill Check**: for completed medium/high work that touched durable
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
   retirement schedule, accepted architecture drift, and release/distribution
   strategy that future contributors would otherwise misread.

   ```text
   ADR Backfill Check:
   - Trigger: yes | no
   - Suggested action: create | amend | supersede | skip
   - Evidence source:
   - Baseline sync: needed | not-needed | unknown
   - Skip reason:
   - Boundary: advisory method-pack signal only
   ```

12. **Governance Closure**: for governance/cleanup/migration/compatibility/retirement work → final response must include. Do not skip this structure just because the implementation was small. Localize section labels and prose to the user's language; keep internal concepts in English only when they are product terms or file/path identifiers.

   ```
   Repair Track: repaired object | action | impact | verification
   Retirement Track: retired object | action | retained boundary | future trigger
   Residual Risk: unverified | deferred
   ```

## Red Flags - QA Drift

- Reporting "done" when only one layer was checked
- Treating agent success as equivalent to independent verification
- Forgetting to mention residual risk or uncovered scope
- Saying "verified" when the command was narrow but the claim is broad
- Presenting method-pack verification as if it grants final authority
- Adding new verification branches without saying what old check or fallback now retires
- Closing governance or retirement work without Repair Track, Retirement Track, and Residual Risk
