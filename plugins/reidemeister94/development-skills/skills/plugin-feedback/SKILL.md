---
name: plugin-feedback
description: Write development-skills feedback from observed work, or assess a report for useful simplifications.
user-invocable: true
argument-hint: "produce | ingest <report-path>"
---

# Plugin feedback

`produce` writes `docs/reports/development-skills-feedback-YYYY-MM-DD.md` from the current session.
Include the task, used capabilities, observed delays or errors, evidence, and reproducible improvement ideas.
Explain decision reasons. Do not include private reasoning traces or invent token and time measurements.

`ingest <report-path>` treats the report as claims to verify against the current files and observed behavior.
Apply changes within the user's authorization when they fix a demonstrated problem or repeated waste.
Prefer deletion or merging. Keep project facts and avoid a universal rule for one model mistake.
Add an eval only when it can expose a meaningful regression, and tag its owning paths.
Report changes, rejected suggestions with reasons, and verification limits.
