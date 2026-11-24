---
case: checklist-C5
description: Use when a step on the checklist turns out wrong or no longer needed, and the user should see that the plan changed and why.
---

# When the plan changes

Shapes: checklist, chat.

```sh
stickypane todo add refactor "keep the old function as a wrapper"
stickypane chat add chat "plan changed: 3 callers are in a public API, so the old function stays as a wrapper"
```

Do not delete the step that turned out wrong: leave it unticked, add the
new step under it, and say why in one chat message. The user who looks
back sees both what was planned and what was done.

Done when: the checklist has the new step, the old one is still there,
and the chat has one line with the reason.
