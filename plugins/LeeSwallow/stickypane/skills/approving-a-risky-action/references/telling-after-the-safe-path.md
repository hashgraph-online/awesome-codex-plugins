---
case: chat-T8
description: Use when a wait for approval ran out, you took the safe path, and the user should find out what happened when they come back.
---

# Telling after the safe path

Shapes: chat, log.

```sh
stickypane wait deploy-1 --timeout 10m || code=$?
stickypane log add deploy-run --time "no answer in 10m: did not deploy; build 412 is ready"
stickypane chat add chat "no answer on deploy-1, so nothing was deployed; build 412 waits for your yes"
```

The chat line says what you did not do, what is ready, and what would
start it. Leave the form where it is: when the user comes back, they
answer it and you wait again.

Done when: nothing risky ran after the timeout, and the chat and the log
each have one line saying so.
