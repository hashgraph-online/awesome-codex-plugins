---
name: eval
user-invocable: true
tags: [eval, measurement, quality, meta, standard]
model: sonnet
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
args-schema:
  - flag: --session
    description: "session_id to evaluate (default: last completed session via the resolution cascade)"
  - flag: --no-write
    description: "Evaluate + report without appending to the eval journal (.orchestrator/metrics/eval.jsonl)"
  - flag: --verify
    description: "Re-evaluate a stored run-id and diff per-dimension for scoring drift (exit 1 on drift)"
description: >
  Use this skill to run an honest session-process evaluation (Standard v1, aiat-llm-eval/1.0) — score the last completed orchestrator session against the pre-registered rubric-v1 dimensions, run /eval, evaluate this session, produce an eval report, or re-verify a stored eval run for reproducibility. Deterministic-first with an optional advisory LLM judge; never produces a global score.
---

> **Platform Note:** State files use the platform's native directory: `.claude/` (Claude Code), `.codex/` (Codex CLI), or `.cursor/` (Cursor IDE). Shared metrics + the eval journal live in `.orchestrator/metrics/`. See `skills/_shared/platform-tools.md`.

# Eval Skill — Session-Process Evaluation (aiat-llm-eval/1.0)

On-demand, honest measurement of ONE completed orchestrator session against the
pre-registered **rubric-v1** check set. The deterministic engine
(`scripts/eval-session.mjs` → `scripts/lib/eval/engine.mjs`) reads only local
metrics files (`sessions.jsonl` + `events.jsonl`), scores the five deterministic
dimensions, appends a `session-eval` record to the journal, and optionally
renders an HTML report. An opt-in LLM judge overlays two advisory dimensions.

The standard this skill implements is [`docs/eval/aiat-llm-eval-v1.md`](../../docs/eval/aiat-llm-eval-v1.md);
the frozen, content-hashed check set is [`skills/eval/rubric-v1.md`](./rubric-v1.md).

## Posture Contract (load-bearing — read before executing)

- **No global score, by construction.** The record has no overall/total/mean
  field, and this skill never derives one. Report per-dimension verdicts only.
- **Never guess.** Missing source data yields `cannot-determine` (a first-class,
  non-error verdict) with an honest reason — never a fabricated `pass`/`fail`.
  Do NOT "fill in" a missing KPI or infer a gate result the events do not show.
- **Deterministic before judge.** The five deterministic dimensions are complete
  on their own. The judge (Phase 3) is opt-in, ADVISORY, and `uncalibrated` in
  v1 — never blend a judge verdict into the deterministic tally.
- **Journal is SSOT; the report is a derived view.** The append-only
  `.orchestrator/metrics/eval.jsonl` is authoritative. The HTML report is
  rebuildable from any stored record and is never authoritative over the journal.
- **`--verify` is the reproducibility proof.** Re-scoring stored source data
  reproduces the stored dimensions byte-for-byte (exit 0) or reports drift
  (exit 1). This proves the SCORING replays — NOT that the model is deterministic.
- **Self-evaluation is labelled as such.** The orchestrator scoring its own
  session is a self-evaluation, not an independent audit.

---

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is
CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before
proceeding. If the gate is OPEN, continue to Phase 1.

<HARD-GATE>
Do NOT proceed past Phase 0 if GATE_CLOSED. There is no bypass. Refer to
`skills/_shared/bootstrap-gate.md` for the full HARD-GATE constraints.
</HARD-GATE>

---

## Phase 1: Config & Argument Loading

### 1.1 Read Session Config

Read and parse Session Config per `skills/_shared/config-reading.md`. Extract the
`eval` block (`scripts/lib/config.mjs` returns it as `config.eval`, parsed by
`scripts/lib/config/eval.mjs`):

```
enabled:  boolean  (default false)
mode:     'warn' | 'off'            (default 'warn')
judge:    'off' | 'haiku' | 'sonnet' (default 'off')
report:   'html' | 'none'           (default 'html')
handle:   string | null             (default null)
```

**On-demand `/eval` runs regardless of `eval.enabled`.** The `enabled` flag gates
the AUTOMATIC session-end eval phase only — it does NOT gate this command (same
posture as `/reconcile` vs `reconcile.enabled`). `mode: off` is honoured as a
kill-switch only for the automatic phase; on-demand invocation still runs. If
`eval.judge` is `off`, skip Phase 3 entirely.

> **Parser gotcha:** the `eval:` key-line itself MUST NOT carry an inline comment
> (strict `/^eval:\s*$/`); a trailing `# comment` on that exact line makes the
> parser skip the whole block and silently apply ALL defaults. Sub-key lines
> tolerate inline comments.

### 1.2 Parse Arguments

Inspect `$ARGUMENTS`:

- `--session <id>` → pass through to `--session`.
- `--no-write` → evaluate without appending to the journal (dry-run).
- `--verify <run-id>` → **verification mode**: skip Phases 2–4, run the CLI
  `--verify` path (see Phase 6), report MATCH/DRIFT, done.

### 1.3 Capture the Model Id (honest provenance)

The record's `model.source` records HOW the model id was captured, precisely
because self-report is unreliable:

- If `$ANTHROPIC_MODEL` is set in the environment, the engine reads it
  automatically with `source: env` — **env wins over the flag** (precedence
  `env > flag`). Do not pass `--model-id` in that case; let the engine resolve it.
- Otherwise the coordinator passes its own self-reported model id:
  `--model-id <self-reported-model-id> --model-source self-report`.

---

## Phase 2: Deterministic Run

Run the deterministic engine via its CLI. Default target is the last completed
session (resolution cascade); `--session` overrides.

```bash
node scripts/eval-session.mjs [--session <id>] --json \
  [--model-id <self-reported-id> --model-source self-report] \
  [--no-write]
```

- **Do NOT pass `--metrics-dir`** for a real run — the engine defaults to the
  live `.orchestrator/metrics`, the session being evaluated.
- The CLI captures the eval `timestamp` (the one sanctioned clock read) and hands
  it to the engine as a parameter, so the scoring path stays clock-free and
  `--verify`-reproducible.
- Exit codes: `0` success · `1` user error (session not found) · `2` system error.
  On exit `1` (e.g. "no completed session found"), surface the message and stop —
  do not retry with fabricated inputs.

Parse the emitted JSON record. It carries `dimensions[]` (5 deterministic
entries), `kpis{}`, `provenance.rubric_sha256` (non-null once `rubric-v1.md`
exists), `model`, `harness`, and `run_id`. Unless `--no-write` was passed, the
record is already appended to `.orchestrator/metrics/eval.jsonl` by the CLI.

**Contamination check:** if the human-render/summary reports a peer-overlapped
window, note it — `verification-evidence` and `gate-health` will read
`cannot-determine` for that reason (attribution is unsafe), which is correct, not
a defect.

---

## Phase 3: Judge Overlay (ONLY when `eval.judge != off`)

The judge runs **coordinator-side** — `AskUserQuestion` and the `Agent` tool are
not available inside a dispatched subagent, so the judge is dispatched from the
coordinator thread using the read-only agent `session-orchestrator:eval-judge`
(model = `eval.judge`). Reference the API; do not reimplement scoring here:

```javascript
import { runEvalJudge, mergeJudgeDimensions } from '$PLUGIN_ROOT/scripts/lib/eval/judge.mjs';
import { appendEvalRecord } from '$PLUGIN_ROOT/scripts/lib/eval/sink.mjs';

// dispatchAgent = the coordinator's Agent-tool dispatch closure targeting
// subagent_type 'session-orchestrator:eval-judge'.
const { status, dimensions } = await runEvalJudge({
  dispatchAgent,
  record,                       // the deterministic record from Phase 2
  model: EVAL_JUDGE_MODEL,      // eval.judge ('haiku' | 'sonnet')
  budget: JUDGE_BUDGET_TOKENS,  // optional
});

// mergeJudgeDimensions appends the advisory judge dimensions to the record.
const merged = mergeJudgeDimensions(record, dimensions);

// The COORDINATOR appends the enriched record (subagents never write the journal).
appendEvalRecord(merged, { path: '.orchestrator/metrics/eval.jsonl' });
```

- Every judge dimension arrives `advisory: true` + `calibration_status:
  "uncalibrated"` (the schema firewall rejects any other shape). Keep them
  visibly separated from the deterministic five in the summary.
- If `runEvalJudge` returns a non-ok `status` (e.g. dispatch failed), keep the
  deterministic record as-is and note the judge was unavailable — the
  deterministic evaluation is complete without it.
- When `--no-write` was passed in Phase 2, do NOT append the merged record either.

> The judge merge re-writes the record with the SAME `run_id`/`timestamp`, so a
> later `--verify <run-id>` re-scores the deterministic dimensions from source
> and diffs them; judge dimensions are advisory and excluded from the drift diff.

---

## Phase 4: Report (ONLY when `eval.report == html`)

Render the derived HTML view from the record:

```javascript
import { writeEvalReport } from '$PLUGIN_ROOT/scripts/lib/eval/report.mjs';

const res = writeEvalReport(record, { generatedAt: new Date().toISOString() });
// res.ok === true → res.path === .orchestrator/eval/reports/<run_id>.html
```

- Output path: `.orchestrator/eval/reports/<run_id>.html` (gitignored — a derived
  view, rebuildable from the journal).
- `writeEvalReport` NEVER throws; on `res.ok === false` surface the WARN reason
  and continue (the journal record is unaffected — the report is derived).
- **Name the report path in the chat** so the operator can open it.
- When `eval.report == none`, skip this phase.

---

## Phase 5: Chat Summary

Emit a compact, honest per-dimension summary. Status lines only — no global score.

```
## /eval — <session_id>  (self-evaluation, aiat-llm-eval/1.0 · rubric-v1 · n=1, no CI)

Deterministic:
  verification-evidence   PASS   <one-line evidence>
  plan-fidelity           PASS   completion_rate=1.0 (score)
  gate-health             PASS   <one-line evidence>
  process-safety          PASS   <one-line evidence + guard-emission disclosure>
  efficiency-kpis         N/A    (reported: duration=…s waves=… agents=… tok_in=… tok_out=… carryover=…)

Judge (advisory, uncalibrated)  [only when eval.judge != off]:
  instruction-adherence   <verdict>   advisory
  report-quality          <verdict>   advisory

cannot-determine: <k> of 5 deterministic dimensions (<reasons>)
Report:  .orchestrator/eval/reports/<run_id>.html
Journal: .orchestrator/metrics/eval.jsonl  (appended: <yes|--no-write>)
Re-verify: node scripts/eval-session.mjs --verify <run_id>
```

Always report the `cannot-determine` share explicitly — a high abstention count
is an honest signal about missing telemetry, not a failure to hide. Always print
the `--verify` command as the reproducibility handle.

---

## Phase 6: Verification Mode (`--verify <run-id>`)

When Phase 1.2 detected `--verify`, run ONLY:

```bash
node scripts/eval-session.mjs --verify <run-id> --json
```

- Exit `0` + `{ match: true }` → the stored record re-scores identically across
  all deterministic dimensions. Report MATCH with the dimension count.
- Exit `1` + `{ match: false, diffs }` → scoring drift. Report the per-dimension
  diff (`id.field: stored=… fresh=…`). Drift means the source data or the engine
  changed since the record was written — investigate, do not overwrite.
- `--verify` reproduces the stored model + timestamp verbatim (no env override),
  so a MATCH is a real reproducibility proof of the scoring, not of model output.

---

## Cross-Platform (Codex CLI / Cursor / Pi) — FA4

The deterministic core is pure Node CLIs (`scripts/eval-session.mjs`) plus Node
library modules (`report.mjs`, `sink.mjs`) — they run identically on every
platform. Only the judge phase needs harness-specific tooling.

- **Codex CLI / Cursor / Pi:** the `Agent` tool (and `AskUserQuestion`) are
  unavailable, so **Phase 3 (judge) is SKIPPED with a one-line note**
  ("judge phase skipped: requires the Agent tool, unavailable on `<platform>`").
  Phases 2, 4, 5, 6 run unchanged — they are Node-only. See
  `skills/_shared/platform-tools.md` § Agent Dispatch Pattern.
- **`harness.platform`** on the record is resolved from `$SO_PLATFORM`
  (falls back to `claude-code`) inside the engine — no skill action needed.
- The deterministic five dimensions + the HTML report + `--verify` are fully
  available on all platforms; the judge overlay is a Claude-Code-only enrichment
  in v1.

---

## Anti-Patterns

- **DO NOT** derive, print, or imply a global/overall/aggregate score — the record
  forbids one by construction and so does every report.
- **DO NOT** guess or "fill in" missing data — a missing gate result, KPI, or
  completion_rate is `cannot-determine`/`null`, never a fabricated pass or `0`.
- **DO NOT** present the judge's advisory verdict as a measurement — it is
  `uncalibrated` in v1 and must stay visibly separated from the deterministic
  tally.
- **DO NOT** treat the HTML report as authoritative — the journal is the SSOT; the
  report is a rebuildable derived view.
- **DO NOT** skip `--verify` when reproducibility is in question — it is the
  executable proof, and its MATCH/DRIFT exit code is the source of truth.
- **DO NOT** pass `--metrics-dir` for a real run — that points the engine at
  fixture data instead of the live session metrics.
- **DO NOT** call `runReconcile`-style writes from a subagent — the coordinator
  owns every `eval.jsonl` append (PSA-007).
