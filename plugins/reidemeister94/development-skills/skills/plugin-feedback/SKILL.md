---
name: plugin-feedback
description: "Use when the user asks to write development-skills feedback from observed work, or to assess a feedback report for useful simplifications."
user-invocable: true
argument-hint: "produce | ingest <report-path>"
---

# Plugin feedback

`produce` writes `docs/reports/development-skills-feedback-YYYY-MM-DD.md` from the current session.
Include the task, used development-skills capabilities, observed delays or errors, evidence, and reproducible improvement ideas.
Explain decision reasons. Do not include private reasoning traces or invent token and time measurements.

`ingest <report-path>` treats the report as claims to verify against the current files and observed behavior.
Apply changes within the user's authorization when they fix a demonstrated problem or repeated waste.
Prefer deletion or merging. Keep project facts and avoid a universal rule for one model mistake.
Add an eval case only when it can expose a meaningful regression.
Report changes with the checks that prove them, and rejected suggestions with reasons.
