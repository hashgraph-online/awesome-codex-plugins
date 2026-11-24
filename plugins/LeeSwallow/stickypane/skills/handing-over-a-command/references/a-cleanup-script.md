---
case: script-S5
description: Use when files or folders should be deleted (build output, caches), and the user runs the deletion.
---

# A cleanup script

Shapes: script.

```sh
stickypane note write clean.sh <<'EOF'
#!/bin/sh
# Deletes dist/ and .cache/ in this project. Nothing else.
set -eu
rm -rf ./dist ./.cache
EOF
stickypane note show clean.sh
```

Name every path in full, starting with `./`. No variables in a path, no
`*`, no path outside the project: what the user reads is exactly what is
deleted.

Done when: the script names each path it deletes, and none of them is
built from a variable or a wildcard.
