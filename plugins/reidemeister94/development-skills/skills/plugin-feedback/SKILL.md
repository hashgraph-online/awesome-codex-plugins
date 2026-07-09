---
name: plugin-feedback
description: "Record or apply development-skills plugin feedback. Mode via argument: produce (factual chronicle of plugin interactions this conversation) | ingest <report-path> (apply FIX verdicts, challenged against the Iron Rules). Runs on /plugin-feedback."
disable-model-invocation: true
argument-hint: "produce | ingest <report-path>"
---

# Plugin Feedback

`$ARGUMENTS` selects the mode.

## produce

Factual chronicle of development-skills interactions in this conversation — pure record, no judgment. Write to `docs/reports/development-skills-feedback-YYYY-MM-DD.md`, self-contained:

- **Context** — language, size, test count, framework; the task; why the plugin was involved.
- **Chain of thought** — exhaustive chronological dump of every plugin interaction (skill trigger, phase read, gate, routing decision, agent spawn, tool call, verification, deviation). Per step: plugin instruction quoted · agent action · reasoning · outcome.
- **Friction points** — the steps that wasted effort or misled: file + instruction, what happened.

## ingest <report-path>

The report is input, not truth — most friction is model behavior or edge cases; a change must EARN its place against Iron Rules 3 (simplicity) and 5 (signal). SKIP if any holds: model ignored a clear instruction · fix adds a rule/exception for a one-time event · marginal gain for more words · already covered · shortening would fix it better (the only good FIX direction). FIX only when an instruction is wrong/misleading/repeatedly wasteful AND the fix is net simplification.

- Apply FIX verdicts only, surgically; adding words requires removing at least as many elsewhere (net ≤ 0).
- Write verdicts + summary (FIX/SKIP counts, files changed) to `docs/reports/ingest-YYYY-MM-DD.md`; run pre-commit if a `.py` was touched.
- Expect most friction to SKIP. If >30% FIX, re-examine your rigor.
