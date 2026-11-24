---
case: script-S7
description: Use when a release is near and the checks before it (tests, lint, version numbers) should be one press for the user.
---

# A release check

Shapes: script.

```sh
stickypane note write precheck.sh <<'EOF'
#!/bin/sh
# Checks the release is ready. Tags nothing, pushes nothing.
set -eu
go vet ./...
go test -race ./...
test -z "$(gofmt -l .)"
grep -q '## \[0.4.0\]' CHANGELOG.md
EOF
stickypane note show precheck.sh
```

Only checks. Tagging and pushing are the user's, so they are not in the
script, not even at the end.

Done when: the script changes nothing in the repository or outside it.
