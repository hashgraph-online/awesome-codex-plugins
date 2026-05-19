# `<repo>/ai-agent-bench-anomalies.md` — format spec

Append-only log of anything unexpected during an `ai-agent-bench` trial. Created by the
harness on the first anomaly. Never overwritten — historical runs stay visible. Listed in
the user's `.gitignore` proposal — operational, not source-of-truth.

## Top-level structure

```markdown
# AI Agent Bench Anomalies

Append-only log. Each run is delimited by `---` and a `## Run …` header; previous runs are
preserved.

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
- Severity: <info|medium|high>
- Symptom: <one paragraph — what was observed>
- Evidence: <exact commands, log excerpts with line numbers, exit codes>
- Detailed analysis:
  - Expected: <what>
  - Observed: <what>
  - Implication: <how it affects trial validity>
  - Details: <all relevant observable details, assumptions, alternatives considered, and decision factors>
- Disposition: <auto-resolved | waiting for user | aborted | logged and continuing>

### <ISO timestamp> — <Another event in the same run>

…

---

## Preflight — <ISO timestamp>

### <ISO timestamp> — <Short title>

…
```

A new `## Run …` header is written **once per `run_dir`** (the harness uses the run dir
path as the dedupe marker). Subsequent events in the same run append directly under it as
`### …` sub-sections. Preflight failures (no run started yet) get their own `---` /
`## Preflight …` block per harness invocation.

## Trigger events (write an entry when any of these fires)

- `git status --porcelain` non-empty on launch
- `outer_check` exit ≠ 0 on HEAD before trial → STOP, no trial possible
- `outer_check` exit ≠ 0 after agent → behavioural regression
- Agent CLI missing or crashes
- Agent re-runs `outer_check` itself (look for its basename in `session.jsonl` tool calls)
- `session.jsonl` flat for > 10 min while phase is `agent:running` (probable stall)
- Codex `{"type":"error","message":"Reconnecting..."}` in `session.jsonl`
- Wall time crosses 150 min (warn) or 240 min (recommend terminate)
- Pre-existing `.worktree-eval-*` not cleaned up by previous run
- Cost-meter or token-count parse fails (parser schema mismatch)

## Per-entry rules

- **Timestamps**: ISO 8601 with timezone offset (`2026-04-26T14:30:00+02:00` or `…Z`).
- **Evidence**: paste exact excerpts with file:line refs. Redact secrets.
- **Detailed analysis**: mandatory. Do not compress to a terse summary when more detail helps audit the event. Include expected / observed / implication, plus concrete details such as assumptions, alternatives considered, why the disposition was chosen, and what would change the interpretation.
- **Severity**:
  - `info` — observed, does not affect validity
  - `medium` — weakens interpretation, run continues
  - `high` — invalidates trial or requires user decision

## What NOT to log

Successful phase transitions (those go to `status.txt`). Routine progress output. Agent
self-corrections that left no human-visible impact. Anything already in the final
`report.md` / `comparison.md` — this file is for surprises, not statistics.
