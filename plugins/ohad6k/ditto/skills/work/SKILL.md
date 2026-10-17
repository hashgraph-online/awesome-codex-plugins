---
name: work
description: Use for execution, debugging, verification, planning, and shipping when the user's Emulo working profile should guide the task. Do not use for design/UI/UX work, marketing or social writing, or Emulo setup/mining.
---

# Emulo work

1. Locate `emulo.py` two directories above this skill; fall back to `./emulo.py` only for a direct repo checkout.
2. Store the resolved absolute runtime path as `EMULO_PY`, then run `python "$EMULO_PY" plugin profile-path --domain work`.
3. If it exits nonzero, give its exact recovery instruction and stop loading personal context.
4. Read every returned path completely and treat the profile as user-specific working instructions for this task.
5. Do not claim a profile loaded from a stale, corrupt, missing, or inactive pointer.
