---
case: log-L9
description: Use when the user ran a script from the board and you should say what its output means.
---

# Reading what it printed

Shapes: log.

```sh
stickypane note cat deploy.log
stickypane log add worklog --time "deploy.sh: staging healthy, build 412 live (deploy.log)"
```

Read the log first, then write one line on what it means, naming the
log. Never write the line before the run: it would be a guess.

Done when: your line came after the run and agrees with the log's last
lines.
