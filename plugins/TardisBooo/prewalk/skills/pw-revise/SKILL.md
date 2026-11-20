---
name: pw-revise
description: Revise a durable Prewalk checkpoint in the active root session, re-verifying task 1 when needed.
---

# /pw-revise `<changes>` — revise the plan on the frontier

Run this to fetch the revision instructions for the current checkpoint:

Use the absolute helper path resolved from this installed skill, with the shell
working directory set to the user's project. On Windows use `python`.
Pass the actual session ID; do not change directories to the plugin.

```text
python <absolute-plugin-path>/hooks/_pw.py revise <session-id> <revision-text>
```

Then follow its output:

- **Re-explore only what the revision affects** — do not redo the whole
  exploration.
- **Update the todo list** (`update_plan` / `todo`) to reflect the requested
  changes (each item still needs a concrete file path + a verification word).
- **Re-verify task #1** only if the revision changed it.
- Keep only real work in the updated structured Handoff Packet. Save it inside
  the project and run `_pw.py checkpoint <session-id> <absolute-packet-file>`
  using the absolute helper path. Require a checkpoint_ready receipt, then stop
  for user review. Do not rely on Stop to persist the revised packet.

You stay on the frontier (planner) model. When the revised plan is ready, the
user runs `/pw-go` to hand off. If the script says there is no active
checkpoint, reply with a single line saying so and end your turn.
