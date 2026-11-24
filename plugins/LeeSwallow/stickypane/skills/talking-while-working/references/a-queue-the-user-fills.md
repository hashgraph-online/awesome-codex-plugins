---
case: checklist-C9
description: Use when the user adds work for you as lines of a checklist while you are busy with something else.
---

# A queue the user fills

Shapes: checklist.

```sh
stickypane todo add queue "rename the config flag"
# between two steps: did the user add a line?
stickypane watch --once --note queue --type item.added --timeout 1s --json
stickypane todo check queue "rename"
```

Each line the user adds comes as an `item.added` event with the line in
`item`. Finish the step you are on, then take the oldest unticked line,
and tick it when it is done.

Done when: every line the user added is ticked or has a chat message
saying why not.
