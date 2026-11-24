---
case: board-B2
description: Use when the work is cards on a kanban and a card must not go further until the user has looked at it.
---

# A review column

Shapes: board, chat.

```sh
stickypane card move work "drop old tables" --to Review
stickypane chat add chat "'drop old tables' is in Review: 3 tables, 41k rows; move it to Approved to go on"
stickypane watch --once --note work --type card.moved --timeout 30m --json
```

Move a card into Review yourself; only the user moves it out. Go on when
the event says `"to":"Approved"`. Nothing stops you moving it yourself,
so never do: the column is only a gate if you keep to it.

Done when: every card that left Review left it by the user's hand: you
ran no `card move` out of Review, and the event came before you went on.
