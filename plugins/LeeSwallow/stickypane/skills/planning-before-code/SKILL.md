---
name: planning-before-code
description: Use when a change is not small and the user should read the plan, and say go or revise, before you write code. Pins the plan beside the chat as a note and asks for the go with a form.
metadata:
  cases: note-N1 form-F2
---

# Planning before code

```sh
stickypane note write plan-cache --open <<'EOF'
---
title: Plan: cache the price lookups
---
**Goal.** Price pages under 200 ms; now 900 ms.
**Change.** A read-through cache in `price/lookup.go`, 5 min TTL.
**Not touched.** The checkout path keeps reading the database.
**Risk.** Stale prices for up to 5 min after an edit.
**Check.** `go test ./price/...` and the p95 from `bench.sh`.
EOF
stickypane note write plan-cache-go --open <<'EOF'
---
type: form
title: Go with the cache plan?
---
![[plan-cache]]

## Changes to the plan
>

[ Approve ] [ Revise ]
EOF
stickypane wait plan-cache-go --timeout 15m
```

Shapes: note for the plan, form for the go, checklist for the steps once
it is approved (`tracking-the-work`).

## How

- Keep the plan to one screen: goal, change, what is not touched, risk,
  how you will check it. A plan too long to read gets approved unread.
- The form shows the plan inside it (`![[plan-cache]]`), so the user
  reads what they approve.
- `submitted: Revise`: read the line under "Changes to the plan", rewrite
  the plan note, and ask again with a new form (`plan-cache-go-2`).
- `submitted: Approve`: turn the plan into checklist steps and start.
- Exit code 3: no answer yet. Do not start the change; say so in the
  chat and keep to what the plan does not touch.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/a-migration-in-pages.md`: a plan large enough for a book, with its progress beside it.
