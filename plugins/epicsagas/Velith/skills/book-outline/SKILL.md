---
name: book-outline
description: "Phase 2: Outlining. Apply genre-specific structures, generate per-chapter specs, cross-reference map, structural validation."
---

# Phase 2: Outlining

Genre structures: Fiction → 3-Act/15-Beat · Non-fiction → Problem→Principles→Practice→Advanced · Technical → Intro(15%)→Foundations(25%)→Practice(30%)→Advanced(20%)→Reference(10%).

Per-chapter spec: hook · key concepts (3-5) · word target (±10%) · difficulty · prerequisites · source refs.

Cross-reference map as DAG. Rules: no cycles, each concept defined only at first appearance.

Validation by genre:
- **Fiction**: narrative arc complete, protagonist arc natural, conflict escalation, climax placement
- **Non-fiction**: problem→solution linear, difficulty gradient, each part has clear purpose
- **Technical**: novice→expert ordering, code deps correct, exercise gradient smooth

Output: `outline.md` (structure overview, chapter specs, dependency map, validation results).

Gate: outline.md exists, all chapters specified, cross-reference map written.


## Post-Completion

Update the project dashboard status:

```bash
node {PLUGIN_ROOT}/skills/book-status/scripts/scan-project.js [project-dir] --plugin-root={PLUGIN_ROOT}
```
