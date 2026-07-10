---
name: ai-agent-bench
description: "Use when the user wants to benchmark or compare AI agents (Claude Code, Codex, OpenCode) on a refactoring, perf, or code-change task in the current repo. Use when user says compare agents, benchmark Claude vs Codex, agent eval, measure agent, AI agent comparison, agent trial, /ai-agent-bench."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Edit, Write, Skill
---

# AI Agent Bench

Benchmark one or more AI agents on a real coding task in the current repo. Per agent, the harness:
1. Creates a git worktree at `start_commit` on a fresh `eval-<agent>-run<id>-<ts>` branch.
2. Runs `outer_check` once (baseline — live e2e correctness + wall time).
3. Launches the agent with the user's prompt; the agent uses `inner_check` for fast iteration.
4. Runs `outer_check` once again (post — same gate + wall time).
5. Captures transcript, diff, exit codes, timings under `eval-results/<task>/<agent>/run-<id>-<ts>/`.

The branch survives after the trial; the worktree directory is removed. `outer_check` is both gate and measure — there are no pre_hooks, measure_repetitions, or sufficiency checks.

## TOML schema (`<repo>/.agent-bench.toml`)

```toml
prompt       = "prompts/<task>.md"        # task prompt (markdown)
start_branch = "main"                      # override with start_commit = "<sha>" to pin
agents       = ["claude"]                  # subset of ["claude", "codex", "opencode"]
outer_check  = "./scripts/full_check.sh"   # live e2e: PASS/FAIL + wall-time, run once before/after
inner_check  = "pytest tests/integration/test_x.py -q"  # fast iteration test for the agent
```

The harness stages nothing — if the task needs fixtures/env, make `outer_check`/`inner_check` self-sufficient and commit (or gitignore + regenerate) anything they read.

## Step 0 — Preflight

```bash
REPO=$(git rev-parse --show-toplevel) || exit 1
[ -z "$(git -C "$REPO" status --porcelain)" ] || { echo "uncommitted changes — commit/stash first"; exit 1; }
[ -f "$REPO/.agent-bench.toml" ] || { echo "missing $REPO/.agent-bench.toml — see schema above"; exit 1; }
```

For each `agent`: `which $agent` must succeed. Python ≥ 3.11.

## Step 1 — Validate `outer_check` on HEAD

Run `outer_check` once in the repo before any trial. Exit 0 = baseline reference. Exit ≠ 0 = STOP, fix the code or the command; do NOT proceed.

## Step 2 — Confirm runtime params (numbered options, STOP and wait)

1. `agents` — confirm the TOML value or pick a subset.
2. `run_id` — default `1` if `eval-results/<task>/` is empty, else next integer.

To change the prompt or commands, the user edits the TOML and re-invokes.

## Step 3 — Launch trials sequentially

```bash
for AGENT in "${AGENTS[@]}"; do
    python "${CLAUDE_PLUGIN_ROOT}/skills/ai-agent-bench/scripts/run_trial.py" \
        --repo "$REPO" --config "$REPO/.agent-bench.toml" --agent "$AGENT" --run "$RUN_ID"
done
```

Sequential, never parallel (wall time is a measure).

`${CLAUDE_PLUGIN_ROOT}` is set by Claude Code; under Codex resolve via Glob `**/skills/ai-agent-bench/scripts/run_trial.py` or use the absolute path.

`run_trial.py` spawns `monitor.py` as a sidecar that polls `run_dir/status.txt` and tails `session.jsonl` every 3 min into `run_dir/progress.md`. Read `progress.md` on every user message to surface the heartbeat. Hard timeouts: warn at 150 min wall time, recommend terminating at 240 min if `status.txt` still says `agent:running`.

## Step 4 — Aggregate

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/ai-agent-bench/scripts/parse_transcript.py" \
    --aggregate "$REPO/eval-results/<task>"/*/run-*/ \
    --output "$REPO/eval-results/<task>/comparison.json" \
    --render-report "$REPO/eval-results/<task>/comparison.md"
```

Print run dirs, branch names (`git checkout eval-<agent>-run<id>-<ts>` to inspect each diff), `outer_check` exit codes, baseline-vs-post wall-time delta, and cost USD per agent.

## Anomaly log

Append anything unexpected in real time to `<repo>/ai-agent-bench-anomalies.md`. Append-only across runs (one `## Run …` header per run dir, that path is the dedupe marker). Format and trigger list in `references/anomalies.md`.

## Rules

- **Never commit on the user's branch.** Agent works in a worktree on `eval-<agent>-run<id>-<ts>`; the snapshot commit is harness-owned.
- Re-running on the same `(task, agent, run_id)` creates a new timestamped run dir and branch; previous metrics stay intact.

Add a new agent: `references/agents.md`.
