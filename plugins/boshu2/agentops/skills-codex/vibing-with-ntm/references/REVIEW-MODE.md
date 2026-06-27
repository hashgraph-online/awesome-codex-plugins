# Review-Only Mode

<!-- TOC: When To Use | Architecture | Spawn | Mixed Swarms | Phase 1 Dispatch | Phase 2 Monitoring | Phase 3 Kill+Relaunch | Quality Rubric | File Conventions | Severity Tagging | Termination | Mode Switch | Anti-Patterns | vs Gemini Skill | Quick Reference -->

## Contents

- When to run reviewer panes instead of implementers
- Spawn patterns, dispatch sequence, and monitoring cadence
- Quality rubric, severity tags, and output conventions
- Termination and mixed-swarm mode switching

A specialized operational shape of `vibing-with-ntm` in which agents are pure auditors: they explore, find bugs, fix them, and cross-review each other's work. They do NOT pick beads, claim ready work, or do feature implementation.

This mode generalizes the Gemini-swarm review pattern (see `/code-review-gemini-swarm-with-ntm` for model-specific tuning) — but works equally well with `cc`, `cod`, `gmi`, or any mix.

## When To Use Review-Only Mode

- Codebase is feature-complete; you want to harden it with deep audits before a release.
- Implementers have been working for ≥15-20 min; now you want a second opinion.
- You've just merged a big refactor and need eyes on it.
- You're running a mixed swarm and want some panes to focus on quality, not throughput.

## Architecture (agent-agnostic)

```
Round loop:
  ┌─── P1 (study) ────┐
  │                   │
  │  ┌─ P2 (explore) ─┐
  │  │                │
  │  │  ┌─ P3 (cross-review) ─┐
  │  │  │                     │
  │  │  │  ┌─ P4 (continue) ──┐
  │  │  │  │                  │
  │  │  │  └── repeat P2-P4 ×2 more times ──┘
  │
  ├── end of round: kill + relaunch all panes ──┘
```

**Per agent per round: 7 prompts total** (1 study + 3×explore+cross-review, with 2 continuation nudges between iterations). Exploits prompt caching — the agent already has the codebase loaded after the first prompt.

**Between rounds: kill and relaunch.** Context freshness matters more than any one pane's state. After 2-3 explore passes on the same codebase, agents start narrating rather than reviewing — the kill-relaunch cycle resets them.

## Spawning A Review-Only Swarm

```bash
# Pure review (no implementation)
ntm spawn $PROJECT --cc=3 --cod=2 --no-user --stagger-mode=smart
#   or --gmi=N if you want Gemini-only (see /code-review-gemini-swarm-with-ntm)

# Wait for all agents to be ready
ntm --robot-wait=$PROJECT --wait-until=idle --timeout=2m
```

Then immediately dispatch P1 to all panes. See "Phase 1: Dispatch" below.

## Mixed Implementation + Review Swarms

You can run reviewers alongside implementers in the same session. Recommended ratios from real sessions:

| Swarm Size | Implementer (cc/cod) | Reviewer |
| --- | --- | --- |
| Small (6)  | 5 | 1 |
| Medium (14) | 10 | 4 |
| Large (24) | 20 | 4 |

Reviewers scale sub-linearly — they cover the same codebase, so more reviewers yields diminishing returns. 4 is typically sufficient even for large swarms.

**Timing.** Start reviewers 15-20 min AFTER implementers begin. Reviewing an empty or barely-started codebase wastes the reviewer's context.

**Coordination rules (reviewers only):**

- Reviewers do NOT register with MCP Agent Mail (avoids communication purgatory — see OC-007/AP-19)
- Reviewers do NOT pick beads from bv (not implementers)
- Reviewers DO read `git log` and `git diff` to find recent changes by other panes
- Reviewers DO run tests/linters after making fixes
- Implementers should expect that reviewers may revise their code

To enforce this, put it in the reviewer's initial marching orders:

```text
You are pane <N>, running in REVIEW-ONLY MODE.
- Do NOT register with MCP Agent Mail.
- Do NOT claim beads from bv or br.
- DO explore the codebase deeply, find bugs, fix them, and verify.
- DO read git log / git diff to understand recent implementer activity.
- DO run the repo's verify commands after every fix.
```

## Phase 1: Dispatch (per round)

### Core prompt sequence

All prompts are in PROMPTS.md under "Review-Only Mode Prompts." The four core ones:

- **P1 (Study)** — sent once per round, to every pane. Agent reads AGENTS.md, README.md, and builds mental model.
- **P2 (Explore + Fresh-Eyes Review)** — sent 3× per round. Agent picks files, traces execution, finds bugs, fixes them.
- **P3 (Cross-Review)** — sent 3× per round, after each P2. Agent reviews OTHER agents' recent changes. Critical: always prefix with "Reread AGENTS.md" so repo rules stay fresh.
- **P4 (Continuation Nudge)** — between iterations. Short, context-cheap. Pushes the agent into unexplored territory.

### Sequence patterns

| Pattern | Prompt chain | When |
| --- | --- | --- |
| **Standard** | P1 → P2 → P3 → P4 → P2 → P3 → P4 → P2 → P3 | Default; works for most codebases |
| **Deep Dive** | P1 → P2 → P2 → P3 → P4 → P2 → P2 → P3 → P-verify | Large codebases where one explore can't cover meaningful ground |
| **Quick Audit** | P1 → P2 → P3 | Small codebases (<5K lines); single pass |
| **Post-Refactor** | P1 → P3 (with commit range) → P-verify | Focused audit on a specific commit range |

### Dispatch loop (async per-agent)

Track each pane's position in the sequence. Agents advance ASYNCHRONOUSLY — faster panes get their next prompt sooner; do NOT wait for the slowest.

```bash
# Sketch: per-pane state tracked in /tmp/review-state-$PROJECT.json
# Each tick: for each idle pane, send its next prompt and update state

for pane in $(ntm --robot-is-working=$PROJECT | jq -r '.panes[] | select(.is_idle) | .pane'); do
  step=$(jq -r ".pane_${pane}" /tmp/review-state-$PROJECT.json)
  next=$(compute_next_step "$step")            # P1→P2, P2→P3, P3→P4, P4→P2, etc.
  ntm --robot-send=$PROJECT --panes=$pane --msg="$(cat prompts/$next.txt)"
  jq ".pane_${pane} = \"$next\"" /tmp/review-state-$PROJECT.json > /tmp/.new && mv /tmp/.new /tmp/review-state-$PROJECT.json
done
```

See CRON-AND-AUTOMATION.md for the full cron pattern — this is a specialization of the canonical operator loop.

## Phase 2: Monitoring Heartbeat

Every 3 minutes (use `CronCreate` or `/loop 3m`), do one tick:

1. `ntm --robot-is-working=$PROJECT` — real per-pane state
2. `ntm --robot-tail=$PROJECT --lines=80` — read what reviewers are actually finding
3. For any idle pane, dispatch its next prompt per the sequence
4. For any rate-limited pane, rotate (see OC-002) or retire
5. **Critically assess review quality** — see rubric below

### Why 3 minutes

- Review sessions take 2-5 min per prompt on average
- Any polling more frequent wastes tokens
- Any longer misses the idle→dispatch window and panes sit empty

## Phase 3: Kill + Relaunch (end of round)

Trigger: ALL panes have completed their 7-prompt sequence OR been retired.

```bash
# 1. Capture final state of this round
ntm --robot-tail=$PROJECT --lines=200 > "/tmp/review-round-${ROUND}-tail.log"
ls -la *REVIEW*.md *FIXES*.md *FINDINGS*.md 2>/dev/null

# 2. Check for early-exit convergence
#    If ALL active panes report "no issues found" on their last cross-review pass → stop
convergence_signal=$(ntm --robot-tail=$PROJECT --lines=50 | grep -cE "no issues|no fixes needed|clean|already complete|ready to ship")
active=$(ntm --robot-is-working=$PROJECT | jq '[.panes[] | select(.is_working or .is_idle)] | length')
if [ "$convergence_signal" -ge "$active" ]; then
  echo "CONVERGED — review complete"; exit 0
fi

# 3. Kill + relaunch all reviewer panes for next round
ntm --robot-restart-pane=$PROJECT --type=cc   # or --type=cod, --type=gmi depending on pool
ntm --robot-wait=$PROJECT --wait-until=idle --timeout=2m

# 4. Start next round at P1
```

## Quality Assessment Rubric

After every cron tick, rate each pane's last output:

| Signal in tail | Quality | Action |
| --- | --- | --- |
| Names specific files, line numbers, root causes | **High** | Keep running |
| Finds and fixes real bugs with verification (tests/lint) | **High** | Keep running |
| Explores deeply but finds nothing, with reasoning | Medium | Acceptable for clean codebases |
| Narrates code structure without concrete findings | **Low** | One more pass, then kill & relaunch |
| Repeats findings from previous iteration | **Low** | Kill immediately |
| Produces structured `*REVIEW*.md` / `*FIXES*.md` | **High** | Read file for findings |
| Attempts to delete its own tracking files | Normal | No-deletion rule blocks it (per AGENTS.md rule #1); ignore |
| Gets stuck on Agent Mail coordination | **Fail** | Should not happen — reviewer was supposed to skip Mail |

### What good output looks like

```
**Bug: Flawed .jsonl Provider Inference Logic (src/discovery.rs:48)**
- Issue: `infer_provider_for_path` uses `?` operator on `serde_json::from_str().ok()?`.
  If the first non-empty line is not valid JSON, the function exits with None.
  Also the loop has unconditional break, so it only ever checks one line.
- Fix: Rewrote the JSONL parser loop to gracefully continue on non-JSON lines
  and scan up to 50 valid JSON lines for a provider signature.
- Verified: cargo test -p discovery passes; cargo clippy clean.
```

Named file, line number, root cause, patched, verified. This is the standard.

### What bad output looks like (noise)

```
I reviewed src/main.rs. The code looks well-structured.
The error handling follows Rust best practices.
I don't see any obvious issues.
Moving on to the next file.
```

This is narration, not review. If you see this pattern on iteration 2+, the pane has exhausted its usefulness on this codebase — kill and relaunch.

## Review Output File Conventions

Reviewers naturally produce tracking artifacts during work. Agent-agnostic naming (generalized from Gemini's convention):

| File | Purpose |
| --- | --- |
| `REVIEW_SUMMARY.md` or `<AGENT>_REVIEW_SUMMARY.md` | Per-agent review findings summary |
| `FIXES.md`, `FIXES_2.md`, `FIXES_3.md` | Numbered fix logs across iterations |
| `FINAL_REPORT.md` or `<AGENT>_FINAL_REPORT.md` | Consolidated findings for the round |
| `STATUS.md` or `<AGENT>_STATUS.md` | Self-tracked progress |
| `SESSION_TODO.md` | Cross-agent shared TODO with per-pane numbered sections |

When ingesting a round, check these files — they often contain structured findings that don't appear in the tail.

**Do NOT instruct reviewers to delete these files.** AGENTS.md rule #1 (no deletions without permission) typically blocks self-cleanup. If your AGENTS.md doesn't have this rule, reviewers may garbage-collect their own artifacts; add the rule before running a review swarm.

## Bug Severity Tagging

Encourage reviewers to tag findings in their output for easy grepping:

```
[CRITICAL] use-after-free in src/cache.rs:201
[HIGH]     unwrap on Option in hot path crates/io/src/read.rs:87
[MEDIUM]   TODO without tracking bead in src/config.rs:42
[LOW]      debug println! left in src/util.rs:15
```

Reviewers can be prompted to emit this tag format via P-summary (see PROMPTS.md).

## Termination Conditions

Stop the whole review loop when ANY of:

1. `MAX_ROUNDS` completed (default 10)
2. All panes rate-limited or offering fallback models — no one left to work
3. Convergence: ALL active panes report clean on their last cross-review
4. Human interrupt

Always cancel the monitoring cron (`CronDelete`) before ending.

## Merging With Implementation Mode

You can flip a pane between implementation and review modes mid-session:

```bash
# Convert pane 3 from implementer to reviewer
ntm --robot-send=$PROJECT --panes=3 --msg="MODE SWITCH: You are now a REVIEWER. Do not claim new beads. Begin with P1 (study), then P2 (explore + review), then P3 (cross-review). See /vibing-with-ntm references/REVIEW-MODE.md."

# Or the reverse — flip a reviewer to implementer
ntm --robot-send=$PROJECT --panes=3 --msg="MODE SWITCH: You are now an IMPLEMENTER. Register with Agent Mail, pick the top ready bead from bv, claim it, reserve files, ship a commit within 60 min."
```

Never silently mix modes in one pane — always announce the switch.

## Review-Specific Anti-Patterns

### AP-R1: Superficial Reviews After Many Iterations

**Symptom.** Tick 4+ produces "I reviewed foo.rs, looks well-structured" for every file.

**Fix.** Kill + relaunch at end of round. Three iterations per round is the natural limit before diminishing returns.

### AP-R2: Context Drift On Cross-Review

**Symptom.** Reviewer makes changes that violate AGENTS.md conventions (e.g. adds `unwrap()` in a no-unwrap codebase).

**Fix.** Always prefix P3 with "Reread AGENTS.md so it is still fresh in your mind." Not optional.

### AP-R3: Reviewer Registers Agent Mail And Gets Stuck

**Symptom.** Reviewer pane spends ticks 2-5 reading/writing mail instead of reviewing code.

**Fix.** Initial marching orders must include explicit "Do NOT register with MCP Agent Mail" directive. See `Phase 1: Dispatch` above.

### AP-R4: Reviewers Pick Beads And Compete With Implementers

**Symptom.** Reviewer claims a bead from bv; implementer sees bead already claimed; two panes duplicate work.

**Fix.** Initial marching orders must include explicit "Do NOT claim beads from bv or br."

### AP-R5: Kill-Relaunch Skipped, Diminishing Returns Accepted

**Symptom.** Same panes running 10+ iterations; output getting shallower; operator doesn't restart.

**Fix.** Strict end-of-round restart. The 3-round context reset is part of the design, not optional.

### AP-R6: No Early-Exit On Convergence

**Symptom.** Reviewers reported clean on round 2; operator runs rounds 3-10 anyway; wasted 80%+ of the budget.

**Fix.** Check convergence signal at end of every round. See Phase 3 snippet.

## How This Differs From `/code-review-gemini-swarm-with-ntm`

| Aspect | This skill (Review-Mode in vibing-with-ntm) | `/code-review-gemini-swarm-with-ntm` |
| --- | --- | --- |
| Agent type | Any (cc, cod, gmi, or mix) | Gemini-only |
| Flash/fallback detection | Generic rate-limit + fallback-model detection | Exact Gemini string match ("Switched to fallback model gemini-3-flash-preview") |
| Model lock setup | Handled by `caam` / `ntm rotate` per pool | Requires `~/.gemini/settings.json` + CLI args |
| Integration | First-class part of vibing-with-ntm; seamless mode switch | Standalone specialist skill |
| Prompt tuning | Agent-neutral (works for Claude/Codex/Gemini) | Gemini-optimized phrasing |

**When to use which:**

- **Pure Gemini review swarm** → `/code-review-gemini-swarm-with-ntm` (has the model-specific knobs)
- **Review with cc/cod, or mixed implementation+review** → this REVIEW-MODE.md
- **Specific bug-hunt round inside a running implementation swarm** → this REVIEW-MODE.md's "Phase 1" dispatch prompts only

## Quick Reference: Spawn, Dispatch, Tend, Close

```bash
# Spawn
ntm spawn $PROJECT --cc=3 --cod=2 --no-user --stagger-mode=smart
ntm --robot-wait=$PROJECT --wait-until=idle --timeout=2m

# Dispatch P1 to all (initial study)
ntm send $PROJECT --all --skip-first --no-cass-check "$(cat prompts/p1-study.txt)"

# Start the 3-min monitoring loop (via CronCreate or /loop 3m — see CRON-AND-AUTOMATION.md)

# Kill + relaunch between rounds
ntm --robot-restart-pane=$PROJECT --type=cc
# (repeat for cod, gmi as applicable)
ntm --robot-wait=$PROJECT --wait-until=idle --timeout=2m

# Close swarm when converged
CronDelete $JOB_ID
ntm --robot-markdown --md-compact > "review-$PROJECT-final.md"
ls *REVIEW*.md *FIXES*.md *FINAL_REPORT*.md 2>/dev/null   # collect artifacts
# Do NOT ntm kill — leave session for user to inspect
```
