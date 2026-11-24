---
case: chat-T5
description: Use when the user asks for something you think is risky (force push to main, skip the tests), and you should say why before doing it.
---

# When the user asks for the risk

Shapes: chat, form.

```sh
stickypane chat add chat "force-pushing main drops 2 commits by someone else (a1b2c3, d4e5f6); a form is up"
stickypane note write force-push-1 --open <<'EOF'
---
type: form
title: Force-push main anyway?
---
It drops a1b2c3 and d4e5f6, pushed by another person yesterday.

[ Force-push ] [ Push a merge instead ]
EOF
stickypane wait force-push-1 --timeout 10m
```

Say once, in one chat line, what you think will go wrong, then let the
form decide. If the user presses the risky button, do it: the choice is
theirs.

Done when: the chat has your reason and the action matches the button.
