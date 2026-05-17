---
name: ai-agent-bench
description: "Use when the user wants to benchmark or compare AI agents (Claude Code, Codex, OpenCode) on a refactoring, perf, or code-change task in the current repo. Use when user says compare agents, benchmark Claude vs Codex, agent eval, measure agent, AI agent comparison, agent trial, /ai-agent-bench."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Edit, Write, Skill
---

# AI Agent Bench

**Announce:** "Using the ai-agent-bench skill."

Benchmark one or more AI agents on a real coding task in the current repo. The harness:
1. Creates a git worktree at `start_commit` on a fresh `eval-<agent>-run<id>-<ts>` branch.
2. Runs `outer_check` once (baseline — live e2e correctness + wall time).
3. Launches the agent with the user's prompt; the agent uses `inner_check` for fast iteration.
4. Runs `outer_check` once again (post — same correctness gate + wall time).
5. Captures everything (transcript, diff, exit codes, timings) under `eval-results/<task>/<agent>/run-<id>-<ts>/`.
6. Writes anomalies in real time to `<repo>/ai-agent-bench-anomalies.md` (append-only, one `## Run …` block per trial separated by `---`).

The branch survives after the trial — the worktree directory is removed.

## TOML schema (`<repo>/.agent-bench.toml`)

```toml
prompt       = "prompts/<task>.md"        # path to the task prompt (markdown)
start_branch = "main"                      # branch to start from. Override with start_commit = "<sha>" to pin.
agents       = ["claude"]                  # subset of: ["claude", "codex", "opencode"]

outer_check  = "./scripts/full_check.sh"   # live e2e: PASS/FAIL + wall-time. Run once before, once after.
inner_check  = "pytest tests/integration/test_x.py -q"  # fast iteration test for the agent; transcript captures its output.
```

That's the whole config. No `pre_hooks`, no `measure_repetitions`, no `agent_test_commands`, no sufficiency or prompt-hygiene checks. If the task needs setup (fixtures, env files), make `outer_check`/`inner_check` self-sufficient — the harness does not pre-stage anything.

## Step 0 — Preflight

```bash
REPO=$(git rev-parse --show-toplevel) || exit 1
[ -z "$(git -C "$REPO" status --porcelain)" ] || { echo "uncommitted changes — commit/stash first"; exit 1; }
[ -f "$REPO/.agent-bench.toml" ] || { echo "missing $REPO/.agent-bench.toml — see schema above"; exit 1; }
```

For each `agent` in the TOML: `which $agent` must succeed. Python ≥ 3.11.

## Step 1 — Validate `outer_check` on HEAD

Run `outer_check` once, in the repo, before launching any trial. Exit 0 = baseline reference. Exit ≠ 0 = STOP, fix the code or the command. Do NOT proceed.

This single check replaces sufficiency / gate-validation / measure-validation theatrics — the user's e2e command IS the gate AND the measure. If they want stricter coverage, they tighten that command, not the harness.

## Step 2 — Confirm runtime params (plain text, numbered options, STOP and wait)

Carry every value over from the TOML and ask only for confirmation + the per-invocation params:

1. `agents` — confirm or pick a subset.
2. `run_id` — default to `1` if `eval-results/<task>/` is empty, else next integer.

Nothing else needs asking. If the user wants to change the prompt or commands, they edit the TOML and re-invoke.

## Step 3 — Launch trials sequentially

```bash
for AGENT in "${AGENTS[@]}"; do
    python "${CLAUDE_PLUGIN_ROOT}/skills/ai-agent-bench/scripts/run_trial.py" \
        --repo "$REPO" \
        --config "$REPO/.agent-bench.toml" \
        --agent "$AGENT" \
        --run "$RUN_ID"
done
```

Sequential — never parallel (CPU contention distorts wall time).

`${CLAUDE_PLUGIN_ROOT}` is set by Claude Code. Under Codex, resolve via Glob `**/skills/ai-agent-bench/scripts/run_trial.py` or use the absolute path.

`run_trial.py` spawns `monitor.py` as a sidecar; the sidecar polls `run_dir/status.txt` and tails `session.jsonl` every 3 min, writing a one-paragraph summary to `run_dir/progress.md`. Read that file on every user message to surface heartbeat to the user.

Hard timeouts: warn at 150 min wall time, recommend terminating at 240 min if `status.txt` still says `agent:running`.

## Step 4 — Aggregate

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/ai-agent-bench/scripts/parse_transcript.py" \
    --aggregate "$REPO/eval-results/<task>"/*/run-*/ \
    --output "$REPO/eval-results/<task>/comparison.json" \
    --render-report "$REPO/eval-results/<task>/comparison.md"
```

Print the run dirs, branch names (`git checkout eval-<agent>-run<id>-<ts>` to inspect each agent's diff), `outer_check` exit codes, baseline-vs-post wall-time delta, and cost USD per agent.

## Anomaly log (cross-cutting, mandatory)

Anything unexpected gets appended in real time to `<repo>/ai-agent-bench-anomalies.md` — preflight failures, `outer_check` regressions, agent crashes, harness sidecar gaps, `Reconnecting…` stream errors, agents invoking `outer_check` themselves, etc. The file is append-only across runs: each new run writes a `---` divider and a `## Run <agent>/<id> — <timestamp>` header before its first entry, so historical runs stay intact and the boundary is unambiguous. Format and trigger list in `references/anomalies.md`.

## Files in this skill

- `scripts/run_trial.py` — single-trial orchestrator (worktree → outer_check pre → agent → outer_check post → cleanup)
- `scripts/monitor.py` — sidecar heartbeat (3-min poll, writes `progress.md`)
- `scripts/parse_transcript.py` — per-agent transcript parsers + cross-agent aggregator
- `scripts/pricing.json` — USD/M tokens per model
- `references/anomalies.md` — `<repo>/ai-agent-bench-anomalies.md` format + trigger events
- `references/agents.md` — how to add a new agent (OpenCode, Aider, …)

## Rules

- **Never commit on the user's branch.** Agent works inside a worktree on `eval-<agent>-run<id>-<ts>`. Snapshot commit is harness-owned.
- **Sequential trials only** — CPU contention distorts wall time.
- **Fixtures stay in the repo** — anything the agent or `inner_check` needs must be committed (or gitignored + regenerated by the user beforehand). The harness no longer stages anything.
- **Repeatable re-invocation.** Re-running the skill on the same `(task, agent, run_id)` creates a new timestamped run dir and branch; previous metrics stay intact.
