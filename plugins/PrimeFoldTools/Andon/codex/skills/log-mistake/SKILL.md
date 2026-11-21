---
name: log-mistake
description: Append a one-line entry to the Mistakes Log (symptom, correction, codified). Use when the user says "log this mistake", corrects a mistake you made, or asks to record what went wrong.
---

Codex version of `commands/log-mistake.md` (in testing with codex-cli 0.153.4, Codex turned `orient` and `wrap` into skills by itself but not `log-mistake`). Keep the two in step.

Append a Mistakes Log entry (to `AGENTS.md` or `CLAUDE.md`'s Mistakes Log section, or your mistakes-log file) for what the user says went wrong.

Use this format, with today's date (UTC):

`YYYY-MM-DD — <symptom>. Correction: <how to avoid it next time>. Codified: <test / hook / rule, or "not yet">`

Be specific in the correction. Then ask the real question: **can this be made mechanical?** If a hook or a test could stop this class of mistake from recurring, say so in Codified and offer to build it — that's the difference between writing it down and making it un-repeatable.
