---
case: board-B1
description: Use when several agents take cards from one kanban, and the user should see who holds which card.
---

# Lanes for agents

Shapes: board.

```sh
stickypane card add work "login API @api-agent" --to Doing
stickypane card move work login --to Review
stickypane card move work login --to Done
```

End a card's text with the name of the agent that holds it, the same
name every time (the one you sign the chat with). Move only the cards
that carry your name.

Done when: each card in Doing names one agent, and the cards you moved
carry your name.
