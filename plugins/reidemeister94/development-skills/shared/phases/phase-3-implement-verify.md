# Phase 3: IMPLEMENT + VERIFY — GATE

**Cannot start without user-approved plan.** No approval → Phase 1.

Implementation in main thread; verification inline via `Bash`. Apply [Iron Rules](../iron-rules.md) — Process Rule B (Red/Green TDD) and Process Rule D (spirit beats letter) govern every cycle; Pillar 3 (no claim without fresh evidence) governs every verification claim.

---

## Step 1: Update plan file BEFORE any source file

1. **WORKFLOW STATE** → `Current Phase: 3 (Implement + Verify)`.
2. **Add `## Task Checklist`** — one `- [ ]` line per task.

---

## Implementation Discipline (main-thread standing instructions)

**Vertical slices only:** one behavior/check → minimal implementation → verification → next behavior. Do NOT write all tests first and then all code; that's horizontal slicing and produces brittle tests for imagined implementation shape. If a task would require >100 lines before feedback, split it smaller.

**TDD cycle:** RED (one test, run, must fail for the *expected reason*) → GREEN (simplest code that passes, no regressions) → REFACTOR (kill duplication, unclear names, >70 lines, dead code, defensive try/catch on safe paths, wrapper-for-nothing — run tests after). One test = one cycle. **Wrote production code before the test? Delete it. Start with the test.**

**Surgical:** modify only what the task requires. No bundled cleanup. No refactoring of nearby code. Functions >70 lines → split.

**Anti-poisoning:** before each task, confirm file paths exist (Glob/Grep) and signatures match source. Never trust memory of file contents across tasks — re-read.

**Module refactoring:** before moving anything, `Grep` every import + every mock/patch path in `src/` and `tests/`. After moving, update every caller + every mock; linter clean; tests show zero `ImportError`. Don't claim split complete until ALL callers + mocks are updated.

**Comments:** WHY only. Never restate WHAT the code does.

**Progress checkpoints (5+ tasks):** every 3 done, mark `[x]` in plan with affected files. Context near capacity → write progress to disk + summarize.

---

## Step 2: Implement each task

For each task in `## Task Checklist`:

1. **Read relevant source files** (fresh — don't trust memory).
2. **If unclear:** STOP. Ask the user with specific questions. Do NOT guess.
3. **Run TDD cycle(s)** per behavior (RED → GREEN → REFACTOR).
4. **Update plan file** after the task:
   ```markdown
   - [x] Task N: [description]
     Files: src/file.py:15-42, tests/test_file.py (new)
   ```

---

## Step 3: 5-Step Verification Gate

**Before ANY positive claim** ("tests pass", "implementation complete", "no issues"):

1. **IDENTIFY** — What command proves this claim? Name it.
2. **RUN** — Execute the FULL command. Fresh, complete, no partial runs.
3. **READ** — Read full output. Check exit code. Count pass/fail.
4. **VERIFY** — Does the output actually confirm the claim?
   - YES → State claim WITH evidence (command + result).
   - NO → State actual status with evidence. Do NOT rationalize.
5. **CLAIM** — Only now make the assertion.

**Skip any step = lying, not verifying.** *"I'm confident"* is not a step.

---

## Step 4: Verification via inline Bash (no subagent)

Run verification commands from your language skill's config via the `Bash` tool:

- Run from project root.
- Capture FULL output. For long output (>200 lines), redirect to a temp file (e.g., `/tmp/verify-out-NNNN.log`) and read excerpts.
- Append details (or temp-file path) to plan file's `## Verification Results`.
- Keep ONLY the pass/fail summary + failing-line excerpts in your chat response.

```markdown
## Verification Results

### Iteration N
- **Command:** `<test command>`
- **Result:** `<N/M passed>` (or details from `/tmp/verify-out-NNNN.log`)
- **Action:** [what was fixed]

### Final
- **Command:** `<test && lint && format-check>`
- **Result:** all green
```

### Tiers

- **Tier A — Projects with tests:** run all verification commands; add new tests for new/modified code first; coverage target 70-80%.
- **Tier B — Legacy without tests:** run verification commands inline. If a command mutates state (DB writes, network calls, file system changes beyond the working tree), confirm with the user before each run.
- **Language skills may define additional tiers** (e.g., Tier C for Xcode).

### Verification Honesty

Distinguish levels in the chat summary: `Tests: PASS (N/M)` · `Tests: COULD NOT RUN — [reason]. Linting: PASS` · `Tests: FAIL (N/M)`. Never report "all checks pass" if tests didn't execute. Always attempt the test command, not just the linter.

---

## Step 5: Fix-Verify cycle

If verification FAILS:

1. **Read failure details** from plan file `## Verification Results`.
2. **Code bug:** fix, re-run Step 4. Stay in this phase.
3. **Plan wrong:** return to Phase 1, get new approval, resume.
4. **Environmental:** document, ask user.

**Regression guard:** Track pass/fail across iterations. Net regression → STOP and reassess. Two consecutive regressions → return to Phase 1.

**After fix-verify cycle:** Run `/compact` before re-running.

---

## Step 6: Final Implementation Log

After all tasks complete and verification PASS, append `## Implementation Log` to plan file:

```markdown
## Implementation Log

### Task N: [name]
- **Approach:** [why this, not alternatives]
- **Discoveries:** [unexpected findings — omit if none]
- **Decisions:** [design choices + rationale — omit if none]
```

Update chronicle (if created in Phase 2) with discoveries from Implementation Log.

---

## Expected Artifacts

- All tasks `[x]` in plan file with affected files
- `## Implementation Log` with per-task reasoning
- `## Verification Results` with full audit trail
- Chronicle updated with discoveries
- WORKFLOW STATE: `Current Phase: 4 (Review + Finalize)`

**Gate:** State **"IMPLEMENT + VERIFY COMPLETE"** with evidence.

**→ Run `/compact` now** — this is the heaviest phase. Then proceed to Phase 4. Read `phase-4-review-finalize.md`.
