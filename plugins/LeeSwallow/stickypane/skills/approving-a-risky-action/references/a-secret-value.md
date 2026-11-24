---
case: form-F6
description: Use when the next step needs a secret (an API key, a password, a token) from the user.
---

# A secret value

Shapes: form.

```sh
stickypane note write key-ready-1 --open <<'EOF'
---
type: form
title: Set STRIPE_KEY
---
Put the key in `.env` as `STRIPE_KEY=...` (not here: a form's answers
stay in a plain file in `.sticky/`). Then press Done.

[ Done ] [ Skip ]
EOF
stickypane wait key-ready-1 --timeout 15m
```

Never ask for the value in a form or a chat: both are files the board
keeps. Ask the user to put it where the program reads it, and only wait
for the button.

Done when: no secret appears in `.sticky/` (`grep -r STRIPE_KEY= .sticky`
finds nothing) and the program reads it from the environment.
