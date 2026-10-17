# Datasheet Extraction Dispatcher Contract

> **Status:** Phase 3a (v1.4). The contract is stable and applies to every dispatcher implementation: `dispatch-claude-code.md` (v1.4), `dispatch-codex.md`, `dispatch-gemini.md`, `extract.py` SDK runner, canned harness dispatcher (all v1.5+).

A **dispatcher** is the swappable layer between `plan_extraction.py` and `merge_results.py` in the Phase 3a extraction pipeline. Its job: read `<mpn>.plan.json`, run each per-task subagent under its native LLM-dispatch primitive, write per-task wrapped result files. Python (plan_extraction + merge_results) is stdlib-only and platform-agnostic; the dispatcher is the only agent-specific component.

## Inputs

The dispatcher reads:

- `<cache_dir>/<mpn>.plan.json` — `plan.schema.json` shape
- `<cache_dir>/<mpn>.scout.json` — `scout.schema.json` shape (for prompt placeholder injection)
- The PDF at `<plan.pdf_path>` (each subagent reads it directly; the dispatcher does not read PDF content)
- Each `task.prompt_template` (Markdown with `{{MPN}}`, `{{PDF_PATH}}`, `{{PAGES}}`, `{{SCHEMA_PATH}}` placeholders)
- Each `task.schema` (JSON Schema for validation)

## Outputs

Per task: `<cache_dir>/<mpn>.<task_id>.result.json` — the **wrapped result file**.

```json
{
  "task_id": "regulator",
  "schema_version": "0.3",
  "status": "complete",
  "extracted_at": "2026-04-25T11:00:00Z",
  "model_tier": "B",
  "model_id": "claude-sonnet-4-6",
  "data": { ... }
}
```

`status` ∈ `{"complete", "failed"}`. Other fields:

- `task_id`: matches `task.task_id` exactly.
- `schema_version`: schema version of the task's output (e.g. `"0.3"` for regulator). Read from the schema's `x-schema-version` field if present; otherwise `"1.0"`.
- `extracted_at`: ISO-8601 UTC timestamp.
- `model_tier`: `A` or `B` per `task.tier`.
- `model_id`: opaque identifier of the LLM that produced the output.
- `data`: the subagent's output object (or `null` on failure).
- `error` (failed only): string describing why the task failed.

## Contract

| | The dispatcher |
|---|---|
| **MUST** | For each task in `plan.tasks` where `status: "pending"`: instantiate the subagent with `task.prompt_template` (placeholders substituted) and the task's PDF page list, capture subagent output, write the wrapped result file to `<cache_dir>/<mpn>.<task_id>.result.json`. |
| **MUST** | Set `status: "complete"` if subagent output passes JSON-schema validation against `task.schema`; set `status: "failed"` with an `error` field if validation fails or the subagent reports an explicit error. |
| **MUST** | Respect `task.depends_on` — never dispatch a task whose dependencies haven't all reached `status: "complete"`. (Phase 3a tasks all have `depends_on: []`, so this is a future-proofing constraint.) |
| **MUST** | Be idempotent — if a result file already exists with `status: "complete"`, skip that task (resume-safe). |
| **MUST** | Substitute prompt placeholders: `{{MPN}}` ← `plan.mpn`, `{{PDF_PATH}}` ← `plan.pdf_path`, `{{PAGES}}` ← `task.pages` (formatted as a human-readable list, e.g. "5, 6, 13–15"), `{{SCHEMA_PATH}}` ← `task.schema`. |
| **MAY** | Dispatch parallel-eligible tasks (empty or fully-satisfied `depends_on`) concurrently. Single-threaded dispatch is also valid. |
| **MAY** | Do its own internal retry on transient failures (network errors, rate limits). This is distinct from the plan-level retry semantics owned by `merge_results.py`. |
| **MAY** | Append a per-task entry to a cost ledger JSONL file (format: `{run_id, mpn, task_id, tier, model_id, tokens_in, tokens_out, cost_usd, success}`). Cost ledger location and format are documented per dispatcher. |
| **MUST NOT** | Modify `plan.json` itself. `merge_results.py` owns `execution.outcomes`. |
| **MUST NOT** | Skip schema validation. A result file with `status: "complete"` implies schema-valid by contract. |
| **MUST NOT** | Overwrite an existing `status: "complete"` result file without an explicit `--force` flag passed to the dispatcher. |
| **MUST NOT** | Edit or merge into `<mpn>.json` directly. That's `merge_results.py`'s job. |
| **MUST NOT** | Read or generate `<mpn>.json` (except for resume-safety idempotence checks against the result files, which is fine). |

## Retry semantics

The dispatcher is invoked **at most twice per pipeline run**:

1. **First invocation**: dispatch all `pending` tasks. Result files written. `merge_results.py` runs, validates, writes `<mpn>.json`. If any task is `failed`, exit nonzero — the orchestrator that drives the pipeline re-invokes the dispatcher once more, re-running just the failed tasks (delete or rename their result files first to bypass idempotence).

2. **Second invocation** (`--retry-failed` mode in the dispatcher recipe): re-dispatch the failed tasks with the original prompt + appended error message ("Your previous output failed schema validation: <error>. Try again."). Write new result files (overwriting the failed ones). `merge_results.py --retry-failed` then runs; tasks that succeed merge cleanly; tasks that still fail get partial-merged with `{"_extraction_failed": true, "reason": ...}`.

The dispatcher does NOT loop on its own. The retry decision is owned by the orchestrator (or the user running the recipe).

## Failure classification

The dispatcher classifies subagent output as one of:

- **Hard failure**: malformed JSON, schema validation error, subagent returned an error message, missing required field. Set `status: "failed"`, populate `error`.
- **Soft / quality issue**: schema-valid but anomalous output (zero pins extracted, every absolute_max field null). Set `status: "complete"` and let the acceptance gate's quality score / sanity vector check catch the issue.

The dispatcher does NOT inspect the data semantically beyond schema validation. Quality checking is `datasheet_score.py`'s and `validate_sanity_vector.py`'s job.

## Cost ledger (optional, recommended for v1.4)

If the dispatcher writes a cost ledger, the format is JSONL:

```
{"run_id": "20260425T100000Z-a1b2c3", "mpn": "LM2596-ADJ", "task_id": "scout", "tier": "B", "model_id": "claude-sonnet-4-6", "tokens_in": 12000, "tokens_out": 800, "cost_usd": 0.0123, "success": true, "extracted_at": "2026-04-25T10:00:30Z"}
```

Location: `<cache_dir>/_cost_ledger.jsonl`. Append-only; never rewritten.

The Phase 3a Claude Code recipe makes this optional (the cost data isn't auditable from inside the `Agent` tool); v1.5 SDK dispatchers populate it directly from API responses.

## Relationship to plan_extraction.py and merge_results.py

```
                       plan_extraction.py
                               │
                               ▼
                       <mpn>.plan.json
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │         DISPATCHER (this contract)   │
            └──────────────┬───────────────────────┘
                           │  result files
                           ▼
                       merge_results.py
                               │
                               ▼
                       <mpn>.json
```

The dispatcher knows nothing about `<mpn>.json`. Plan in, result files out.
