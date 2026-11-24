---
case: log-L5
description: Use when you run several destructive steps after a yes, and the user should be able to see afterwards exactly what ran and when.
---

# An audit line

Shapes: log.

```sh
stickypane log add audit --time "about to run: DROP TABLE sessions_old (approved in drop-tables-1)"
psql -c 'DROP TABLE sessions_old'
stickypane log add audit --time "done: sessions_old dropped"
```

One line right before each step, naming the step and the form that
approved it, and one after with the outcome. It is your own record and
not a guard: it proves nothing you did not write down.

Done when: each destructive step has a line before it and a line after
it, and each names its approval.
