---
name: handing-over-a-command
description: Use when a command should run on the user's yes rather than by you (a deploy, a cleanup, a release check, a reproduction), so the user reads it, presses Run and sees the output in one place. Puts it on the stickypane board as a script note.
metadata:
  cases: script-S1
---

# Handing over a command

```sh
stickypane note write deploy.sh <<'EOF'
#!/bin/sh
# Deploys build 412 to staging. Takes about 2 minutes.
set -eu
./scripts/build.sh 412
./scripts/push.sh staging 412
curl -fsS https://staging.example.com/health
EOF
stickypane note show deploy.sh
stickypane chat add chat "deploy.sh is on the board: build 412 to staging; press Run when ready"
```

Shapes: script (`name.sh`, or `.ps1`); its output is a log of the same
name, `deploy.log`, beside it. The board asks the user before it runs.

## How

- The first lines say what it does and how long it takes, as comments,
  so the user reads them above the Run button.
- `set -eu` at the top: the script stops at the first failure.
- One script, one job. Fixed paths and names, no `rm -rf $VAR`, no
  wildcards in anything that deletes.
- You do not run it; the user does. Read `deploy.log` after the run
  (`stickypane note cat deploy.log`) before you say how it went.
- A command you can run safely yourself (tests, a read-only check) does
  not need a script; run it.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/dry-run-first.md`: show what would change before the real run.
- `references/a-cleanup-script.md`: a script that deletes, written so it deletes only what it says.
- `references/a-release-check.md`: the checks before a release, without the release.
- `references/a-reproduction-script.md`: a bug the user can see happen by pressing Run.
- `references/after-a-form.md`: the script appears only after the user said yes in a form.
- `references/reading-what-it-printed.md`: say what the run's output means, after reading it.
