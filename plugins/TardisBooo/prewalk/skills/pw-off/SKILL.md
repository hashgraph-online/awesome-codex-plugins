---
name: pw-off
description: Disarm Prewalk for the current Codex session without changing files or todos.
---

# Prewalk Off

Run:

Use the absolute helper path resolved from this installed skill, with the shell
working directory set to the user's project. On Windows use `python`.
Pass the actual session ID; do not change directories to the plugin.

```text
python <absolute-plugin-path>/hooks/_arm.py disarm <session-id>
```

Report the result and do not alter the task or workspace.
