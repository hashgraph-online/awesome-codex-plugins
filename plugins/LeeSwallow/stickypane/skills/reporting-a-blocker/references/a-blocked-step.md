---
case: checklist-C7
description: Use when one step of a tracked task is blocked and you can go on with the others meanwhile.
---

# A blocked step

Shapes: checklist, chat.

```sh
stickypane todo add refactor "BLOCKED: run e2e (needs the browsers, see [[blocked]])"
stickypane chat add chat "e2e is blocked; going on with the unit tests"
stickypane todo check refactor "unit tests"
```

Add the blocked step as its own line starting with `BLOCKED:`, linked to
the report, and leave it unticked: the progress bar should not claim it.
Do the steps that do not depend on it.

Done when: the blocked line is unticked, says what it waits for, and the
chat says what you went on with.
