# Cycle History Format and Recovery Protocol

## Compaction Resilience

The evolve loop MUST survive context compaction. Every productive cycle appends
to its ledger artifacts before proceeding. `cycle-history.jsonl` is the
on-disk recovery point for cycle numbering, and `.agents/evolve/session-state.json`
is the on-disk resume point for pending queue claims, queue refresh count, and
generator-empty streaks.

### Local-Only Status (Not Git-Tracked)

Both `cycle-history.jsonl` and `session-state.json` are **local-only files**.
The repository's nested `.agents/.gitignore` denies all paths via `*` (with
only `!.gitignore` re-allowed), which overrides the outer `.gitignore`
allowlists at the repo root. Aspirational allowlist entries for
`!/.agents/evolve/cycle-history.jsonl` and `!/.agents/evolve/session-state.json`
exist in the outer `.gitignore` but have no effect because the nested
deny wins per gitignore precedence rules.

Implication for the cycle protocol:

- These files survive **session compaction** (recovered from disk on the next
  invocation), but they do **not** survive cloning or shared with peers.
- Important per-cycle milestones (e.g. baseline-capture results, regression
  events, convergence-criterion transitions) MUST also be recorded in
  **commit messages** so they remain in tracked git history.
- Do not depend on cycle-history.jsonl as a cross-clone authoritative ledger.
  Treat it as a session journal that helps the next-cycle bootstrap.

## Cycle History JSONL Format

Append one line per cycle to `.agents/evolve/cycle-history.jsonl`.

### Canonical Schema

All new entries MUST use this schema:

```json
{
  "cycle": 123,
  "target": "goal-id-or-idle",
  "result": "improved|regressed|unchanged|harvested|quarantined",
  "sha": "abc1234",
  "canonical_sha": "abc1234",
  "timestamp": "2026-02-23T12:00:00-05:00",
  "goals_passing": 59,
  "goals_total": 59
}
```

**Field standardization:**
- Use `target` (not `goal_id`) — this is what recent cycles already use
- Use `sha` as the compatibility alias for `canonical_sha`
- Use `canonical_sha` for the implementation commit the cycle actually delivered
- Use `log_sha` only when the bookkeeping/log commit is distinct from `canonical_sha`
- Always include `goals_passing` and `goals_total` — enables trajectory plotting
- Optional fields: `quality_score` (quality mode), `idle_streak` (idle cycles), `parallel` + `goal_ids` (parallel mode)

**Legacy field names:** Older entries may use `goal_id` instead of `target` and `commit_sha` instead of `sha`. Tools reading cycle-history.jsonl should handle both conventions.

**Sequential cycle entry:**
```jsonl
{"cycle": 1, "target": "test-pass-rate", "result": "improved", "sha": "abc1234", "canonical_sha": "abc1234", "goals_passing": 18, "goals_total": 23, "timestamp": "2026-02-11T21:00:00Z"}
{"cycle": 2, "target": "doc-coverage", "result": "regressed", "sha": "def5678", "canonical_sha": "def5678", "log_sha": "fedcba9", "goals_passing": 17, "goals_total": 23, "timestamp": "2026-02-11T21:30:00Z"}
```

**Idle cycle entry** (not committed to git):
```jsonl
{"cycle": 3, "target": "idle", "result": "unchanged", "timestamp": "2026-02-11T22:00:00Z"}
```

**Parallel cycle entry** (use `goal_ids` array and `parallel: true`):
```jsonl
{"cycle": 4, "goal_ids": ["test-pass-rate", "doc-coverage", "lint-clean"], "result": "improved", "sha": "ghi9012", "goals_passing": 22, "goals_total": 23, "parallel": true, "timestamp": "2026-02-11T22:30:00Z"}
```

### Mandatory Fields

Every productive cycle log entry MUST include:

| Field | Description |
|-------|-------------|
| `cycle` | Cycle number (1-indexed) |
| `target` | Target goal ID, or `"idle"` for idle cycles |
| `result` | One of: `improved`, `regressed`, `unchanged`, `harvested`, `quarantined` |
| `sha` | Compatibility alias for the implementation SHA (omitted for idle cycles) |
| `canonical_sha` | Implementation commit the cycle actually delivered |
| `goals_passing` | Count of goals with result "pass" (omitted for idle cycles) |
| `goals_total` | Total goals measured (omitted for idle cycles) |
| `timestamp` | ISO 8601 timestamp |

`log_sha` is optional and should only be written when the log/bookkeeping commit
differs from `canonical_sha`. These fields enable fitness trajectory plotting
without losing retrospective provenance.

### XP/BDD/TDD Evidence Trace (optional `trace` object)

A productive cycle MAY record a `trace` object capturing the
continuous-evolution kernel — the evidence a reviewer needs to reconstruct
the cycle **without reading the transcript**. The kernel shape is:

> goal hypothesis → selected gap → Gherkin scenario → first failing proof →
> red evidence → green evidence → refactor note → validation evidence →
> ratchet action → goal reshape decision

```json
{
  "cycle": 200,
  "target": "test-pass-rate",
  "result": "improved",
  "sha": "abc1234",
  "canonical_sha": "abc1234",
  "goals_passing": 60,
  "goals_total": 60,
  "timestamp": "2026-05-16T12:00:00Z",
  "trace": {
    "goal_hypothesis": "raising test-pass-rate lifts overall fitness",
    "selected_gap": "loop cycle ledger carries no evidence trace",
    "gherkin": "Feature: trace\n  Scenario: reviewer reconstructs a cycle",
    "first_failing_proof": "go test ./internal/ports -run TraceCompleteness  # FAIL",
    "red_evidence": "TestTraceCompleteness_FullTraceIsComplete red: undefined CycleTrace",
    "green_evidence": "TestTraceCompleteness_* pass (5/5)",
    "refactor_note": "extracted requiredTraceFields table; no behavior change",
    "validation_evidence": "cd cli && go test ./... green; bats evolve-log-cycle.bats 10/10",
    "ratchet_action": "ao ratchet record implement",
    "goal_reshape": "goal unchanged; gap closed — fold trace into next epic's audit"
  }
}
```

**Trace fields** (all strings, all `omitempty`):

| Field | Records |
|-------|---------|
| `goal_hypothesis` | The goal/fitness hypothesis the cycle is testing |
| `selected_gap` | The specific gap chosen from the queue/generator |
| `gherkin` | The Given/When/Then scenario the slice satisfies |
| `first_failing_proof` | The command/assertion that fails before the change |
| `red_evidence` | Observed failing-test output (the RED state) |
| `green_evidence` | Observed passing-test output (the GREEN state) |
| `refactor_note` | The refactor step — record `"none"` when there is none |
| `validation_evidence` | Independent validation commands and their results |
| `ratchet_action` | The `ao ratchet record …` action taken |
| `goal_reshape` | Whether the goal stayed, narrowed, or was replaced |

**Trivial-cycle exemption.** A tiny one-shot bookkeeping change (a typo fix,
a dependency bump) does NOT need full BDD/TDD ceremony. Instead of silently
omitting the trace fields, record an explicit `exemption_reason`:

```json
{"cycle": 201, "target": "idle", "result": "unchanged", "timestamp": "...",
 "trace": {"exemption_reason": "trivial one-shot typo fix; no Gherkin or failing proof appropriate"}}
```

A trace with a non-empty `exemption_reason` is **exempt** — no other field is
expected. A trace with neither `exemption_reason` nor the evidence fields is
**incomplete**: `ports.TraceCompleteness` (Go) reports which required fields
are missing.

**Completeness is advisory, never blocking.** `TraceCompleteness` is a pure
helper for reports and audits; it is deliberately NOT wired into
`ao loop verify` or `scripts/check-evolve-cycle-logging.sh`. The `trace`
object is recorded as-is. This keeps the loop honest about its own evidence
without making loop-shape a hard gate before real cycle output conforms.

**Writing a trace.** Both writers accept it:

```bash
# canonical script writer — file path, inline JSON, or - for stdin
bash scripts/evolve-log-cycle.sh --cycle "$CYCLE" --target "$TARGET" \
  --result improved --canonical-sha "$SHA" --cycle-start-sha "$START" \
  --goals-passing "$P" --goals-total "$T" --trace-json cycle-trace.json

# typed BC3 LoopWriterPort
ao loop append --mode evolve --result improved --trace-json cycle-trace.json
```

`ao loop history` emits the `trace` object back as part of each `CycleEntry`,
so the report surface carries the evidence with no extra step.

### Session-State Sidecar

Persist the non-ledger loop state to `.agents/evolve/session-state.json`:

```json
{
  "cycle": 124,
  "generator_empty_streak": 1,
  "last_selected_source": "testing",
  "queue_refresh_count": 17,
  "claimed_work": {
    "ref": "source_epic=ag-123:item=Add smoke test",
    "claimed_by": "evolve:cycle-124",
    "claimed_at": "2026-03-08T10:15:00Z"
  }
}
```

On resume:
1. recover `cycle` from `cycle-history.jsonl`
2. recover generator and claim state from `session-state.json`
3. if `claimed_work` exists, inspect the queue entry:
   - if the prior cycle succeeded, finalize it as consumed
   - if the prior cycle failed or is ambiguous, release the claim and continue

### Substantive-Delta Rule

Do not record `result: "improved"` when a cycle produces no non-agent repo delta.
If the cycle touched only `.agents/` artifacts or otherwise made no substantive
repo change, rewrite the outcome to `unchanged` and keep it local-only. This
prevents ledger churn from being misread as product progress.

### Telemetry

Log telemetry at the end of each cycle:
```bash
bash scripts/log-telemetry.sh evolve cycle-complete cycle=${CYCLE} score=${SCORE} goals_passing=${PASSING} goals_total=${TOTAL}
```

### Compaction-Proofing: Commit After Productive Cycles

Only **productive cycles** (improved, regressed, harvested) are committed. Idle
cycles are appended to cycle-history.jsonl locally but NOT committed — they are
disposable if compaction occurs, and the idle streak is re-derived from disk at
session start. Producer-layer exhaustion is tracked in `session-state.json`, not
by stopping early.

```bash
# Productive cycle: log via the canonical writer, then commit
bash scripts/evolve-log-cycle.sh \
  --cycle "$CYCLE" \
  --target "$TARGET" \
  --result "$OUTCOME" \
  --canonical-sha "$(git rev-parse --short HEAD)" \
  --cycle-start-sha "$CYCLE_START_SHA" \
  --goals-passing "$PASSING" \
  --goals-total "$TOTAL"

# Parallel productive cycle:
bash scripts/evolve-log-cycle.sh \
  --cycle "$CYCLE" \
  --target "parallel-wave" \
  --goal-ids "${goal_ids_csv}" \
  --parallel \
  --result "$OUTCOME" \
  --canonical-sha "$(git rev-parse --short HEAD)" \
  --goals-passing "$PASSING" \
  --goals-total "$TOTAL"

# Idle or no-delta cycle: append locally, do NOT commit
bash scripts/evolve-log-cycle.sh --cycle "$CYCLE" --target "idle" --result "unchanged" >/dev/null
# No git add, no git commit
```

### 60-Minute Circuit Breaker

At session start (Step 0), after recovering the idle streak, check the timestamp
of the last productive cycle. If it was more than 60 minutes ago, go directly to
Teardown. This prevents runaway sessions that accumulate empty queue/generator
passes without producing value.

```bash
LAST_PRODUCTIVE_TS=$(grep -v '"idle"\|"unchanged"' .agents/evolve/cycle-history.jsonl 2>/dev/null \
  | tail -1 | jq -r '.timestamp // empty')
# If >3600s since last productive cycle AND timestamp parsed correctly: CIRCUIT BREAKER → Teardown
# Guard: LAST_EPOCH > 1e9 prevents false trigger on date parse failure
```

## Recovery Protocol

On session restart or after compaction:

1. Read `.agents/evolve/cycle-history.jsonl` to find last completed cycle number
2. Set `evolve_state.cycle` to last cycle + 1
3. Resume from Step 1 (kill switch check)
4. Preserve existing `.agents/evolve/fitness-baselines/goals-<hash>/` directories; do not regenerate the current era baseline if its directory already contains a JSON snapshot

## Kill Switch

Two paths, checked at every cycle boundary:

| File | Purpose | Who Creates It |
|------|---------|---------------|
| `~/.config/evolve/KILL` | Permanent stop (outside repo) | Human |
| `.agents/evolve/STOP` | One-time local stop | Human or automation |

To stop $evolve:
```bash
echo "Taking a break" > ~/.config/evolve/KILL    # Permanent
echo "done for today" > .agents/evolve/STOP       # Local, one-time
```

To re-enable:
```bash
rm ~/.config/evolve/KILL
rm .agents/evolve/STOP
```

## Flags Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--max-cycles=N` | unlimited | Optional hard cap. Without this, loop runs forever. |
| `--test-first` | off | Pass `--test-first` through to `$rpi` -> `$crank` |
| `--dry-run` | off | Measure fitness and show plan, don't execute |
| `--skip-baseline` | off | Skip cycle-0 baseline sweep |
| `--parallel` | off | Enable parallel goal execution via $swarm per cycle |
| `--max-parallel=N` | 3 | Max goals to fix in parallel (cap: 5). Only with `--parallel`. |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `$evolve` exits immediately with "KILL SWITCH ACTIVE" | Kill switch file exists | Remove `~/.config/evolve/KILL` or `.agents/evolve/STOP` to re-enable |
| "No goals to measure" error | GOALS.yaml missing or empty | Create GOALS.yaml in repo root with fitness goals (see goals-schema.md) |
| Cycle completes but fitness unchanged | Goal check command is always passing or always failing | Verify check command logic in GOALS.yaml produces exit code 0 (pass) or non-zero (fail) |
| Regression revert fails | Multiple commits in cycle or uncommitted changes | Check cycle-start SHA in fitness snapshot, commit or stash changes before retrying |
| Harvested work never finalizes | Queue item was claimed but cycle did not clear/finalize it | Inspect `claim_status`, `claimed_by`, and `claimed_at`; successful cycles consume, failed cycles release |
| Loop stops after empty queues | Generator streak was exhausted too quickly or `--max-cycles` was set | Verify producer layers ran, inspect `session-state.json`, and omit `--max-cycles` for overnight runs |
