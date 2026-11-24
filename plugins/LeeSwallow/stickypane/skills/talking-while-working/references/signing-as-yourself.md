---
case: chat-T7
description: Use when more than one agent writes in the same chat note, and the user must tell who said what.
---

# Signing as yourself

Shapes: chat.

```sh
stickypane chat add chat --as api-agent "handlers done, 12/12 tests pass"
```

Without `--as` a message is signed `agent`. Pick one name for yourself,
say the part of the work you do, and use it for the whole session.

Done when: every message you wrote carries the same name, and no other
agent uses it.
