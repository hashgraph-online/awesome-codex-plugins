---
name: book-ideation
description: "Phase 1: Ideation. Concept validation, market gap analysis, competitive matrix, final concept selection."
---

# Phase 1: Ideation

Generate 5-10 concepts from PRD + sources. Each: elevator pitch, target reader, differentiation, scope, difficulty.

**Market Gap Analysis**: existing coverage → gaps → market shifts → reader complaints. Analyze 5+ competing books in matrix (title, author, topic, differentiator, gap we fill).

**Validation**: clarity (1 sentence?) · reader value · differentiation · feasibility · timeliness · scope

Present to user → select ≤3 → merge → confirm single concept.

Output: `ideation.md` (pitch, competitive matrix, gap summary, rationale).

Gate: ideation.md exists, 5+ competitors analyzed, user approved.


## Post-Completion

Update the project dashboard status:

```bash
node {PLUGIN_ROOT}/skills/book-status/scripts/scan-project.js [project-dir] --plugin-root={PLUGIN_ROOT}
```
