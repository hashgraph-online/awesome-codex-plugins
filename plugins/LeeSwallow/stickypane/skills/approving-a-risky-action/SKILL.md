---
name: approving-a-risky-action
description: Use when an action is hard to undo (deploy, delete, force push, migrate, send) and needs the user's yes first. Asks on the stickypane board with a form that shows the effect, waits for the button, and acts only on it.
metadata:
  cases: form-F1 form-F3 form-F7 form-F8
---

# Approving a risky action

```sh
# 1. what will happen, in a log the form can show
stickypane log add drop-run "will delete 3 tables: sessions_old (41k rows), carts_tmp, audit_2023"
# 2. a new form, named for this action and this time
stickypane note write drop-tables-1 --open <<'EOF'
---
type: form
title: Delete 3 old tables?
---
![[drop-run]]

## Target
- ( ) staging
- ( ) production

[ Delete ] [ Cancel ]
EOF
# 3. wait, always with a limit; act only on its answer
stickypane wait drop-tables-1 --timeout 10m
```

Shapes: form for the yes; log for the effect before and the outcome
after; a kanban column or a chat line in the recipes below.

## What to read back

| `wait` | Do |
| --- | --- |
| `submitted: Delete` and `Target: staging` | the action, on staging only; then log the outcome |
| `submitted: Cancel` | nothing; say so in one line |
| exit code 3, nothing printed | nothing; `stickypane log add drop-run --time "no answer in 10m, nothing deleted"` |
| `at:` earlier than the form | an old answer: write a new form, do not act |

## How

- Show the effect, not the command: what is deleted, where it goes, how
  many rows, what cannot come back. The form embeds it (`![[drop-run]]`).
- Name each form for one action at one time (`drop-tables-1`,
  `drop-tables-2`); never reuse one that was answered.
- Do not make the risky option the one already picked; the user picks it.
- No safe path you can see? Do nothing and say what you are waiting for.
- The rule, written once: `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md`.
- A choice without risk: `choosing-between-options`. A command the user
  runs: `handing-over-a-command`.

## Recipes

- `references/several-at-once.md`: several changes, each its own yes, in one form.
- `references/a-secret-value.md`: the action needs a key or a password.
- `references/a-review-column.md`: a kanban column that only the user moves cards out of.
- `references/when-the-user-asks-for-the-risk.md`: the user's own instruction is the risky one.
- `references/telling-after-the-safe-path.md`: no answer came, and the user should hear what you did instead.
- `references/an-audit-line.md`: a line in a log right before each destructive step.
