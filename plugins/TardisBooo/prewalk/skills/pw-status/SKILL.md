---
name: pw-status
description: Show the current Prewalk phase, models, routing attempts, checkpoint evidence, remaining todos, and last error.
---

# Prewalk Status

Run and report the output exactly:

Use the absolute helper path resolved from this installed skill, with the shell
working directory set to the user's project. On Windows use `python`.
Pass the actual session ID; do not change directories to the plugin.

```text
python <absolute-plugin-path>/hooks/_arm.py status <session-id>
```
