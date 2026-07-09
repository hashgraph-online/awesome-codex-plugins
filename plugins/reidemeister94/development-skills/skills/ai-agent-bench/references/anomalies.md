# `<repo>/ai-agent-bench-anomalies.md` — format spec

Append-only log of anything unexpected during a trial. Created by the harness on the first anomaly, never overwritten. Operational, not source-of-truth — propose adding it to `.gitignore`.

## Structure

```markdown
# AI Agent Bench Anomalies

---

## Run <agent>/<run_id> — <ISO timestamp>

- Agent: <claude|codex|opencode>
- Run ID: <label>
- Start commit: <SHA>
- Run dir: <path>
- Worktree branch: <eval-...>
- Prompt: <path>

### <ISO timestamp> — <Short title>

- Step: <which phase>
- Severity: <low|medium|high>
- Symptom: <what was observed>
- Evidence: <exact commands, log excerpts with line numbers, exit codes — redact secrets>
- Analysis: expected / observed / implication for trial validity, plus assumptions and alternatives considered
- Disposition: <auto-resolved | waiting for user | aborted | logged and continuing>
```

One `## Run …` header **per `run_dir`** (the run dir path is the dedupe marker); later events append as `### …` under it. Preflight failures (no run started) get their own `---` / `## Preflight — <ts>` block per invocation.

Severity: `low` = no validity impact; `medium` = weakens interpretation, run continues; `high` = invalidates trial or needs user decision.

## Trigger events

- `git status --porcelain` non-empty on launch
- `outer_check` exit ≠ 0 on HEAD before trial (STOP, no trial possible) or after agent (regression)
- Agent CLI missing or crashes
- Agent re-runs `outer_check` itself (its basename appears in `session.jsonl` tool calls)
- `session.jsonl` flat for > 10 min while phase is `agent:running` (probable stall)
- Codex `{"type":"error","message":"Reconnecting..."}` in `session.jsonl`
- Wall time crosses 150 min (warn) or 240 min (recommend terminate)
- Pre-existing `.worktree-eval-*` not cleaned up by a previous run
- Cost-meter or token-count parse fails (parser schema mismatch)

## What NOT to log

Successful phase transitions (those go to `status.txt`). Routine progress. Self-corrections with no human-visible impact. Anything already in `comparison.md` — this file is for surprises, not statistics.
