---
case: form-F9
description: Use when a new task will raise the same few questions (test style, scope, branch), and asking them once at the start saves interrupting later.
---

# Preferences up front

Shapes: form.

```sh
stickypane note write start --open <<'EOF'
---
type: form
title: Before I start
---
## Tests
- ( ) unit tests only
- ( ) unit and e2e

## Scope
- [ ] also fix the lint warnings
- [ ] also update the docs

## Branch name
>

[ Start ]
EOF
stickypane wait start --timeout 15m --json
```

Five questions or fewer; more and the user gives up. Read the answers
once and keep to them: do not ask the same thing again later.

Done when: the work follows every answer, and no later question repeats
one of them.
