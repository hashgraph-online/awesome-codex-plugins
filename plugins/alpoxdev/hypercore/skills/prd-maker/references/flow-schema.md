# Planning Package Flow Schema

> JSON schema for `.hyper/prd/[slug]/flow.json` — used for complex planning packages only.

## Contents

- Schema
- Status values
- Rules
- Example: initial state

## Schema

```json
{
  "id": "package-{slug}-{YYYYMMDD-HHmmss}",
  "skill": "prd-maker",
  "mode": "create | update",
  "status": "in_progress | completed | blocked",
  "complexity": "complex",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "slug": "kebab-case-slug",
  "request": {
    "summary": "brief description of the initiative",
    "requester": "who requested it if known",
    "context": "additional context"
  },
  "current_phase": "brief | research | prd | diagram | feature_spec | user_flow | wireframe | sources | preview | validate",
  "outputs": {
    "prd": "prd.md",
    "diagram": "diagram.md",
    "diagram_data": "diagram.data.json",
    "diagram_svg": "diagram.svg",
    "preview": "preview.html",
    "feature_spec": "feature-spec.md",
    "user_flow": "user-flow.md",
    "wireframe": "wireframe.md",
    "sources": "sources.md"
  },
  "phases": {
    "brief": {
      "status": "pending | in_progress | completed",
      "product_name": "feature or product name",
      "problem": "problem to solve",
      "target_users": ["who benefits"],
      "desired_outcome": "business goal",
      "constraints": ["known constraints"],
      "unknowns": ["known unknowns"]
    },
    "research": {
      "status": "pending | in_progress | completed | skipped",
      "queries": ["distinct search queries used"],
      "sources_found": 0,
      "skip_reason": "reason if skipped"
    },
    "prd": {
      "status": "pending | in_progress | completed",
      "sections_written": ["summary", "problem", "scope", "requirements", "metrics"],
      "open_questions_count": 0
    },
    "diagram": {
      "status": "pending | in_progress | completed",
      "branches_written": ["prd", "feature_spec", "user_flow", "wireframe", "open_questions"],
      "rendered": false,
      "renderer": "scripts/render-planning-map.sh"
    },
    "feature_spec": {
      "status": "pending | in_progress | completed",
      "requirements_mapped": ["R1", "R2"],
      "edge_cases_count": 0
    },
    "user_flow": {
      "status": "pending | in_progress | completed",
      "flows_written": ["happy_path", "alternate_paths", "error_paths"]
    },
    "wireframe": {
      "status": "pending | in_progress | completed",
      "screens_written": ["screen names"],
      "states_covered": ["empty", "loading", "error"]
    },
    "sources": {
      "status": "pending | in_progress | completed",
      "entries_logged": 0
    },
    "preview": {
      "status": "pending | in_progress | completed",
      "built": false,
      "builder": "scripts/build-preview.sh"
    },
    "validate": {
      "status": "pending | in_progress | completed | failed",
      "checks_passed": ["scope_clarity", "cross_artifact_alignment", "sources", "open_questions", "change_history"],
      "checks_failed": [],
      "notes": "validation details"
    }
  }
}
```

## Status values

| Status | Meaning |
|--------|---------|
| `pending` | Phase not yet started |
| `in_progress` | Phase currently active |
| `completed` | Phase finished successfully |
| `skipped` | Phase intentionally skipped (research only) |
| `failed` | Phase failed validation (validate only) |
| `blocked` | Waiting on external input (overall status only) |

## Rules

- Set `current_phase` to the first phase with status `in_progress` or `pending`.
- Update `updated_at` on every write.
- When all phases are `completed` or intentionally `skipped`, set top-level `status` to `completed`.
- If `validate` fails, set its status to `failed`, fix the issues, then re-run validation.
- The `id` combines slug and creation timestamp: `package-billing-retry-20260430-100000`.
- The `mode` reflects `create` or `update` from the package workflow.

## Example: initial state

```json
{
  "id": "package-billing-retry-20260430-100000",
  "skill": "prd-maker",
  "mode": "create",
  "status": "in_progress",
  "complexity": "complex",
  "created_at": "2026-04-30T10:00:00Z",
  "updated_at": "2026-04-30T10:00:00Z",
  "slug": "billing-retry",
  "request": {
    "summary": "Create planning package for automatic billing retry flow",
    "requester": "PM",
    "context": "Current failed payments require manual retry"
  },
  "current_phase": "brief",
  "outputs": {
    "prd": "prd.md",
    "diagram": "diagram.md",
    "diagram_data": "diagram.data.json",
    "diagram_svg": "diagram.svg",
    "preview": "preview.html",
    "feature_spec": "feature-spec.md",
    "user_flow": "user-flow.md",
    "wireframe": "wireframe.md",
    "sources": "sources.md"
  },
  "phases": {
    "brief": { "status": "in_progress" },
    "research": { "status": "pending" },
    "prd": { "status": "pending" },
    "diagram": { "status": "pending" },
    "feature_spec": { "status": "pending" },
    "user_flow": { "status": "pending" },
    "wireframe": { "status": "pending" },
    "sources": { "status": "pending" },
    "preview": { "status": "pending" },
    "validate": { "status": "pending" }
  }
}
```

## Sources

> No external sources; content checked 2026-09-21.

This file states this package's own `flow.json` schema, status vocabulary, and phase rules. It cites no external URL and asserts no external fact, so no external source is recorded.
