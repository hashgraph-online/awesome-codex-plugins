---
case: api-A8
description: Use when a request changes something that cannot be changed back (a DELETE, a payment, a message sent to people), so the user, not you, should send it.
---

# A request the user sends

Shapes: api.

```sh
stickypane note write refunds.http <<'EOF'
@base = https://api.example.com

### Refund order 812 (sends money back: user only)
POST {{base}}/orders/812/refund
# @assert response.statusCode == 200
EOF
stickypane note show refunds.http
stickypane chat add chat "refunds.http has the refund for order 812; select it and press enter to send it"
```

Write it and do not send it: `stickypane api` sends without asking. On
the board, enter asks the user first. Say in the request's name that it
is the user's to send.

Done when: `refunds.log` has no run of yours, only the user's.
