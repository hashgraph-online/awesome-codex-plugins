---
name: revision
description: >
  Trace bugs and manual fixes back to kits and prompts, then fix at the source so the iteration loop
  can reproduce the fix autonomously. Covers the 6-step revision process for commit sweeps AND the
  single-failure backpropagation protocol (six steps: TRACE, ANALYZE, PROPOSE, GENERATE, VERIFY, LOG)
  that runs automatically via the auto-backprop hook on test failure and manually via
  /ck:revise --trace. Trigger phrases: "revise", "revision", "trace bug to cavekit",
  "fix the cavekit not the code", "why did this bug happen", "update kits from bug",
  "trace this bug", "backprop", "why wasn't this caught", "fix the kit", "regression test".
---

# Revision: Tracing Bugs Back to Kits

In Cavekit, revision means tracing a production defect upstream through the cavekit chain until you find the gap that allowed it. In practice, when the built software has bugs or gaps, you trace the issue back to the kits and prompts and fix at the source -- not just in code.

**Key insight:** When a fix lives only in code with no corresponding cavekit update, the next iteration loop may reintroduce the same defect. The goal is that kits plus the iteration loop can reproduce any fix autonomously.

---

## 1. Why Revision Matters

Without revision, every bug fix is a one-off patch. The next time the iteration loop runs, it may reintroduce the bug because nothing in the kits or plans prevents it.

With revision:
- Bug fixes become **cavekit improvements** that persist across all future iterations
- The iteration loop becomes **self-correcting** -- it learns from every manual intervention
- Kits become **progressively more complete** over time
- The gap between "what kits describe" and "what works" **shrinks monotonically**

```
Without revision:
  Bug found -> Fix code -> Bug may return next iteration

With revision:
  Bug found -> Fix code -> Update cavekit -> Re-run iteration loop -> Fix emerges from kits alone
```

---

## 2. The 6-Step Revision Process

This is the complete process for tracing a bug back to its cavekit-level root cause and closing the loop.

### Step 1: Identify and Fix the Defect

Locate the bug -- whether through manual testing, automated failures, user reports, or monitoring alerts -- and resolve it through normal debugging. This produces a working code change, but the job is far from done: until the underlying cavekit gap is closed, this fix is fragile.

```bash
# The fix produces commits that we will analyze
git log --oneline -5
# a1b2c3d Fix: connection pool exhaustion under concurrent load
# e4f5g6h Fix: missing rate limit headers in API responses
```

### Step 2: Analyze What the Cavekit Missed

This is the pivotal step. Ask: **"Where in the cavekit chain did this requirement slip through?"**

Break the analysis into five dimensions:
- **WHAT** changed (files, functions, observable behavior)
- **WHY** it was wrong (which assumption proved false)
- **VISUAL** — does this fix change visual appearance (CSS, styling, layout)? If yes, check whether DESIGN.md covers the pattern. A missing design pattern is a design system gap that should be fixed alongside the cavekit gap.
- **The RULE** (the invariant that should have been stated)
- **The LAYER** (which cavekit, plan, or prompt should have contained this)

Example analysis:

```markdown
## Revision Analysis: Database Connection Pooling

**WHAT changed:** Added pool size limits and idle timeout in `src/db/pool.ts`
**WHY:** The data layer cavekit assumed unlimited connections; under load the database
         rejected new connections once the server-side limit was reached
**RULE:** "The database module MUST configure a bounded connection pool with
          idle timeout and max-connection limits matching the deployment target"
**LAYER:** cavekit-data.md (no mention of pool configuration), plan-data.md (no task for pool tuning)
**Cavekit implications:** Add requirement R5 to cavekit-data.md covering connection pool settings
```

### Step 3: Update the Cavekit

Add the missing requirement or constraint to the appropriate cavekit file. Focus on acceptance criteria that are concrete enough for the iteration loop to act on:

```markdown
# In context/kits/cavekit-data.md, add:

### R5: Database Connection Pool Configuration
**Description:** The database module must use a bounded connection pool
with configurable limits to prevent resource exhaustion under load.
**Acceptance Criteria:**
- [ ] Maximum pool size is configurable and defaults to a sensible value
- [ ] Idle connections are reaped after a configurable timeout
- [ ] Pool exhaustion returns a clear error rather than hanging indefinitely
- [ ] Connection health checks run before returning a connection from the pool
**Dependencies:** R1 (database client setup), R2 (environment configuration)
```

### Step 4: Propagate Changes to Plans and Tracking

Trace the cavekit update through every downstream context file:

1. **Identify affected plan files:** Which plans govern the changed source paths?
2. **Update plans:** Add or close tasks reflecting the new requirement.
3. **Update impl tracking:** Record the revision event and its root cause.
4. **Annotate:** Mark updated sections with revision metadata so future reviews can trace lineage.

```markdown
# In context/plans/plan-data.md, add:

### T-DATA-005: Configure bounded connection pool
- **Status:** DONE (revised from manual fix a1b2c3d)
- **Cavekit:** R5 in cavekit-data.md
- **Files:** src/db/pool.ts
- **Acceptance criteria:**
  - [ ] Max pool size enforced
  - [ ] Idle timeout configured
  - [ ] Exhaustion handled gracefully
```

### Step 5: Apply Systemic Prompt Improvements (If Pattern Detected)

When the defect represents a recurring class of problem rather than a one-off, elevate the fix to the prompt level so it applies across all domains:

**Signs you are looking at a pattern:**
- The same category of bug has surfaced in more than one module
- The gap is structural (e.g., no specs anywhere address resource limits)
- A missing validation gate allowed the issue through

**Example systemic fix:**

```markdown
# In prompt 003, add to the validation section:

## Resource Management Validation
For every external resource integration, verify:
- [ ] Connection or handle limits are bounded and configurable
- [ ] Idle resources are cleaned up on a timeout
- [ ] Exhaustion scenarios return actionable errors
- [ ] Resource lifecycle is covered by tests under load
```

### Step 6: Verify and Lock In

Run the iteration loop against the updated kits to prove the fix emerges from kits alone, then generate regression tests to prevent future recurrence:

```bash
# Proof step: remove the manual fix and re-run from specs
git stash  # temporarily remove the manual fix
iteration-loop context/prompts/003-generate-impl-from-plans.md -n 5 -t 1h
# Verify the fix appears in the generated implementation

# If it does NOT, the cavekit update is insufficient -- return to Step 3
```

Once verified, create regression tests:

```bash
# Generate tests targeting the updated cavekit
{TEST_COMMAND} --cavekit context/kits/cavekit-data.md

# Or manually create a regression test
# tests/db/connection-pool-limits.test.ts
```

The regression tests should:
- Map directly to the acceptance criteria from Step 3
- Fail if the fix is reverted
- Run as part of the standard test suite going forward

---

## 3. Revision Analysis (Automated)

The revision analysis automates Steps 2-4 by examining recent git history.

### 3.1 Classify Commits

Analyze recent commits and classify each as:

| Classification | Meaning | Action |
|---------------|---------|--------|
| **Manual fix** | Human or interactive agent fixed a bug | Trace back to cavekit -- this is a revision target |
| **Iteration loop** | Automated iteration loop made the change | No action -- this is the system working as intended |
| **Infrastructure** | Build config, CI, tooling changes | No action -- not cavekit-related |

**How to classify:**
- Commits from iteration loop sessions have predictable patterns (automated commit messages, batch changes)
- Manual fixes are typically single-issue, focused commits with descriptive messages
- Infrastructure changes touch config files, build scripts, CI pipelines

### 3.2 Analyze Each Manual Fix

For each commit classified as a manual fix, determine:

```markdown
## Commit: abc1234 "Fix: auth token not refreshing on 401"

### WHAT changed
- File: src/auth/client.ts
- Function: handleApiResponse()
- Behavior: Added 401 detection and token refresh logic

### WHY it was wrong
- The auth module did not handle 401 responses
- Tokens would expire and never refresh, causing cascading auth failures

### RULE (invariant that should have been specified)
- "Authentication tokens must be refreshed automatically on 401 responses"

### LAYER (which context file should have caught this)
- cavekit-auth.md: Missing requirement for error-based token refresh
- plan-auth.md: No task for 401 handling

### Cavekit Implications
- Add R7 to cavekit-auth.md: Token Refresh on Authentication Failure
- Add T-AUTH-007 to plan-auth.md: Implement token refresh on 401
```

### 3.3 Discover Affected Plan Files

Dynamically discover which plan files govern the changed source paths:

```
Changed file: src/auth/client.ts
  -> Matches pattern: src/auth/*
  -> Governed by: plan-auth.md
  -> Cavekit: cavekit-auth.md

Changed file: src/data/api.ts
  -> Matches pattern: src/data/*
  -> Governed by: plan-data.md
  -> Cavekit: cavekit-data.md
```

Use file ownership tables (from prompts) or directory conventions to map source files to plan/cavekit files.

### 3.4 Update Context Files

For each revision target, update:

1. **Cavekit file:** Add missing requirement with acceptance criteria
2. **Plan file:** Add task referencing the new requirement
3. **Impl tracking:** Record the revision event

```markdown
# In context/impl/impl-auth.md, add:

## Revision Log
| Date | Commit | Issue | Cavekit Update | Plan Update |
|------|--------|-------|-------------|-------------|
| 2026-03-14 | abc1234 | 401 not handled | R7 added to cavekit-auth.md | T-AUTH-007 added |
```

### 3.5 Run Tests

After updating context files, run the test suite to verify nothing broke:

```bash
{BUILD_COMMAND}
{TEST_COMMAND}
```

### 3.6 Generate Regression Tests

For each revision target, generate a regression test that:
- Tests the specific acceptance criteria from the new cavekit requirement
- Would fail if the fix were reverted
- Is included in the standard test suite going forward

---

## 4. Patterns and Anti-Patterns

### Signs the process is working

| Pattern | What You Observe |
|---------|--------------------|
| **Declining manual intervention** | Each iteration cycle requires fewer hand-applied fixes because kits capture more of the ground truth |
| **Broader cavekit coverage per fix** | A single revision event adds constraints that block an entire family of related defects, not just one |
| **Cross-domain prevention** | Prompt-level adjustments made after a bug in one module prevent analogous bugs from appearing in other modules |
| **Autonomous reproducibility** | After a cavekit update, the iteration loop independently produces the same correction that a human applied manually |

### Warning signs and remedies

| Anti-Pattern | Symptom | Remedy |
|-------------|---------|-----|
| **Code-only patches** | The same category of defect resurfaces across iterations | Follow the full 6-step process; never stop after the code fix in Step 1 |
| **Overly specific cavekit additions** | Each revision prevents only the exact bug encountered, while slight variations slip through | Formulate the RULE as a general invariant, not a narrow patch |
| **Skipping verification** | Kits are updated but nobody confirms the iteration loop can reproduce the fix independently | Always execute Step 6; a cavekit that does not drive correct generation is incomplete |
| **Brittle over-specification** | Kits dictate implementation minutiae, causing breakage on minor refactors | Constrain the WHAT and WHY; leave the HOW to the implementation |
| **Accumulated revision debt** | A backlog of manual fixes sits un-traced, growing with each sprint | Set a cadence (e.g., end of each iteration) to clear the backlog; debt compounds quickly |

---

## 5. When NOT to Revise

Not every code fix needs revision:

- **One-off environment issues** (wrong config, missing dependency) -- these are infrastructure, not cavekit gaps
- **Typos and formatting** -- trivial fixes that do not reflect missing requirements
- **Exploratory changes** during prototyping -- kits are still being formed
- **Performance optimizations** that do not change behavior -- unless performance is a cavekit requirement

**Rule of thumb:** If the iteration loop could plausibly reintroduce the bug, revise. If not, skip it.

---

## 6. Revision and Convergence

Revision directly improves convergence:

```
Iteration 1: 350 lines changed, 8 manual fixes needed
  -> Revise all 8 fixes into kits
Iteration 2: 140 lines changed, 3 manual fixes needed
  -> Revise 3 fixes
Iteration 3: 30 lines changed, 1 manual fix needed
  -> Revise 1 fix
Iteration 4: 10 lines changed, 0 manual fixes needed
  -> Convergence achieved
```

Every revision cycle tightens the kits, so the iteration loop settles into a stable solution in fewer passes. If convergence is not improving, the most likely cause is that manual fixes are being applied without tracing them back to kits.

**Stalled convergence paired with ongoing manual fixes is a clear sign of revision debt.** The kits have not absorbed the lessons from past corrections, so the loop keeps regenerating flawed output that demands human repair.

---

## 7. Integration with Other Cavekit Skills

- **Convergence monitoring:** Use `ck:convergence-monitoring` to detect when manual fixes are decreasing (good) or increasing (revision debt).
- **Prompt pipeline:** Revision may trigger changes to prompts (Step 6), which affects the `ck:prompt-pipeline` design.
- **Validation-first design:** Stronger validation gates catch issues earlier, reducing the need for revision.
- **Gap analysis:** Systematic gap analysis (`/ck:review --mode gap`) identifies revision targets proactively, rather than waiting for bugs.

---

## Cross-References

- **Convergence patterns:** See `references/convergence-patterns.md` for how revision drives convergence.
- **Prompt pipeline:** See `ck:prompt-pipeline` skill for how prompt 006 (rewrite pattern) implements automated revision.
- **Impl tracking:** See `ck:impl-tracking` skill for the revision log format in implementation tracking documents.
- **Validation gates:** See `ck:validation-first` skill for validation layers that catch issues before they require revision.

---

## 8. Automated Backpropagation (Single-Failure Trace)

The revision skill also handles the **single-failure backpropagation protocol** — invoked automatically when a test command fails during `/ck:make`, or manually via `/ck:revise --trace`. Where Sections 1–7 describe the multi-commit revision sweep, this section describes the single-failure trace with a tighter six-step procedure and an explicit audit log.

**Principle:** Bugs are spec bugs until proven otherwise. Before patching code, verify the kit actually covered the failing behavior. If it did not, the fix is a kit amendment plus a regression test — not just a patch.

### Six-Step Procedure

#### 1. TRACE — match failure to a requirement

Read the failure output. Find the single acceptance criterion (or gap of one) that, if asserted, would have caught this. Identify the kit and R-ID:

```
Kit: cavekit-auth.md
Requirement: R004 (rate-limit middleware)
Closest AC: AC2 ("returns 429 when limit exceeded")
Missing coverage: 429 header case sensitivity not asserted
```

If no requirement fits, the bug is in a dimension the kit never addressed — this is a **missing requirement** (case D below).

#### 2. ANALYZE — classify the gap

One of:

- **A. missing_criterion** — the requirement exists but the acceptance criteria do not cover this case. Add an AC.
- **B. incomplete_criterion** — an AC partially covers it but is too vague to catch the failure. Tighten the AC.
- **C. wrong_criterion** — an AC asserts the wrong thing. Correct it.
- **D. missing_requirement** — no requirement addresses this dimension at all. Add a new R.

#### 3. PROPOSE — draft the spec change

Write the exact amendment. Required fields:

```
Classification: missing_criterion
Kit: cavekit-auth.md
Change: R004 append AC5
Proposed AC: "AC5 — Rate-limit headers (X-RateLimit-*, Retry-After) are
  returned with canonical lowercase casing per RFC 7230 §3.2."
Trace: auth.test.ts → 429 path → header casing mismatch
```

Show the proposed change to the user. **Wait for explicit approval** before writing to the kit. Do not silently amend specs.

#### 4. GENERATE — regression test

Before fixing the bug, write a test that asserts the new AC and currently **fails**. This locks in the requirement in executable form.

Commit the failing test separately from the fix:

```
git commit -m "test: add regression for rate-limit header casing (cavekit-auth.md R004 AC5)"
```

#### 5. VERIFY — fix until the test passes

Patch the code. Run the full test suite. Confirm the new regression test passes and nothing else regresses. Commit the fix referencing the AC.

#### 6. LOG — write a trace entry

Append to `.cavekit/history/backprop-log.md`:

```markdown
## Entry {n}

- id: 12
- date: 2026-04-17T14:22Z
- classification: missing_criterion
- kit: cavekit-auth.md
- requirement: R004
- ac_added: AC5
- failing_test_before_fix: auth.test.ts::rate-limit headers casing
- fix_commit: abc1234
- pattern_category: input_validation
```

### Pattern Detection

The log is a corpus. If the same `pattern_category` appears 3+ times in one project, the issue is systemic and belongs one layer up — at the brainstorming / kit-writing layer, not per-requirement. Categories:

- `input_validation` — unvalidated / mis-cased / range-unchecked input.
- `concurrency` — races, missed locks, stale reads.
- `error_handling` — swallowed exceptions, missing retries, partial rollbacks.
- `integration` — contract drift between services, missing end-to-end tests.
- `observability` — silent failures, missing logs/metrics.

When a threshold hits, propose a cross-kit amendment (e.g., a validation rule added to every input-accepting kit). Announce this to the user.

### Auto-Backprop Hook Integration

The `auto-backprop.js` hook writes `.cavekit/.auto-backprop-pending.json` when a test command fails during `/ck:make`. The stop hook reads this flag and prepends a trace directive to the next iteration's prompt, which tells the agent to run the six steps above before resuming normal task execution. Once the directive fires, the flag is atomically deleted.

Disable via `auto_backprop = false` in `.cavekit/config.json` if you need to run `/ck:make` without this safety net (e.g., during exploratory spikes).

### Anti-Patterns

- **Patch first, spec later** — fixes that never make it back to the kit. Every rerun of the loop may re-introduce the bug.
- **Silent amendment** — updating a kit without user approval. The spec is the contract; amendments are a negotiation, not a refactor.
- **Per-bug regression test with no spec change** — the test passes, but the next reader of the kit still will not know why. The AC must be written down.
- **Bulk backprop** — rolling up N failures into one spec change. Each failure gets its own entry. Patterns emerge only if each is logged separately.
