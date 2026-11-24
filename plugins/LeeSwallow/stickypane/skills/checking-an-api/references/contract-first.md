---
case: api-A2
description: Use when you are about to change an API and can say beforehand what the responses must look like.
---

# Contract first

Shapes: api.

```sh
stickypane note write orders.http <<'EOF'
@base = http://localhost:8080

### List orders
GET {{base}}/orders?customer=7
# @assert response.statusCode == 200
# @assert response.json("items") exists
# @assert "json" in response.header("Content-Type")
EOF
stickypane api orders --all        # before the change: 0/3 or 1/3
```

Write the checks first and send them: they fail. Change the code until
the last line says `3/3 ✔`. Checks cannot say everything (a whole
schema, a field that must be absent): say what they leave out.

Done when: the log has a failing run from before the change and a
passing run after it.
