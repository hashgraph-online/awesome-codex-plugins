# Claude Code Dispatcher Recipe

> **Reference dispatcher for v1.4 Phase 3a.** Satisfies `dispatcher-contract.md` using Claude Code's `Agent` tool.

This document tells an orchestrator running inside Claude Code how to dispatch the per-task subagents for an extraction plan. It assumes the orchestrator has read `dispatcher-contract.md` and the relevant prompt templates.

## Inputs

Two files in `<cache_dir>`:

- `<mpn>.plan.json` — the plan written by `plan_extraction.py`
- `<mpn>.scout.json` — the unwrapped scout output (used to inject metadata if a prompt template needs it; in 3a, only `plan.tasks[].pages` is needed)

## Workflow

### Step 1 — Confirm scout has run

If `<mpn>.scout.json` does not exist, run the scout first:

1. Read `skills/datasheets/prompts/scout.md`.
2. Substitute placeholders: `{{MPN}}` = `<plan.mpn>`, `{{PDF_PATH}}` = `<plan.pdf_path>`, `{{SCHEMA_PATH}}` = `skills/datasheets/schemas/scout.schema.json`.
3. Invoke `Agent` with:
   - `subagent_type: general-purpose`
   - `description: "Datasheet scout for <mpn>"`
   - `prompt`: the substituted prompt
4. Capture the agent's JSON output. Validate against `skills/datasheets/schemas/scout.schema.json`. If valid, write the unwrapped JSON to `<cache_dir>/<mpn>.scout.json` AND a wrapped version to `<cache_dir>/<mpn>.scout.result.json` (status complete, schema_version 1.0, extracted_at now, model_tier B, model_id claude-{current model}, data = the JSON).
5. Then re-invoke `plan_extraction.py <mpn> <pdf_path> --use-cached-scout --cache-dir <cache_dir>` to generate the plan.

### Step 2 — Dispatch per-task subagents in parallel

For each `task` in `plan.tasks` with `status: "pending"` and `depends_on: []`, dispatch in parallel **in a single Claude Code message containing one `Agent` tool-call per task**.

For each task:

1. Read the prompt template from `task.prompt_template` (relative to repo root).
2. Substitute placeholders:
   - `{{MPN}}` ← `plan.mpn`
   - `{{PDF_PATH}}` ← `plan.pdf_path`
   - `{{PAGES}}` ← human-readable formatted list (e.g. `task.pages = [5,6,13,14,15]` → `"5, 6, 13–15"`)
   - `{{SCHEMA_PATH}}` ← `task.schema`
3. Invoke `Agent` with:
   - `subagent_type: general-purpose`
   - `description: "Datasheet <task.subagent_role> extractor for <mpn>"`
   - `prompt`: the substituted prompt (which includes the page list as part of the agent's instructions and the schema path as the validation contract)

**All three (base, pinout, regulator) for LM2596-ADJ go in one message.** Claude Code dispatches them concurrently. Wait for all to return.

### Step 3 — Wrap and validate each agent output

For each returned agent output:

1. Parse the JSON from the agent's response. If the agent wrapped it in markdown code fences or surrounding prose, strip those (the prompts say "no prose, no fences" but be defensive).
2. Run JSON Schema validation against `task.schema` (use `python -c "import json,jsonschema; ..."` or call `merge_results.py` indirectly).
3. Build the wrapped result:
   ```json
   {
     "task_id": "<task.task_id>",
     "schema_version": "<schema's x-schema-version>",
     "status": "complete" or "failed",
     "extracted_at": "<now ISO-8601>",
     "model_tier": "<task.tier>",
     "model_id": "claude-<current Claude Code model>",
     "data": <agent JSON, or null>,
     "error": "<validation error message>"  // only if status == failed
   }
   ```
4. Write to `<cache_dir>/<mpn>.<task_id>.result.json`.

### Step 4 — Run merge_results.py

```bash
python3 skills/datasheets/scripts/merge_results.py <mpn> --cache-dir <cache_dir>
```

If exit code is 0: extraction is complete; `<cache_dir>/<mpn>.json` is the canonical cache file. Done.

If exit code is 1: at least one task is in `failed` status. Read stderr for the specific task IDs.

### Step 5 — Retry once on hard failure

For each failed task:

1. Read the existing `<mpn>.<task_id>.result.json` to get the `error` message.
2. Read `task.prompt_template` again, substitute placeholders, **and append**:

   ```
   ## Previous attempt failed

   Your previous output failed validation with this error:
   <error>

   Re-read the relevant pages and produce a corrected output. Pay particular attention to: <hint based on error category — e.g. "missing required field topology", "min > max in VIN_max">.
   ```

3. Invoke `Agent` again with the augmented prompt.
4. Wrap and write the new result file (overwriting the failed one).

### Step 6 — Re-merge with --retry-failed

```bash
python3 skills/datasheets/scripts/merge_results.py <mpn> --cache-dir <cache_dir> --retry-failed
```

Exit code 0 always (this is the second-and-final merge). Tasks that succeeded merge cleanly; tasks that still failed are partial-merged with `{"_extraction_failed": true, "reason": ...}`.

## Concurrency note

Claude Code's `Agent` tool supports parallel tool-call dispatch within a single message. Issuing all three Phase 3a tasks (base, pinout, regulator) in one message gives ~3× speedup over serial. If context bloat becomes an issue (long conversations after multiple PDFs), fall back to two messages: `[base, pinout]` then `[regulator]`.

## Cost ledger (optional)

If you want to record cost data for analysis, append one JSONL entry per `Agent` invocation to `<cache_dir>/_cost_ledger.jsonl`:

```json
{"run_id": "20260425T100000Z-a1b2c3", "mpn": "LM2596-ADJ", "task_id": "scout", "tier": "B", "model_id": "claude-sonnet-4-6", "tokens_in": null, "tokens_out": null, "cost_usd": null, "success": true, "extracted_at": "2026-04-25T10:00:30Z"}
```

Tokens and cost are unavailable from inside Claude Code's `Agent` tool — leave them null in v1.4. v1.5 SDK dispatcher populates them.

## Failure modes to watch for

- **Agent returns prose with code fences.** Strip the fences before parsing.
- **Agent emits non-canonical units** (e.g. `unit: "µF"` instead of `unit: "F"` with value 4.7e-4). The schema accepts µF as a string but the verifier and downstream consumers expect F. Treat as a hard failure (schema validation should catch via `datasheet_verify.py` v1.4 extensions running in the harness gate).
- **Agent invents pin numbers** in the regulator extractor that don't appear in pinout. The verifier catches this.
- **Family-PDF disambiguation drift**: agent extracts a different variant's spec. Catches via sanity vector diff.
- **Page list not honored**: agent reads pages outside `task.pages`. The prompt instructs "focus on these pages"; if the agent ranges further, that's allowed (the constraint is "not less than these pages", not "only these pages").

## Example conversation flow (LM2596-ADJ)

```
USER: Run Phase 3a extraction for LM2596-ADJ from /path/to/LM2596.pdf

ORCHESTRATOR:
  - Run plan_extraction (which would dispatch scout — but cached-scout flow:
    first invoke scout subagent via Agent tool, write scout.json, then
    invoke plan_extraction --use-cached-scout)
  - [Single Agent call: scout]
  - Write LM2596-ADJ.scout.json + LM2596-ADJ.scout.result.json
  - Run plan_extraction.py LM2596-ADJ /path/to/LM2596.pdf --use-cached-scout
  - [Single message with three parallel Agent calls: base, pinout, regulator]
  - Wrap and write 3 result files
  - Run merge_results.py LM2596-ADJ
  - If any failures → retry once, re-merge with --retry-failed
  - Hand off to harness for 4-check gate
```

---

## Phase 4 addendum: dispatching review tasks

The `design_context` task (v2.0) reuses this same dispatcher contract per spec §4.5. Key differences:

- Tasks have `task_type: "review"` (vs `"extraction"` for Phase 3 datasheet tasks).
- The design_context task lives at `skills/kicad/review/prompts/design_context.md`. The reviewer task is retired in v2.0 (superseded by the Deep Review pass — see `skills/kicad/references/deep-review.md`).
- Result schemas live under `skills/kicad/review/schemas/{design_context,review_annotations}.schema.json`.
- Result paths are `analysis/<artifact>.json` (NOT `<mpn>.<task>.result.json` — review outputs are run-level, not MPN-level).

### Task → Subagent mapping

When you see a task with `task_type: "review"`:

| `task_id` | Tier | Subagent prompt |
|-----------|------|----------------|
| `design_context` | B (cheaper) | `skills/kicad/review/prompts/design_context.md` |

Same dispatch primitive (Claude Code `Task` tool); same output-validation contract (validate against `result_schema` after subagent returns); same retry semantics (one retry on hard fail with error context).

### Merge after design_context task completes

Once the design_context task has written its result file, invoke:

```bash
python3 skills/kicad/review/scripts/merge_annotations.py \
    --raw-dir analysis/ \
    --review analysis/review_annotations.json \
    --merged-dir analysis/merged/
```

This applies overlays to a copy of each raw analyzer JSON. The raw files remain unmodified.
