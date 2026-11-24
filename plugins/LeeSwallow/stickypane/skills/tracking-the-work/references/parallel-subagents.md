---
case: checklist-C6
description: Use when you split the work among subagents that run at the same time, and the results must come together before the task goes on.
---

# Subagents that meet at the end

Shapes: checklist.

```sh
stickypane todo add split "subagent api: the handlers"
stickypane todo add split "subagent web: the forms"
stickypane todo add split "merge both and run the tests"
# each subagent ticks its own line when it is done
stickypane todo check split "subagent api"
```

Give each subagent one line, named after it, and keep the meeting point
as the last line. Tick that line yourself only after every line above it
is ticked and the merged result passed.

Done when: every line is ticked and the last one was ticked after the
others.
