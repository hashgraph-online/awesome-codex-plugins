---
name: plugin-feedback
description: "Produce factual development-skills feedback or ingest a report to apply only evidence-backed simplifications."
user-invocable: true
argument-hint: "produce | ingest <report-path>"
---

# Plugin feedback

`produce` writes `docs/reports/development-skills-feedback-YYYY-MM-DD.md` with the task context, plugin/skill actions, observed outcomes, friction, and reproducible eval ideas. Record events and evidence, not private reasoning.

`ingest <report-path>` treats the report as a hypothesis. Change the plugin only when an instruction is demonstrably wrong or repeatedly wasteful, and the fix is simpler than the current text.

Prefer deletion or merging. Do not add an exception for one model mistake.

Add an eval only when the Pydantic schema can observe its outcome. Tag the owning paths so normal checks select it only when relevant. Report fixes, rejected suggestions, changed files, and verification. Expect most suggestions to be rejected.
