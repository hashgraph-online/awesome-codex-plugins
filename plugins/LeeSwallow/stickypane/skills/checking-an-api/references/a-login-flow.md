---
case: api-A3
description: Use when the requests you check need a login first, and the token should not be copied by hand or end up in the chat.
---

# A login flow

Shapes: api.

```sh
stickypane note write auth.http <<'EOF'
@base = http://localhost:8080
@password = env:API_PASSWORD

### Log in
POST {{base}}/login
Content-Type: application/json

{"user": "min", "password": "{{password}}"}
# @assert response.statusCode == 200
# @capture file token {{response.json.token}}

### Me
GET {{base}}/me
Authorization: Bearer {{token}}
# @assert response.statusCode == 200
EOF
stickypane api auth --all
```

The password comes from the environment or the project's `.env`; the
token is captured, not pasted. The log hides credentials in headers,
not in bodies: do not put a secret in a body you send.

Done when: both requests end in ✔, and no password or token is in the
`.http` file or the chat.
