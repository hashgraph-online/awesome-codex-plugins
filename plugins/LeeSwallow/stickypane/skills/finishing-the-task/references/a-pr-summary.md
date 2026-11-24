---
case: note-N5
description: Use when the work will become a pull request, and the user should read a summary of it before it is opened.
---

# A PR summary

Shapes: note.

```sh
stickypane note write pr-cache --open <<'EOF'
---
title: PR draft: cache the price lookups
---
**What.** A read-through cache in `price/lookup.go`, 5 min TTL.
**Why.** Price pages took 900 ms; now 180 ms (p95, 10 runs).
**Checked.** `go test ./...` 41/41; `bench.sh` before and after.
**Not touched.** Checkout still reads the database.
**Least sure of.** The TTL: 5 min stale prices may be too long.
EOF
```

Five parts, each a line or two. The last one names where a reviewer
should look hardest. The user edits it and opens the PR; you do not.

Done when: every claim under Checked names the command that showed it.
