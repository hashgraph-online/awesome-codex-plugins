---
case: form-F10
description: Use when the work is ready for the user's verdict: approve it, or ask for changes with a reason.
---

# A review verdict

Shapes: form, note.

```sh
git diff --stat main | stickypane note write diff
stickypane note write verdict-1 --open <<'EOF'
---
type: form
title: Review: cache the price lookups
---
![[pr-cache]]
![[diff]]

## Why (if changes)
>

[ Approve ] [ Request changes ]
EOF
stickypane wait verdict-1 --timeout 30m
```

The form shows the summary and the change inside it, so the verdict is
on what the user read. On "Request changes", do what the reason says,
then ask again with a new form (`verdict-2`).

Done when: the work after a "Request changes" answers its reason, and
the last verdict is Approve.
