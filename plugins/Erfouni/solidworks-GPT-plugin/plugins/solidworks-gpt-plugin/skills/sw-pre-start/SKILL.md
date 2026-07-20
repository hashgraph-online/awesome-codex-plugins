---
name: sw-pre-start
description: Load mandatory SolidWorks conventions, design rules, task-relevant knowledge documents, standards data, and initial design-rule checks before any modeling or CAD code. Use at the beginning of every SolidWorks create, modify, repair, assembly, drawing, or API task, before touching SolidWorks; also use its final phase before save and export.
---

# SolidWorks Pre-Start

Run all phases in order. Do not model, generate CAD code, or call a SolidWorks
API until Phases 1 through 4 complete or a documented KB outage forces the
offline fallback.

Set `KB_HOST` from `SW_KB_HOST`; default to
`https://sw-plugin.ideep.org`. Use `curl` through the shell for every runtime
request. Quote the complete URL. Do not use browser or web-fetch tools for this
KB.

## Phase 1: conventions

Run:

```text
curl -sS "{KB_HOST}/api/knowledge?kind=convention"
```

Load every returned `body` once per Codex task. Treat conventions as hard rules
unless the user explicitly overrides one. Read Persian and English documents.
Expect conventions for metric units, ISO 2768-mK defaults, material defaults,
fully-defined parametric sketches, `PRJ-<part>-NNN` naming, `work/` and
`exports/` paths, clean rebuilds, assigned material, rule checks, STEP, and
drawing PDF deliverables.

If required geometry or safety input remains unknown, ask the user; a KB
default does not authorize inventing geometry-driving values.

## Phase 2: active design rules

Run:

```text
curl -sS "{KB_HOST}/api/design-rules"
```

Skip entries with `deprecated: true`. Internalize the rest by category.
Enforce severity as follows:

- `critical`: block until resolved;
- `high`: fix before completion;
- `medium`: fix unless the user explicitly overrides;
- `low`: advisory, apply when possible.

## Phase 3: task knowledge

Create a concise URL-encoded query for the requested component and likely
SolidWorks features, then run:

```text
curl -sS "{KB_HOST}/api/knowledge/search?q={query}"
```

Read the top five to eight results, or up to ten for a complex assembly,
thread, or sheet-metal task. Prioritize `playbook`, then `reference`,
`strategy`, and `convention`. Read the complete reference for every SolidWorks
API method about to be used. Fetch a known document with
`GET /api/knowledge/{slug}` when necessary.

## Phase 4: initial rule check

Build a JSON object from known values. Omit unknown keys; never fabricate them.
Typical fields are:

```json
{
  "welded": false,
  "tolerance_class": "m",
  "process": "machined_aluminum",
  "wall_thickness_mm": 2.0,
  "nominal_dimension_mm": 50.0,
  "fastener": "M8",
  "hole_mm": 9.0,
  "material": "6061-T6"
}
```

POST it with `curl`:

```text
curl -sS -X POST "{KB_HOST}/api/check-context" -H "Content-Type: application/json" --data-binary "@<context.json>"
```

React to each result:

- `pass`: continue;
- `fail`: stop CAD work and fix the input, explaining the rule and change;
- `warn`: flag it and fix when possible;
- `advisory`: apply it as a design constraint;
- `na`: ignore it.

Do not proceed while `summary.fail` is greater than zero.

## Phase 5: standards on demand

Query only the table needed for the current decision:

- `GET /api/standards/materials[/<name>]` for density, yield, and modulus;
- `GET /api/standards/fits` for ISO 286 hole and shaft deviations;
- `GET /api/standards/clearance_holes[/<designation>]` for ISO 273 holes;
- `GET /api/standards/tolerances_iso2768` for general tolerances;
- `GET /api/standards/fasteners[/<designation>]` for fastener geometry;
- `GET /api/standards/sheet_metal_gauges` for gauge thickness;
- `GET /api/standards/preferred_numbers` for R-series dimensions.

Record units. The KB database convention is mm, MPa, and g/cm3.

## Phase 6: final rule check

After geometry is complete and before final save or export, POST a more
complete final context to `/api/check-context`. Resolve every `fail`; document
all advisories in the session `issues` narrative.

## Offline and error behavior

- Unreachable server: record `KB offline - proceeding without pre-start
  checks` and continue using verified engineering context.
- Search `404`: continue with available knowledge.
- Check-context `422`: retry once with fewer fields, then continue and record
  the issue.
- `5xx` or timeout: skip the failed phase and record it.

The KB accelerates the task; it is not a gatekeeper.
