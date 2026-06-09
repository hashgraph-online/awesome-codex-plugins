---
name: persona-panel
user-invocable: true
tags: [review, personas, content, quality, multi-agent]
model: inherit
description: >
  Use this skill when you need multi-persona parallel content review — domain experts, buyer
  personas, compliance reviewers, or custom catalog entries reviewing a target file or output.
  Dispatches N persona agents in parallel, consolidates verdicts via a configurable mode
  (voting-quorum, hard-gate-threshold, or coordinator-summary), and writes a timestamped sidecar
  to .orchestrator/persona-panel/. Invoked via /persona-panel <target-path>.
---

# Persona Panel Skill

## Overview

Persona Panel runs any number of catalog-defined personas in parallel against a single target
(file, document, or output range). Each persona agent produces a structured verdict. The
coordinator consolidates the verdicts into a final result using one of three configurable modes
and persists a sidecar record for audit and trend-tracking.

The catalog lives in `.claude/personas/*.md` — per-repo, never plugin-central. This is
intentional: climate-research repos need physicists; SaaS repos need buyer personas;
compliance repos need auditors. Plugin-central catalogs block that diversity.

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED,
invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate is
OPEN, continue to Phase 1.

<HARD-GATE>
Do NOT proceed past Phase 0 if GATE_CLOSED. There is no bypass. Refer to
`skills/_shared/bootstrap-gate.md` for the full HARD-GATE constraints.
</HARD-GATE>

## Phase 1: Catalog Discovery

Load the per-repo persona catalog via `loadCatalog()` from
`scripts/lib/persona-panel/catalog-loader.mjs`.

**Failure modes — all are hard stops:**

**(a) `.claude/personas/` directory missing:**
```
Error (exit 2): .claude/personas/ directory not found in this repo.
Create persona files there to use /persona-panel.
See templates/personas/ for starter templates (issue #458).
```

**(b) `.claude/personas/` present but empty (no `.md` files):**
```
Error (exit 2): .claude/personas/ exists but contains no persona files (*.md).
Add at least one persona file to use /persona-panel.
See templates/personas/ for starter templates (issue #458).
```

**(c) `--personas <name>` arg specified but `name` not found in catalog:**
```
Error (exit 1): Persona "<name>" not found in .claude/personas/.
Available personas: <list of names from catalog>.
```

**(d) Malformed YAML frontmatter in a catalog file:**
```
Error (exit 1): Malformed YAML in .claude/personas/<filename>.md at line <N>: <error>.
Fix the frontmatter before running /persona-panel.
```

**Model validation (H2 security guard):** The catalog loader validates each persona's `model:`
field against `MODEL_ID_RE` + `ALLOWED_MODEL_ALIASES` from `scripts/lib/agent-frontmatter.mjs`
at load time. A persona with an invalid model string triggers failure mode (d) with an
informative message: "invalid model '<value>' — must be a Claude model ID or alias
(inherit|sonnet|opus|haiku)".

**`output_contract` structural pre-check (H3 security guard):** After YAML parse and before
AJV compile, the loader inspects each persona's `output_contract` object for forbidden keys:
`$ref`, `$defs`, `allOf`, `anyOf`. Any occurrence triggers failure mode (d). This structural
pre-check runs BEFORE `ajv.compile()`. The AJV compile call wraps in a 2-second AbortSignal
timeout to guard against pathological schema inputs.

After successful load, emit a one-line status banner:
```
Catalog: [N] personas loaded from .claude/personas/. Tier breakdown: domain-expert [N], buyer-persona [N], compliance [N], custom [N].
```

If `--personas <names>` was passed, filter to the named subset. Report the active set.

## Phase 2: Target-Input-Resolution

Resolve the `<target-path>` argument against the project root.

1. Expand to absolute path (relative inputs are resolved from `git rev-parse --show-toplevel`).
2. Call `validatePathInsideProject(absolutePath, projectRoot)` from
   `scripts/lib/path-utils.mjs`. This function performs a two-phase lexical + realpath guard.
   - If the path resolves outside the project root: exit 1 with message
     "Target path escapes project root — /persona-panel only reviews files inside the repo."
3. Confirm the file exists and is readable. If not: exit 1 with "Target file not found: <path>".
4. If a range was specified (`--lines <start>-<end>`), validate that start ≤ end and both are
   positive integers.

Store the resolved absolute path as `$TARGET`.

## Phase 3: Parallel Dispatch

Dispatch one Agent per persona from the active catalog set.

**Model selection per persona:**
- If `persona.model` is a full Claude model ID (`MODEL_ID_RE`): use it as-is.
- If `persona.model` is `opus` or unset AND `persona.tier == 'domain-expert'`: override to
  `claude-opus-4-7` (empirically validated — Opus finds real problems Sonnet misses; see vault
  learning `[[persona-opus-finds-real-failing-cibadge]]`).
- Otherwise: use the persona's declared model alias.

**Agent dispatch contract:**
```
Agent({
  subagent_type: "general-purpose",
  model: <resolved model ID>,
  prompt: <buildPersonaPrompt(persona, $TARGET)>,
  tools: ["Read", "Grep", "Glob"]
})
```

Use `buildPersonaPrompt(persona, target)` from `scripts/lib/persona-panel/persona-runner.mjs`
to compose the prompt. The runner wraps `evaluation_criteria` entries in
`<persona-criteria>...</persona-criteria>` delimiters (security M1: persona body is treated as
data, not free-form instructions; see `persona-format.md` for the full rationale).

**Concurrency cap (security M2):** Maximum 20 personas per panel run. If the active set exceeds
20, emit a warning and truncate to the first 20 alphabetically:
```
Warning: Persona set truncated to 20 (cap). Omitted: <names>.
```

**run_in_background:** `false` for all agents. Do not proceed to Phase 4 until ALL agents
complete.

**Dispatch summary line (before dispatch):**
```
Dispatching [N] persona agents in parallel. Target: <$TARGET>. Mode: <consolidation-mode>.
```

## Phase 4: Konsolidierung (Consolidation)

After all agents complete, run consolidation via `scripts/lib/persona-panel/consolidator.mjs`.

**Three consolidation modes** (set by `--mode` arg, default: `voting-quorum`):

### `voting-quorum` (default)

Deterministic M-of-N threshold. Default M = ceil(N / 2) + 1 (simple majority). Override with
`--quorum <M>`.

- Count personas whose `verdict == "pass"`.
- If pass-count >= M: final-verdict = `"pass"`.
- If pass-count < M: final-verdict = `"fail"`.
- Tie: impossible when M > N/2. If M == ceil(N/2) exactly and count == M - 1: final-verdict =
  `"fail"` (ties go to FAIL).

### `hard-gate-threshold`

Strict M-of-N where default M == N (unanimity). Override with `--threshold <M>`.

- If ALL N personas pass: final-verdict = `"pass"`.
- If any persona returns `"fail"`: final-verdict = `"fail"`.
- If any persona returns `"warn"` and no failures: final-verdict = `"warn"`.
- Tie-break: ties go to FAIL.

### `coordinator-summary`

LLM aggregate via coordinator. The coordinator reads all persona outputs and produces a
synthesized summary verdict.

**WARN (required — emit to BOTH stderr AND sidecar `consolidation.aggregator_warning`):**
```
Warning: coordinator-summary mode triggers an additional LLM call (the coordinator aggregation
step). This incurs extra token cost. Use voting-quorum or hard-gate-threshold for deterministic,
zero-extra-LLM-call consolidation.
```

For each persona output, parse the structured block (see `persona-format.md` Output Contract).
Validate that `verdict ∈ {"pass", "fail", "warn"}` — if a persona output lacks a valid verdict,
treat it as `"fail"` and record it in `dissenting_personas` with reason `"missing-verdict"`.

Emit a consolidation summary:
```
Consolidation ([mode]): [pass-count] pass / [fail-count] fail / [warn-count] warn — Final: <verdict>
Dissenting: <names> (if any)
```

## Phase 5: Sidecar-Persist + Report

Write the sidecar record and emit the final report.

### Sidecar Persistence

**Run ID generation (H1 security guard):**
```js
const runId = randomUUID().slice(0, 8); // format: [a-z0-9-]{8}
```
Validate: `runId` MUST match `/^[a-z0-9-]{1,64}$/`. Reject and regenerate if it does not.

**Timestamp format for filename:** `^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}(\.\d+)?Z?$`
(filename-safe ISO — colons replaced with hyphens).

Example: `2026-05-20T14-30-00Z-a1b2c3d4.json`

**Path:** `.orchestrator/persona-panel/<isoTs>-<runId>.json`

Validate the sidecar target path with `validatePathInsideProject(sidecarAbsPath, projectRoot)`
(H1 path guard) before writing.

**Schema validation (security M3 — validate BEFORE write):**
Validate the sidecar object against `agents/schemas/persona-panel-sidecar.schema.json` using
`validateAgentOutput()` from `scripts/lib/agent-output-schema.mjs` (AJV 2020-12). If
validation fails: print the AJV errors to stderr and exit 1 — never write an invalid sidecar.

**Write via `writeJsonAtomic()` from `scripts/lib/io.mjs`** (atomic tmp-then-rename to prevent
partial writes).

**Sidecar schema shape** (matched by `agents/schemas/persona-panel-sidecar.schema.json`):

```json
{
  "run_id": "<string, 1-64 chars [a-z0-9-]>",
  "target": "<absolute path to reviewed file>",
  "personas_invoked": [
    {
      "name": "<persona name>",
      "version": "<integer>",
      "model": "<full model ID used>",
      "prompt_hash": "<sha256 of canonicalized prompt — see persona-format.md>",
      "timestamp_start": "<ISO 8601>",
      "timestamp_end": "<ISO 8601>",
      "token_usage": {
        "input": "<integer>",
        "output": "<integer>",
        "cache_read": "<integer>",
        "cache_creation": "<integer>"
      }
    }
  ],
  "outputs": [
    {
      "persona_name": "<string>",
      "verdict": "<pass|fail|warn>",
      "rationale": "<string, max 4096 chars>",
      "recommendations": ["<string>"]
    }
  ],
  "consolidation": {
    "mode": "<voting-quorum|hard-gate-threshold|coordinator-summary>",
    "final_verdict": "<pass|fail|warn>",
    "pass_count": "<integer>",
    "fail_count": "<integer>",
    "warn_count": "<integer>",
    "dissenting_personas": ["<name>"],
    "audit_reason": "<string>",
    "aggregator_warning": "<string | null>"
  }
}
```

**Token-usage contract (H4):** Each `personas_invoked` entry records `token_usage` from the
Anthropic API response: `{ input, output, cache_read, cache_creation }`. Agents that do not
return usage data record all fields as `0`.

### Final Report

Emit to stdout:

```
## Persona Panel Report

Target: <$TARGET>
Personas: <N> invoked | Mode: <mode>
Final verdict: <PASS|FAIL|WARN>

| Persona | Tier | Verdict | Rationale (excerpt) |
|---------|------|---------|---------------------|
| <name>  | ...  | pass    | ...                 |
| <name>  | ...  | fail    | ...                 |

Dissenting: <names or "none">
Sidecar: .orchestrator/persona-panel/<filename>.json
```

If `final_verdict == "fail"`: exit with code 1 so CI and wave-executor hooks can gate on the
result. If `final_verdict == "warn"`: exit 0 with a warning line on stderr. If
`final_verdict == "pass"`: exit 0.

## Critical Rules

- **NEVER** dispatch more than 20 personas per panel (security M2 cap).
- **NEVER** write a sidecar that fails schema validation — validate BEFORE write (security M3).
- **NEVER** skip `validatePathInsideProject` for the target path OR the sidecar output path (H1).
- **NEVER** use `run_in_background: true` for persona agents — lose coordination ability.
- **ALWAYS** validate `model:` fields from the catalog against `MODEL_ID_RE` + aliases (H2).
- **ALWAYS** run `output_contract` structural pre-check before `ajv.compile()` (H3).
- **ALWAYS** emit the `aggregator_warning` to BOTH stderr and sidecar when using
  `coordinator-summary` mode.
- **ALWAYS** treat missing persona verdict as `"fail"` — never silently skip or default to pass.
- Ties in consolidation go to FAIL, not pass or warn.

## Anti-Patterns

- Running without a catalog — Phase 1 must gate on catalog existence.
- Using a single persona as a "quick check" — dispatch all catalog members unless `--personas`
  restricts deliberately. The value is the N-dimensional view.
- Ignoring dissenting personas in `voting-quorum` — record them in the sidecar even when the
  majority passes. They are the signal for trend-tracking (#459).
- Writing the sidecar before schema validation passes — invalid sidecars corrupt trend analysis.
- Calling `ajv.compile()` without the AbortSignal timeout — pathological schemas can block the
  event loop indefinitely.

## See Also

- `commands/persona-panel.md` — argument parsing and CLI contract
- `agents/schemas/persona-panel-sidecar.schema.json` — sidecar JSON Schema (Draft 2020-12)
- `scripts/lib/persona-panel/catalog-loader.mjs` — loadCatalog() implementation
- `scripts/lib/persona-panel/persona-runner.mjs` — buildPersonaPrompt() implementation
- `scripts/lib/persona-panel/consolidator.mjs` — consolidation logic (3 modes)
- `skills/persona-panel/persona-format.md` — persona file format specification
- `skills/wave-executor/wave-loop.md` — Persona-Gate hook (Phase 5b/3b, added in #458)
- `scripts/lib/path-utils.mjs` — validatePathInsideProject()
- `scripts/lib/io.mjs` — writeJsonAtomic()
- `scripts/lib/agent-frontmatter.mjs` — MODEL_ID_RE, ALLOWED_MODEL_ALIASES
