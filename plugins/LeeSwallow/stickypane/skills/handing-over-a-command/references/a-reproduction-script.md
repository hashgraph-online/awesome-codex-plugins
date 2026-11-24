---
case: script-S8
description: Use when you found how to make a bug happen, and the user should see it happen rather than take your word for it.
---

# A reproduction script

Shapes: script.

```sh
stickypane note write repro.sh <<'EOF'
#!/bin/sh
# Shows the cart emptying: adds an item, waits 1s, reads the cart.
curl -s -XPOST localhost:8080/cart -d 'item=42'
sleep 1
curl -s localhost:8080/cart    # expected: [42]; today: []
EOF
stickypane note show repro.sh
```

The comment says what to expect and what happens today. Keep it to the
smallest steps that show the bug.

Done when: a run's `repro.log` shows the wrong result the comment names.
