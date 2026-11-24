---
case: script-S10
description: Use when a large job should appear as a script only after the user agreed to it in a form.
---

# After a form

Shapes: form, script.

```sh
stickypane watch --once --note reindex-1 --type form.submitted --timeout 30m --json
stickypane answers reindex-1
stickypane note write reindex.sh <<'EOF'
#!/bin/sh
# Rebuilds the search index: about 20 minutes, the site stays up.
set -eu
./bin/reindex --all
EOF
stickypane note show reindex.sh
```

Two yeses: the form says the job should happen, Run says now. Keep it
for big jobs; for a small one the Run button is enough. Write the script
only if `answers` shows the yes button.

Done when: the script was written after the form's `submitted`, and only
for the yes button.
