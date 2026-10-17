---
name: convergence-monitoring
description: >
  Detecting whether agent iterations are converging toward a stable solution or hitting a ceiling.
  Covers convergence signals, ceiling detection, non-convergence diagnosis, test pass rate as
  a convergence metric, and forward progress tracking for large projects.
  Trigger phrases: "convergence", "is the agent converging", "ceiling detection",
  "when to stop iterating", "diminishing returns"
---

# Convergence Monitoring

Convergence monitoring answers the most important question in iterative AI development: **when should you stop iterating?** The answer is not a fixed number of iterations or a time limit -- it is convergence. Convergence means the agent's output is stabilizing; each iteration produces fewer and smaller changes than the last.

**Core insight:** You don't need a zero-diff -- you need the remaining modifications to be inconsequential.

---

## 1. What Is Convergence?

Convergence appears as a rapid, consistent decline in the volume of changes from one iteration to the next:

```
Iteration 1:  ████████████████████████████████████████  300 lines changed
Iteration 2:  ████████████████                          120 lines changed
Iteration 3:  ██████                                     40 lines changed
Iteration 4:  ██                                         10 lines changed (cosmetic only)
              ^--- Convergence reached: the diff shrinks each pass until only cosmetic changes remain
```

### Convergence indicators

| Signal | What It Means |
|--------|---------------|
| **Lines changed decreasing exponentially** | Each iteration makes roughly half the changes of the previous one |
| **Changes become trivial** | Remaining changes are formatting, comments, imports -- not behavior |
| **Tests stabilize** | Test count stops increasing; pass rate approaches 100% |
| **No new files created** | The architecture has settled; only existing files are modified |
| **Impl tracking updates shrink** | Implementation tracking changes are status updates, not new findings |
| **Completion signal emitted** | Agent determines all exit criteria are met |

### What convergence looks like in git

```bash
# Check lines changed per iteration
git log --oneline --stat

# Iteration 5: trivial changes
abc1234 Iteration 5: formatting and comment fixes
 3 files changed, 8 insertions(+), 6 deletions(-)

# Iteration 4: minor adjustments
def5678 Iteration 4: edge case handling
 5 files changed, 22 insertions(+), 8 deletions(-)

# Iteration 3: moderate changes
ghi9012 Iteration 3: complete API integration
 12 files changed, 85 insertions(+), 31 deletions(-)

# Iteration 2: significant changes
jkl3456 Iteration 2: implement core features
 18 files changed, 156 insertions(+), 42 deletions(-)

# Iteration 1: major initial work
mno7890 Iteration 1: initial implementation
 25 files changed, 312 insertions(+), 15 deletions(-)
```

---

## 2. What Is a Ceiling?

A ceiling is when the agent **cannot make further progress** due to external constraints. Like convergence, it produces small diffs -- but for fundamentally different reasons.

```
Convergence:  Agent is DONE      -> small diffs because work is complete
Ceiling:      Agent is STUCK     -> small diffs because agent cannot proceed
```

### Ceiling causes

| Cause | Example | How to Detect |
|-------|---------|---------------|
| **Missing dependency** | API not available, library not installed | Agent logs errors about unavailable resources |
| **Ambiguous spec** | Requirement can be interpreted multiple ways | Agent oscillates between implementations |
| **Tooling limitation** | Build tool does not support needed feature | Agent tries workarounds that do not converge |
| **External service** | Test requires network access, external API | Tests fail with connection/timeout errors |
| **Context window exhaustion** | Codebase too large for one session | Agent loses track of earlier work |
| **Permission boundary** | Agent cannot access needed files or systems | Repeated permission errors in logs |

### How to tell them apart

| Dimension | Convergence (work is finishing) | Ceiling (work is stuck) |
|-----------|--------------------------------|-------------------------|
| **Size of diffs** | Shrinking steadily toward zero | Staying small but not trending down |
| **Nature of changes** | Cosmetic -- whitespace, comments, naming | Functional but going in circles |
| **Test results** | Pass rate climbing toward full coverage | Pass rate plateaued below target |
| **Agent stance** | Wrapping up, marking exit criteria done | Retrying the same strategies repeatedly |
| **Tracking status** | Tasks moving to DONE | BLOCKED items piling up |
| **Recommended action** | Declare done, move to next phase | Diagnose the obstacle, resolve it, then continue |

### How to distinguish them

```
Check 1: Are tests passing?
  YES, and improving -> Convergence
  NO, stuck at same failures -> Ceiling

Check 2: Is the agent trying new approaches?
  NO, just polishing -> Convergence
  YES, but they all fail similarly -> Ceiling

Check 3: Are there BLOCKED tasks in impl tracking?
  NO -> Convergence
  YES -> Ceiling (read the blockers)

Check 4: Is the agent producing meaningful error messages?
  NO, just minor changes -> Convergence
  YES, about dependencies/tools/access -> Ceiling
```

---

## 3. Non-Convergence Signals

Non-convergence means the agent is making changes, but they are NOT decreasing. The system is not stabilizing.

```
Non-convergence:
Iteration 1:  ████████████████████████████████████████  250 lines changed
Iteration 2:  ██████████████████████████████████████    230 lines changed
Iteration 3:  ████████████████████████████████████████  260 lines changed
Iteration 4:  ██████████████████████████████████        220 lines changed
              ^--- NOT converging: changes are flat/oscillating
```

### Root causes of non-convergence

| Root Cause | Symptom | Fix |
|-----------|---------|-----|
| **Fuzzy specs** | Agent interprets requirements differently each iteration | Make specs more precise; add concrete acceptance criteria |
| **Weak validation** | Agent cannot verify correctness, so it keeps changing things | Add build/test/lint gates; strengthen acceptance criteria |
| **Fighting sub-agents** | Multiple agents change the same code in conflicting ways | Add file ownership tables; dispatch subagents via the Agent tool |
| **Contradictory requirements** | Spec A says X, spec B says not-X | Resolve contradictions in specs; add explicit priority/precedence |
| **Missing exit criteria** | Agent does not know when it is done | Add explicit exit criteria checklists and completion signals |
| **Over-broad scope** | Too much work for one prompt/iteration | Split into smaller, focused prompts with clear boundaries |
| **Unstable dependencies** | External library or API keeps changing | Pin dependencies; mock external services in tests |

### The critical rule

**When the loop isn't stabilizing, the problem is upstream -- fix the specifications, validation, or coordination rather than adding more passes.**

Running more iterations when the system is not converging wastes time and compute. Instead:
1. Stop the iteration loop
2. Analyze the non-convergence pattern
3. Fix the root cause (usually specs or validation)
4. Resume the iteration loop

---

## 4. Test Pass Rate as Convergence Signal

Test pass rate is the most reliable quantitative convergence signal. Track these metrics:

### Metrics to monitor

```
| Iteration | Tests | Pass | Fail | Skip | Pass Rate | Delta |
|-----------|-------|------|------|------|-----------|-------|
| 1         | 45    | 30   | 15   | 0    | 66.7%     | --    |
| 2         | 62    | 50   | 12   | 0    | 80.6%     | +13.9 |
| 3         | 78    | 70   | 8    | 0    | 89.7%     | +9.1  |
| 4         | 85    | 82   | 3    | 0    | 96.5%     | +6.8  |
| 5         | 88    | 87   | 1    | 0    | 98.9%     | +2.4  |
```

### What to look for

| Pattern | Meaning | Action |
|---------|---------|--------|
| **Test count increasing** | Agent is adding coverage | Good -- system is maturing |
| **Pass rate approaching 100%** | Implementation matches specs | Good -- approaching convergence |
| **Fewer failures per iteration** | Each pass fixes more than it breaks | Good -- healthy convergence |
| **Pass rate plateaus < 100%** | Some tests consistently fail | Ceiling -- investigate failing tests |
| **Test count decreasing** | Agent is deleting tests | Bad -- investigate why; may be deleting inconvenient tests |
| **Pass rate oscillating** | Fixes in one area break another | Non-convergence -- check for conflicting specs |

### Automated convergence check

```bash
# After each iteration, check convergence signals
echo "=== Convergence Check ==="

# 1. Lines changed (should be decreasing)
git diff --stat HEAD~1

# 2. Test results (should be improving)
{TEST_COMMAND} 2>&1 | tail -5

# 3. Build health (should always pass)
{BUILD_COMMAND} 2>&1 | tail -3

# 4. Files changed (should be decreasing)
git diff --name-only HEAD~1 | wc -l
```

---

## 5. Forward Progress Metrics

For large projects where full convergence takes many iterations, track forward progress toward eventual convergence.

### Spec requirement coverage

The percentage of spec requirements with passing tests:

```
Spec Requirements Coverage:
  spec-auth.md:     ██████████████████████████████████████  95% (19/20 requirements)
  spec-data.md:     ████████████████████████████████        80% (16/20 requirements)
  spec-ui.md:       ██████████████████████                  55% (11/20 requirements)
  spec-api.md:      ████████████████████████████            70% (14/20 requirements)
  ─────────────────────────────────────────────────────
  Overall:          ████████████████████████████            75% (60/80 requirements)
```

### Forward progress signals

| Metric | Healthy Trend | Unhealthy Trend |
|--------|--------------|-----------------|
| **Requirements with passing tests** | Increasing each iteration | Flat or decreasing |
| **Total test count** | Increasing | Flat or decreasing |
| **DONE tasks in impl tracking** | Increasing | Flat with BLOCKED tasks growing |
| **Open issues** | Decreasing | Increasing or flat |
| **Dead ends documented** | Increasing slightly (learning) | Exploding (thrashing) |

### Iteration velocity

Track how much progress each iteration makes:

```
| Iteration | Requirements Met | New This Iteration | Velocity |
|-----------|-----------------|-------------------|----------|
| 1         | 15/80           | 15                | 15       |
| 2         | 30/80           | 15                | 15       |
| 3         | 48/80           | 18                | 18       |
| 4         | 60/80           | 12                | 12       |
| 5         | 68/80           | 8                 | 8        |
| 6         | 73/80           | 5                 | 5        |
| 7         | 76/80           | 3                 | 3        |
```

Velocity should decrease over time (easy requirements first, hard ones last), but should never hit zero. Zero velocity = ceiling.

---

## 6. When to Stop Iterating

### Stop conditions (convergence reached)

Stop the iteration loop when ANY of these are true:

1. **Completion signal emitted:** Agent outputs `<all-tasks-complete>`
2. **Changes are trivial:** Last iteration changed fewer than ~20 lines, all formatting/comments
3. **Test pass rate is stable:** Pass rate has been 95%+ for 2+ consecutive iterations
4. **All exit criteria met:** Every `[ ]` in the exit criteria checklist is `[x]`
5. **Forward progress stalled positively:** All spec requirements have passing tests

### Continue conditions (not yet converged)

Continue iterating when ALL of these are true:

1. Changes are still substantial (behavior changes, not just formatting)
2. Test pass rate is still improving
3. There are still TODO or IN_PROGRESS tasks in impl tracking
4. The iteration count is under the maximum

### Investigate conditions (possible ceiling)

Pause and investigate when ANY of these are true:

1. Changes are small but tests are NOT passing
2. Agent is retrying the same approach repeatedly
3. BLOCKED tasks are accumulating in impl tracking
4. Test pass rate is oscillating (up-down-up-down)
5. Agent is producing error messages about dependencies or tooling

---

## 7. Monitoring During Iteration Loops

### What to monitor in real time

```
+------------------------------------------------------+
| Convergence Dashboard                                |
+------------------------------------------------------+
| Iteration: 4/10                                      |
| Lines changed: 45 (prev: 112, trend: decreasing)    |
| Files changed: 3 (prev: 8, trend: decreasing)       |
| Test pass rate: 94.2% (prev: 87.1%, trend: up)      |
| Tests: 82 total (prev: 75, trend: up)               |
| BLOCKED tasks: 0 (prev: 1, trend: down)             |
| Status: CONVERGING                                   |
+------------------------------------------------------+
```

### Monitoring commands

```bash
# Quick convergence check after each iteration
echo "--- Lines changed ---"
git diff --stat HEAD~1 | tail -1

echo "--- Files changed ---"
git diff --name-only HEAD~1 | wc -l

echo "--- Test results ---"
{TEST_COMMAND} --summary 2>&1 | tail -3

echo "--- Impl tracking status ---"
grep -c "BLOCKED\|IN_PROGRESS\|TODO\|DONE" context/impl/impl-*.md
```

### Automated alerts

Set up alerts for non-convergence signals:

| Alert | Trigger | Action |
|-------|---------|--------|
| **Oscillation** | Lines changed increased vs previous iteration | Pause; check for conflicting changes |
| **Stall** | Lines changed < 5 but tests still failing | Pause; likely a ceiling |
| **Regression** | Test pass rate decreased | Pause; investigate what broke |
| **Runaway** | Lines changed > 500 for 3+ iterations | Pause; scope may be too broad |

---

## 8. Non-Convergence Recovery

When you detect non-convergence, follow this recovery process:

### Step 1: Stop the iteration loop

Do not keep running. More iterations will not help.

### Step 2: Diagnose the root cause

```markdown
## Non-Convergence Diagnosis

### Symptoms
- [ ] Changes are flat (not decreasing)
- [ ] Changes are oscillating (up-down-up-down)
- [ ] Agent is retrying failed approaches
- [ ] Tests are oscillating (passing then failing)
- [ ] Multiple agents changing the same files

### Root Cause Analysis
1. Check specs: Are requirements clear and unambiguous?
2. Check validation: Can the agent verify correctness?
3. Check file ownership: Are agents conflicting?
4. Check scope: Is the prompt trying to do too much?
5. Check dependencies: Are external resources available?
```

### Step 3: Fix the root cause

| Root Cause | Fix |
|-----------|-----|
| Fuzzy specs | Rewrite ambiguous requirements with concrete acceptance criteria |
| Weak validation | Add build/test/lint gates to the prompt |
| File conflicts | Add file ownership tables; dispatch subagents via the Agent tool |
| Over-broad scope | Split into smaller prompts; reduce concurrent agents |
| External dependency | Mock the dependency; or resolve it before resuming |

### Step 4: Resume the iteration loop

After fixing the root cause, resume from where you stopped. Do NOT restart from scratch -- git history preserves all progress.

```bash
# Resume with the same prompt, possibly fewer remaining iterations
iteration-loop context/prompts/003-generate-impl-from-plans.md -n 5 -t 1h
```

---

## 9. Convergence and Revision

Revision directly improves convergence by making specs more complete:

```
Without revision:
  Iteration 1: 200 lines, 5 manual fixes -> specs unchanged
  Iteration 2: 180 lines, 4 manual fixes -> specs unchanged
  Iteration 3: 170 lines, 4 manual fixes -> NOT converging

With revision:
  Iteration 1: 200 lines, 5 manual fixes -> specs updated with 5 new requirements
  Iteration 2: 100 lines, 2 manual fixes -> specs updated with 2 new requirements
  Iteration 3: 50 lines, 0 manual fixes  -> CONVERGING
```

**Frequent manual fixes without revision = non-convergence.** The iteration loop keeps producing the same bugs because nothing in the specs prevents them.

---

## Cross-References

- **Convergence patterns reference:** See `references/convergence-patterns.md` for the complete convergence pattern catalog with examples.
- **Revision:** See `ck:revision` skill for how tracing bugs to specs improves convergence.
- **Prompt pipeline:** See `ck:prompt-pipeline` skill for designing prompts with proper exit criteria and completion signals.
- **Validation-first design:** See `ck:validation-first` skill for building validation gates that provide convergence signals.
- **Impl tracking:** See `ck:impl-tracking` skill for tracking progress and detecting ceiling conditions.
