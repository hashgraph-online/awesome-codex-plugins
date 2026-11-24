---
case: api-A10
description: Use when you start to use an outside API you have not called before, and the shape of its responses is a guess from memory.
---

# Learning an outside API

Shapes: api.

```sh
stickypane note write weather.http <<'EOF'
@key = env:WEATHER_KEY

### Today in Seoul
GET https://api.example-weather.com/v1/today?city=seoul&key={{key}}
EOF
stickypane api weather "Today"     # read the real body in the log
```

Then write the file again with what you saw, as checks under the
request: `# @assert response.json("data.temp") exists`, and send it again.

Send one read-only request, read the body in the log, and only then
write the code that reads it, with a check for each field you rely on.
A request that changes the other side is the user's to send.

Done when: every field your code reads has a passing check.
