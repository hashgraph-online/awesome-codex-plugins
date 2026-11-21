---
name: pw-retry
description: Retry one proven-incomplete Prewalk route from its durable packet without repeating task 1.
---

# Prewalk Retry

For permission/configuration failures, first confirm the reported prerequisite
has changed. Do not relaunch the same packet into the same known blocker.
Only after checking that change, pass `--prerequisite-resolved` if the helper
requires it. The flag acknowledges a verified change; it is not a bypass.

Inspect the live `spawn_agent` schema exactly as for `$prewalk:pw-go`, then run:

Use the absolute helper path resolved from this installed skill, with the shell
working directory set to the user's project. On Windows use `python`.
Pass the actual session ID; do not change directories to the plugin.

```text
python <absolute-plugin-path>/hooks/_pw.py retry <session-id> --schema-fields=<comma-separated live field names>
```

Omit schema fields that are absent. If the helper emits a route, make exactly
the native `spawn_agent` call and printed spawn profile it specifies. Do not
change the message, use unsupported fields, use a named agent, restart
planning, or repeat task 1.

If an executor may still be running, do not spawn. Report the helper's
`pw-reconcile` direction instead.
