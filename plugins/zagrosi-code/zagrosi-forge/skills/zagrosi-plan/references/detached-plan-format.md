# Authoring for Detached Execution

Choose this route before writing when implementation must preserve a frozen
planning tree. Use physical `codex-plan.md`, `reviews/codex.md`, and sections;
omit `compact_plan` metadata everywhere. Keep shared evidence/decisions in the
plan and link them from sections. Use the requested depth in plan metadata;
the example below uses `lean`. Replace its requirements and evidence with the
actual inspected task, preserving the source spec.

Run normal plan postflight, then this read-only compatibility check **before**
approval, admission hashes, or freezing:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py lint-plan-artifacts --planning-dir "{planning_dir}" --for-detached --strict
```

Repair failures while the plan is mutable. A passing check proves artifact
compatibility; setup still authenticates the operator-approved admission and
source hashes. Follow the implementation skill's detached operations at handoff.
Never rewrite an already admitted tree to convert formats.

## Minimal worked example

### `spec.md`

```markdown
# Label normalization

REQ-001: Strip label edge whitespace while preserving internal whitespace and case.
```

### `codex-plan.md`

```markdown
<!-- FORGE_META
{"artifact_type":"implementation_plan","depth_mode":"lean","source":"spec.md"}
END_FORGE_META -->
# Label normalization plan

## Goal and scope
REQ-001 strips label edges. Non-goals: case changes, new input types, or storage changes.

## Evidence and decision
Inspected `src/labels.py`, callers in `src/views.py`, existing tests in
`tests/test_labels.py`, and runtime `pyproject.toml` with `rg --files`.
Current helper preserves edge whitespace. Assumption: callers supply strings.
DEC-001: reuse the existing helper. Rationale: its ownership fits; reject a new layer.

## Design and contract
`normalize(value: str) -> str` trims edges, preserves internal whitespace and case,
returns empty for empty input, and is idempotent. Errors and input types stay unchanged.
Section `section-01-normalize` owns `src/labels.py` and `tests/test_labels.py`.

## Tests and acceptance
REQ-001: `test_trim_edges` expects `" Ada  Lovelace " -> "Ada  Lovelace"`;
cover empty and already normalized strings. See section Tests first for the command.
Done when targeted regression checks pass and the contract holds for callers.

## Risks and rollback
RISK-001: case drift; assert exact results. Security/privacy: no I/O.
Migration: none; keep caller compatibility. Rollback: revert the two owned files.
```

### `reviews/codex.md`

```markdown
# Plan review

Reviewed: REQ-001, inspected callers, whitespace/empty-input cases, exact ownership,
regression tests, compatibility, and rollback. No material findings or unresolved risks.
Verdict: pass.
```

### `sections/index.md`

```markdown
<!-- PROJECT_CONFIG
runtime: python-uv
test_command: uv run pytest tests/test_labels.py
END_PROJECT_CONFIG -->
<!-- SECTION_MANIFEST
section-01-normalize
END_MANIFEST -->
Dependencies: none. Execution order: section-01-normalize. Parallel: no siblings.
```

### `sections/section-01-normalize.md`

```markdown
# section-01-normalize

## Goal
Implement REQ-001; use the contract and DEC-001 in `../codex-plan.md`.

## Dependencies
None.

## Owned files
This section owns exactly these paths:
- `src/labels.py`
- `tests/test_labels.py`

## Tests first
REQ-001: Case: `test_trim_edges` plus empty/already normalized inputs.
Expected: `" Ada  Lovelace " -> "Ada  Lovelace"`, preserving internal spaces and case.
Expected failure: current helper preserves edges.
Command: `uv run pytest tests/test_labels.py`.

## Implementation contract
Update the existing helper according to the plan's Design and contract.
No new dependency or input coercion.

## Acceptance and rollback
REQ-001 is complete when the regression command passes for the documented cases.
RISK-001 and rollback: see `../codex-plan.md`; stop if inspected caller assumptions fail.
```
