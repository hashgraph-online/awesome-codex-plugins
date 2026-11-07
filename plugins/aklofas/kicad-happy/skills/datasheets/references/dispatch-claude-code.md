# Claude Code Dispatcher Recipe

> **Reference dispatcher for the extraction pipeline.** Satisfies `dispatcher-contract.md` using Claude Code's `Agent` tool.

This document tells an orchestrator running inside Claude Code how to dispatch the per-task subagents for an extraction plan. It assumes the orchestrator has read `dispatcher-contract.md` and the relevant prompt templates.

## Inputs

Two files in `<cache_dir>`:

- `<sanitized_mpn>.plan.json` (the MPN with every character outside `[A-Za-z0-9_.-]` replaced by `_`: `LM317/NOPB` → `LM317_NOPB`) — the plan written by `plan_extraction.py`
- `<sanitized_mpn>.scout.json` — the unwrapped scout output (used to inject metadata if a prompt template needs it; the shipped prompts need only `plan.tasks[].pages`)

## Workflow

### Step 1 — Confirm scout has run

If `<sanitized_mpn>.scout.json` does not exist, run the scout first:

1. Read `<datasheets-skill-path>/prompts/scout.md`.
2. Substitute placeholders from the requested part (no plan exists yet): `{{MPN}}` = the target MPN, `{{PDF_PATH}}` = the source PDF path, `{{SCHEMA_PATH}}` = `<datasheets-skill-path>/schemas/scout.schema.json`.
3. Invoke `Agent` with:
   - `subagent_type: general-purpose`
   - `description: "Datasheet scout for <mpn>"`
   - `prompt`: the substituted prompt
4. Capture the agent's JSON output. Validate against `<datasheets-skill-path>/schemas/scout.schema.json`. If valid, write the unwrapped JSON to `<cache_dir>/<sanitized_mpn>.scout.json` with an added `"pdf_sha256": "sha256:<hex of the PDF>"` field (`plan_extraction.py --use-cached-scout` refuses a scout whose SHA differs from the PDF's and warns about one without a SHA) AND a wrapped version to `<cache_dir>/<sanitized_mpn>.scout.result.json` (status complete, schema_version 1.0, extracted_at now, model_tier B, model_id claude-{current model}, data = the JSON).
5. Then re-invoke `plan_extraction.py <mpn> <pdf_path> --use-cached-scout --cache-dir <cache_dir>` to generate the plan.

### Step 2 — Dispatch per-task subagents in parallel

For each `task` in `plan.tasks` with `status: "pending"` and `depends_on: []`, dispatch in parallel **in a single Claude Code message containing one `Agent` tool-call per task**.

For each task:

1. Read the prompt template from `task.prompt_template`. The plan stores repo-relative strings that start with `skills/datasheets/`; replace the leading `skills/datasheets/` with `<datasheets-skill-path>/` (the skill's install directory) and read that file instead, and do the same for `task.schema`.
2. Substitute placeholders:
   - `{{MPN}}` ← `plan.mpn`
   - `{{PDF_PATH}}` ← `plan.pdf_path`
   - `{{PAGES}}` ← human-readable formatted list (e.g. `task.pages = [5,6,13,14,15]` → `"5, 6, 13–15"`)
   - `{{SCHEMA_PATH}}` ← `task.schema`
3. Invoke `Agent` with:
   - `subagent_type: general-purpose`
   - `description: "Datasheet <task.subagent_role> extractor for <mpn>"`
   - `prompt`: the substituted prompt (which includes the page list as part of the agent's instructions and the schema path as the validation contract)

Skip a task only when its result file is complete and carries the plan's `pdf_sha256`. A result written under an older schema major version still passes; delete it or pass `--force` to re-run it.

**All three (base, pinout, regulator) for LM2596-ADJ go in one message.** Claude Code dispatches them concurrently. Wait for all to return.

### Step 3 — Wrap and validate each agent output

For each returned agent output:

1. Parse the JSON from the agent's response. If the agent wrapped it in markdown code fences or surrounding prose, strip those (the prompts say "no prose, no fences" but be defensive).
2. Run JSON Schema validation against `task.schema` (use `python -c "import json,jsonschema; ..."` or call `merge_results.py` indirectly).
3. Build the wrapped result:
   ```json
   {
     "task_id": "<task.task_id>",
     "pdf_sha256": "<plan.pdf_sha256>",
     "schema_version": "<schema's x-schema-version>",
     "status": "complete" or "failed",
     "extracted_at": "<now ISO-8601>",
     "model_tier": "<task.tier>",
     "model_id": "claude-<current Claude Code model>",
     "data": <agent JSON, or null>,
     "error": "<validation error message>"  // only if status == failed
   }
   ```
4. Write to `<cache_dir>/<sanitized_mpn>.<task_id>.result.json`.

### Step 4 — Run merge_results.py

```bash
python3 <datasheets-skill-path>/scripts/merge_results.py <mpn> --cache-dir <cache_dir>
```

If exit code is 0: extraction is complete; `<cache_dir>/<sanitized_mpn>.json` is the canonical cache file. Done.

If exit code is 1: at least one task is in `failed` status. Read stderr for the specific task IDs.

### Step 5 — Retry once on hard failure

For each failed task:

1. Read the existing `<sanitized_mpn>.<task_id>.result.json` to get the `error` message.
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
python3 <datasheets-skill-path>/scripts/merge_results.py <mpn> --cache-dir <cache_dir> --retry-failed
```

Exit code 0 always (this is the second-and-final merge). Tasks that succeeded merge cleanly; tasks that still failed are partial-merged with `{"_extraction_failed": true, "reason": ...}`.

## Concurrency note

Claude Code's `Agent` tool supports parallel tool-call dispatch within a single message. Issuing every extraction task in the plan (base, pinout and one per category, e.g. regulator) in one message gives a speedup roughly equal to the task count. If context bloat becomes an issue (long conversations after multiple PDFs), fall back to two messages: `[base, pinout]` then the category tasks.

## Cost ledger (optional)

If you want to record cost data for analysis, append one JSONL entry per `Agent` invocation to `<cache_dir>/_cost_ledger.jsonl`:

```json
{"run_id": "20260425T100000Z-a1b2c3", "mpn": "LM2596-ADJ", "task_id": "scout", "tier": "B", "model_id": "claude-sonnet-4-6", "tokens_in": null, "tokens_out": null, "cost_usd": null, "success": true, "extracted_at": "2026-04-25T10:00:30Z"}
```

Tokens and cost are unavailable from inside Claude Code's `Agent` tool — leave them null. A dispatcher that calls an API directly can populate them.

## Failure modes to watch for

- **Agent returns prose with code fences.** Strip the fences before parsing.
- **Agent emits non-canonical units** (e.g. `unit: "µF"` instead of `unit: "F"` with value 4.7e-4). The SpecValue `unit` enum has no `µF` or `uF`, so the task fails schema validation at merge and is recorded as failed; re-dispatch it with the canonical unit.
- **Agent invents pin numbers** in the regulator extractor that don't appear in pinout. The verifier catches this.
- **Family-PDF disambiguation drift**: agent extracts a different variant's spec. Catches via sanity vector diff.
- **Page list not honored**: agent reads pages outside `task.pages`. The prompt instructs "focus on these pages"; if the agent ranges further, that's allowed (the constraint is "not less than these pages", not "only these pages").

## Example conversation flow (LM2596-ADJ)

```
USER: Run extraction for LM2596-ADJ from /path/to/LM2596.pdf

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

## Dispatching review tasks

The `design_context` task reuses this same dispatcher contract. Key differences:

- Tasks have `task_type: "review"` (vs `"extraction"` for datasheet tasks).
- The design_context task lives at `skills/kicad/review/prompts/design_context.md`. The reviewer task is retired in v2.0 (superseded by the Deep Review pass — see `skills/kicad/references/deep-review.md`).
- Result schemas live under `skills/kicad/review/schemas/{design_context,review_annotations}.schema.json`.
- Result paths are `analysis/<artifact>.json` (NOT `<sanitized_mpn>.<task>.result.json` — review outputs are run-level, not MPN-level).

### Task → Subagent mapping

When you see a task with `task_type: "review"`:

| `task_id` | Tier | Subagent prompt |
|-----------|------|----------------|
| `design_context` | B (cheaper) | `skills/kicad/review/prompts/design_context.md` |

Same dispatch primitive (Claude Code `Agent` tool); same output-validation contract (validate against `result_schema` after subagent returns); same retry semantics (one retry on hard fail with error context).

### After the design_context task completes

The task writes `analysis/design_context.json`, which the Deep Review pass reads when present. Nothing else needs to run: no current task produces `review_annotations.json`, so there is nothing to merge.
