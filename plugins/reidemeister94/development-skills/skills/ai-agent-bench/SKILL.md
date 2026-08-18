---
name: ai-agent-bench
description: "Compare Claude Code and Codex on the same real code-change task with isolated worktrees, identical gates, transcripts, time, and cost."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Edit, Write
---

# AI agent bench

Compare agents only with the same task, starting commit, and outcome check. The harness preserves result branches and removes temporary worktrees.

Create `<repo>/.agent-bench.toml`:

```toml
prompt = "prompts/task.md"
start_branch = "main"              # or start_commit
agents = ["claude", "codex"]
outer_check = "./scripts/full_check.sh"
inner_check = "pytest tests/integration/test_x.py -q"
```

`outer_check` proves the real outcome before and after, and measures wall time. `inner_check` gives agents fast feedback.

Require a clean repo, available CLIs, and a passing `outer_check`. Confirm agents and run ID, then run trials sequentially to avoid load-biased timing:

```bash
python <skill>/scripts/run_trial.py --repo "$REPO" --config "$REPO/.agent-bench.toml" --agent "$AGENT" --run "$RUN_ID"
```

Results go to `eval-results/<task>/<agent>/run-<id>-<timestamp>/`. Record unexpected behavior in `ai-agent-bench-anomalies.md` per [anomalies](references/anomalies.md).

Aggregate with `scripts/parse_transcript.py --aggregate <run-dirs> --output comparison.json --render-report comparison.md`. Report gates, branches, time delta, tokens, and cost. Never rank a failed trial.

For plugin behavior rather than a real code task, use the bounded Pydantic runner documented by `eval-regression` and `scripts/run_evals.py`.

Never commit on the user's branch. A repeated run creates a new timestamped result and preserves prior evidence.
