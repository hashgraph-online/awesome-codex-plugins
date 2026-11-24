---
name: checking-an-api
description: Use when you changed, built or are learning an HTTP, WebSocket or gRPC API and want proof that it answers as it should, proof the user can send again with one key. Writes the requests and their checks in a .http note on the stickypane board and sends them (experimental).
metadata:
  cases: api-A1
---

# Checking an API

```sh
stickypane note write users.http <<'EOF'
@base = http://localhost:8080

### Create user
POST {{base}}/users
Content-Type: application/json

{"name": "min"}
# @assert response.statusCode == 201
# @assert response.json("id") exists

### Get user
GET {{base}}/users/1
# @assert response.statusCode == 200
EOF
stickypane api users --all         # sends each, in order; prints each log
stickypane note show users.http
```

Shapes: api (`.http`, experimental), with its log `users.log` beside it.
`stickypane help api` has the whole format: variables, environments,
captures, WebSocket and gRPC.

Each response goes to `users.log`: the request as curl with credentials
hidden, the body, the checks, and a last line such as
`[201 Created · 41ms · Create user · 2/2 ✔]`. On the board the user
picks a request with `j`/`k` and sends it with enter, after a yes.

## How

- Write a check (`# @assert`) for what "it works" means: the status and
  the one field that matters. A request without checks proves only that
  something answered.
- Report the last line of each request (`2/2 ✔`), not "it works".
- The server must run where the user can reach it, or their resend fails.
- `stickypane api <file> <request>` sends at once, without asking.
  Send only requests that change nothing you cannot change back.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/contract-first.md`: write the checks before the code, see them go from 0/n to n/n.
- `references/a-login-flow.md`: log in once, keep the token for the requests after it.
- `references/a-websocket.md`: subscribe, send, and check what came back.
- `references/grpc.md`: call a gRPC method with a JSON body.
- `references/a-request-the-user-sends.md`: a DELETE or a payment, written but not sent.
- `references/learning-an-outside-api.md`: turn a guessed response shape into a checked one.
