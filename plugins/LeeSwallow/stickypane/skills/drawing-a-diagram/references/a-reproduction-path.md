---
case: note-N7
description: Use when you trace a bug through several calls, and the user should see the path and which part of it you have confirmed.
---

# A reproduction path

Shapes: note with a sequenceDiagram.

````sh
stickypane note write bug-path --open <<'EOF'
---
title: Why the cart empties
---
```mermaid
sequenceDiagram
  participant B as browser
  participant S as server
  participant C as cache
  B->>S: POST /cart
  S->>C: set cart (ttl 0)
  Note over S,C: confirmed: ttl is 0 in config.go
  B->>S: GET /cart
  C-->>S: miss (guess, not yet seen)
```
EOF
````

Mark each step confirmed (you saw it in a log or a test) or a guess, in
a `Note over` line. Update the note as guesses become facts.

Done when: every step is marked, and the confirmed ones say where you
saw them.
