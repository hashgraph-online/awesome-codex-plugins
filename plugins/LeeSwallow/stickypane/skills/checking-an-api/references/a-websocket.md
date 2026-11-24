---
case: api-A6
description: Use when you built or changed a WebSocket endpoint and need to see the connection open and messages come back.
---

# A WebSocket

Shapes: api.

```sh
stickypane note write live.http <<'EOF'
### Live updates
# @websocket timeout=5s idle-timeout=1s
# @ws send-json {"type": "subscribe", "topic": "prices"}
# @ws wait 500ms
# @ws close 1000 done
GET ws://localhost:8080/live
# @assert response.received >= 1
EOF
stickypane api live "Live updates"
```

The log is the transcript, what went out and what came back, with a
last line such as `[101 Switching Protocols · 1.1s · Live updates · 2↑ 2↓ · 1/1 ✔]`.
It ends at the timeout, so it cannot watch a connection for long.

Done when: the last line ends in ✔ and the transcript shows a message
from the server.
