---
case: script-S2
description: Use when a command can say what it would do without doing it (a migration, a sync), and the user should see that before the real run.
---

# Dry run first

Shapes: script, log.

```sh
stickypane note write migrate-dry.sh <<'EOF'
#!/bin/sh
# Shows the SQL the migration would run. Changes nothing.
./migrate --dry-run
EOF
stickypane note write migrate.sh <<'EOF'
#!/bin/sh
# Runs the migration for real. Read migrate-dry.log first.
set -eu
./migrate
EOF
stickypane note show migrate-dry.sh
```

Two scripts: the dry run first, then the real one that points to its
log. Show the real one only after the dry run's log is there.

Done when: `migrate-dry.log` exists from a run before `migrate.log` does.
