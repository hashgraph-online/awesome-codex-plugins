---
name: figma-slop-check
description: "Review the craft and technical precision of a requested Figma scope with project canon, measures and visual evidence; classify swap/snap/ask while respecting existing correction authorization."
license: MIT
compatibility: >-
  Read-only. Checks are written for figma-console-mcp tools (figma_execute,
  figma_get_variables, figma_capture_screenshot) with the Desktop Bridge plugin running in Figma
  Desktop. The official Figma MCP server's use_figma also runs Plugin API JavaScript, but this
  skill was not validated there. Reads the figma-canon skill.
metadata:
  author: Thiago Xikota
  version: "1.2.0"
---

# Figma craft and precision

Audit the requested screen/scope with evidence. Use only the applicable design,
copy and handoff criteria; a status reply or documentary typo does not trigger
a full canvas audit. Review is read-only; corrections of your own work or an
approved fix request use the current authorization, without a new per-item yes.

## Applicable sources

- Project map/glossary/DS and current state govern expected values; project
sample-data and locale rules override generic examples.
- [slop-lens.md](references/slop-lens.md): overlap/density, process residue,
visual excess, repetition, copy and communication criteria.
- `references/checks.md`: 11 precision checks and bounded read-only extraction.
- `references/punch-list.md`: severity, swap/snap/ask and scoped decisions.
- `figma-canon` routes API, state, naming, handoff or anomaly detail when this
operation needs it. A numerical rubric can serve a requested scored audit;
concrete blockers and evidence determine readiness, not an automatic 8/10 stamp.

Check the property/relationship in question: bindings, style/scale, component
integrity, sizing, glossary and real pixels. Reuse valid collection, refresh
when live changes/partial failure make it uncertain. Node ids can persist;
validate file/target rather than asserting every id is session-specific.

For visual claims, inspect the affected frame/state and critical elements at
a useful scale. A whole-section overview proves different things from a crop;
no fixed screenshot count proves completeness. Record truncation, variable-mode
limits, stale export risk and what was actually inspected.

## Findings and action

Each finding carries source, node/path, found/expected, severity and action:
**swap** (identical equivalent), **snap** (signed measurable distance) or
**ask** (a new design decision). Approved snaps retain their distance in the
run’s `fixes`; intentional/debt decisions use `.figma-slop-check/decisions.json`
with scope and reason. Do not silently erase debt or invent canon.

A requested audit reports findings without applying them. An authorized fix
can batch its approved scope, preserving lock/preflight and read-back. “Fix all”
does not decide an unresolved product question. New evidence/regression
justifies rechecking; no mandatory double pass, hidden checklist log or
single-agent-versus-fanout ritual. Stop repeated failures for diagnosis.

Handoff adds its pertinent completeness criteria and can reuse this evidence.
Report blockers, warnings and coverage honestly; do not send PR/Figma replies
or publish a deliverable merely because a reviewer marked it ready. Runtime
memory writes follow the runtime contract, not this review skill.
