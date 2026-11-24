---
case: board-B6
description: Use when the work is cards on a kanban and the user steers by moving them, so the order in To do is the order the user wants.
---

# The user reorders the work

Shapes: board.

```sh
stickypane note cat work               # the order in "To do" now
stickypane card move work "#1" --to Doing
stickypane watch --once --note work --type card.moved --timeout 1s --json
```

Before you take the next card, read the board again: the user may have
moved cards since you last looked. Take the first card in To do, not the
one you had in mind.

Done when: the cards you took left To do in the order the user had them
when you took each one.
