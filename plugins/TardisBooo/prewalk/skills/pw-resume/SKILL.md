---
name: pw-resume
description: Start the explicit manual-root fallback after switching the current Codex thread to the configured executor model.
---

# $prewalk:pw-resume - continue after a manual model switch

Run this only after `pw-go` requested the manual fallback and the user completed
`/model <executor>`:

Use the absolute helper path resolved from this installed skill, with the shell
working directory set to the user's project. On Windows use `python`.
Pass the actual session ID; do not change directories to the plugin.

```text
python <absolute-plugin-path>/hooks/_pw.py resume <session-id>
```

The helper reloads and prints the durable Handoff Packet. Continue the remaining
todos in the current thread, strictly in order; do not reconstruct context,
restart exploration, or repeat task 1. Verify every item before completing it.
Record the explicit manual fallback result with:

```text
python <absolute-plugin-path>/hooks/_pw.py complete <session-id>
python <absolute-plugin-path>/hooks/_pw.py incomplete <session-id> <reason>
```

These commands reject native agent routes; native completion remains owned by
the bound agent's `SubagentStop` hook.
