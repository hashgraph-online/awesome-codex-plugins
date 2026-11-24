---
case: board-B7
description: Use when the work is cards on a kanban and a card passes from you to another agent (a subagent, a reviewer) to finish.
---

# Handing a card on

Shapes: board.

```sh
stickypane card add work "fix flaky login test; repro: go test -run TestLogin -count 20 ./auth @test-agent" --to "To review"
stickypane card move work "parse dates" --to "To review"
```

Move the card across the column where the other agent picks up, and put
in its text what they need to start: the command that shows the problem,
and their name. A card that needs more than a line points to a note with
`[[name]]`.

Done when: the other agent can start from the card alone, without the
chat.
