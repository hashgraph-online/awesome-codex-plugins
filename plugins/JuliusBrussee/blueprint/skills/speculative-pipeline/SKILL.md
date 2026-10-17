---
name: speculative-pipeline
description: >
  A pipeline execution strategy where downstream stages start before upstream stages finish,
  using staggered timing with configurable delays. The leader begins first, and followers start
  after a delay, building from whatever partial output exists. Combined with convergence loops,
  early follower output self-corrects as upstream artifacts solidify. Cuts total pipeline time
  dramatically -- a 3-stage pipeline that takes 12 hours sequentially can finish in roughly 7 hours
  with speculative-pipeline staggering.
  Triggers: "speculative-pipeline", "staggered pipeline", "parallel prompts with delay",
  "overlap pipeline stages", "faster pipeline".
---

# Speculative-pipeline Strategy

Run pipeline stages with staggered timing instead of sequentially. The leader starts first;
followers start after a configurable delay and build from whatever upstream output exists at
that point. Combined with convergence loops, followers self-correct as upstream artifacts
arrive and stabilize.

## Core Principle

> **Start downstream work early with partial upstream output. Convergence loops correct the
> errors introduced by working from incomplete input.**

The insight is that waiting for perfect upstream output is wasteful. A follower working from
80% of the upstream artifacts will produce output that is ~60-70% correct on the first pass.
But with convergence loops running, the follower re-reads the upstream artifacts on each
iteration and corrects course. By the time the leader finishes, the follower is already
most of the way done.

---

## The Pattern

### Sequential (Traditional)

```
Stage 1: Specs     ████████████████████                          (5 hours)
Stage 2: Plans                         ████████████████          (4 hours)
Stage 3: Implement                                     ████████  (3 hours)
                   ─────────────────────────────────────────────
                   Total: 12 hours
```

### Speculative-pipeline (Staggered)

```
Stage 1: Specs     ████████████████████                          (5 hours)
Stage 2: Plans            ████████████████                       (4 hours, started 1.5h after Stage 1)
Stage 3: Implement              ████████████                     (3 hours, started 3h after Stage 1)
                   ─────────────────────────────────────────────
                   Total: ~7 hours
```

### Why It Works

1. **Stage 2 starts after a 1.5-hour offset.** By then, Stage 1 has produced a meaningful set of partial specs.
2. **Stage 2 generates plans from whatever specs are available.** Some plans will be built on incomplete information.
3. **Stage 1 keeps refining specs.** When Stage 2 loops back for its next pass, it picks up
   the newly completed specs and adjusts its plans accordingly.
4. **Stage 3 starts after a 3-hour offset.** By then, both specs and plans exist in draft form.
5. **All stages self-correct through iteration.** Each pass re-reads the latest upstream artifacts. Mistakes caused
   by working from partial input are washed out on subsequent passes.

The key mechanism is **convergence** -- the iterative loop that re-reads inputs each pass. Without
convergence loops, speculative-pipeline would produce garbage. With them, early errors wash out over
iterations.

---

## Example: 3-Stage Pipeline

### Directory Structure

```
context/
├── specs/              # Stage 1 output: implementation-agnostic specs
├── plans/              # Stage 2 output: framework-specific plans
├── impl/               # Stage 3 output: implementation tracking
└── prompts/
    ├── 001-generate-specs.md       # Stage 1 prompt
    ├── 002-generate-plans.md       # Stage 2 prompt
    └── 003-implement.md            # Stage 3 prompt
```

### Terminal Commands

Open three terminal windows (or use tmux panes):

```bash
# Terminal 1: Specs from reference materials (leader -- starts immediately)
{LOOP_TOOL} context/prompts/001-generate-specs.md -n 5 -t 2h

# Terminal 2: Plans from specs (follower -- starts after 1-hour delay)
{LOOP_TOOL} context/prompts/002-generate-plans.md -n 5 -t 2h -d 1h

# Terminal 3: Implementation from plans (follower -- starts after 2-hour delay)
{LOOP_TOOL} context/prompts/003-implement.md -n 10 -t 1h -d 2h
```

**Parameter reference:**
- `-n 5` -- Run up to 5 convergence iterations
- `-t 2h` -- Time budget per iteration (max total time = iterations x budget)
- `-d 1h` -- Delay before starting (speculative-pipeline offset)

Replace `{LOOP_TOOL}` with your convergence loop runner (any script or tool that repeatedly
executes a prompt against the codebase, committing between iterations).

### What Happens Chronologically

| Time | Stage 1 (Specs) | Stage 2 (Plans) | Stage 3 (Implement) |
|------|-----------------|-----------------|---------------------|
| 0:00 | Starts. Reads refs, begins generating specs. | Waiting (1.5h delay). | Waiting (3h delay). |
| 1:30 | Iteration 1 complete. ~50% of specs written. Committed. | Starts. Reads partial specs, begins generating plans. | Waiting. |
| 3:00 | Iteration 2. Specs ~80% complete. | Iteration 1 complete. Plans based on partial specs. Some plans will need correction. | Starts. Reads partial specs + plans, begins implementing. |
| 4:00 | Iteration 3. Specs ~92% complete, converging. | Iteration 2. Re-reads updated specs. Corrects plans. Plans ~65% correct. | Iteration 1 complete. Some implementation based on incomplete plans. |
| 5:00 | Converged. Specs complete. Done. | Iteration 3. Re-reads final specs. Plans ~88% correct. | Iteration 2. Re-reads corrected plans. Fixes implementation. |
| 5:30 | -- | Iteration 4. Plans converged. Done. | Iteration 3. Implementation ~75% correct. |
| 7:00 | -- | -- | Iteration 4-5. Implementation converges. Done. |

**Result: ~7 hours total versus ~12 hours sequential.**

---

## Choosing Delay Values

The delay determines how much upstream work exists when the follower starts. Too short and the
follower wastes iterations on garbage input. Too long and you lose the time savings.

### Guidelines

| Upstream Stage Duration | Recommended Delay | Rationale |
|------------------------|-------------------|-----------|
| 1-2 hours | 15-30 minutes | Short stages produce useful partial output quickly |
| 2-4 hours | 1 hour | Enough time for the first iteration to complete and commit |
| 4+ hours | 1-2 hours | First iteration should have substantial output |

### Rules of Thumb

1. **Delay >= 1 upstream iteration.** The follower should not start until the leader has completed
   at least one full iteration and committed results.
2. **Delay < 50% of upstream duration.** If the delay is longer than half the upstream time, the
   time savings are marginal.
3. **More follower iterations compensate for shorter delays.** If you start the follower early
   (aggressive delay), give it more iterations to converge.

---

## Multi-Stage Pipelines (4+ Stages)

For pipelines with more than 3 stages, stagger each stage relative to Stage 1:

```bash
# 5-stage pipeline example
{LOOP_TOOL} {PROMPT_001} -n 5 -t 2h           # Stage 1: starts immediately
{LOOP_TOOL} {PROMPT_002} -n 5 -t 2h -d 1h     # Stage 2: 1h delay
{LOOP_TOOL} {PROMPT_003} -n 8 -t 1h -d 2h     # Stage 3: 2h delay
{LOOP_TOOL} {PROMPT_004} -n 8 -t 1h -d 3h     # Stage 4: 3h delay
{LOOP_TOOL} {PROMPT_005} -n 10 -t 45m -d 4h   # Stage 5: 4h delay
```

**Notice the pattern:**
- Later stages get **more iterations** (they need more correction cycles)
- Later stages get **shorter time budgets per iteration** (less work per stage)
- Delays increase linearly (each stage offset by roughly 1 hour)

---

## When Speculative-pipeline Works Best

### Good Fit

- **Long pipelines (3+ stages):** The time savings scale with pipeline depth
- **Stages that share a git repo:** Followers read upstream commits automatically
- **Stages with convergence loops:** The self-correction mechanism is essential
- **Specs that are mostly stable after 1-2 iterations:** Partial specs are useful early

### Poor Fit

- **Stages with hard dependencies:** If Stage 2 literally cannot start without Stage 1's
  complete output (e.g., code generation that requires a fully resolved type system), the
  follower will produce only errors
- **Single-iteration stages:** Without convergence loops, there is no self-correction
- **Very short pipelines (2 stages, <1 hour each):** The overhead of staggering is not
  worth the small time savings

---

## Monitoring Speculative-pipeline Execution

### What to Watch

1. **Follower diff sizes per iteration.** If the follower's diffs are large on every iteration
   (not decreasing), it is thrashing -- the delay was too short or the upstream output is
   too unstable.
2. **Follower convergence rate.** The follower should converge within 1-2 iterations of the
   leader finishing. If it takes many more, the stages may have a hard dependency.
3. **Git commit frequency.** Both leader and follower should be committing regularly. If commits
   stall, the agent may be stuck.

### Convergence Signals

A speculative-pipeline pipeline has converged when:
- All stages have completed their iteration loops
- The final iteration of each stage produces minimal diffs
- Build and test gates pass on the merged output

### Thrashing Detection

**Thrashing** = the follower keeps making large changes because upstream output keeps changing.

Signs of thrashing:
- Follower diff sizes do not decrease across iterations
- Follower reverts changes it made in previous iterations
- Build failures increase instead of decreasing

**Fix thrashing by:**
1. Increasing the delay (give the leader more time to stabilize)
2. Reducing follower iterations (let upstream settle first)
3. Adding a "wait for upstream convergence" gate between stages

---

## Combining with Agent Teams

In multi-agent setups, speculative-pipeline applies at the pipeline level, not the agent team level:

```
Pipeline Level (speculative-pipeline timing):
  Stage 1 (Specs)     → Single agent or agent team
  Stage 2 (Plans)     → Single agent or agent team (starts after delay)
  Stage 3 (Implement) → Agent team dispatched via Agent tool (starts after delay)
```

Each stage can internally use agent teams (multiple teammates working in parallel on different
domains), but the *stages themselves* are staggered using speculative-pipeline timing.

**Do not confuse:**
- **Leader-follower:** Pipeline stages overlapping in time
- **Agent teams:** Multiple agents working in parallel within a single stage

They are orthogonal and composable.

---

## Implementation Checklist

When setting up a speculative-pipeline pipeline:

- [ ] Define the pipeline stages (typically: specs, plans, implement)
- [ ] Create a prompt file for each stage with explicit input/output directories
- [ ] Ensure each stage reads from upstream directories and writes to its own directory
- [ ] Configure convergence loop for each stage with appropriate iteration counts
- [ ] Choose delays: first follower at ~1 upstream iteration, subsequent at ~1h increments
- [ ] Set up terminal sessions (one per stage) or use tmux
- [ ] Monitor: watch for convergence (decreasing diffs) vs thrashing (constant large diffs)
- [ ] After all stages complete, run full build + test validation on the merged output

---

## Cross-References

- **prompt-pipeline** -- How to design the prompt files that each stage executes
- **convergence-monitoring** -- How to detect convergence vs ceiling in each stage
- **methodology** -- Where speculative-pipeline fits in the Hunt lifecycle
- **validation-first** -- Validation gates that run after each stage completes
- **context-architecture** -- Directory structure that stages read from and write to
