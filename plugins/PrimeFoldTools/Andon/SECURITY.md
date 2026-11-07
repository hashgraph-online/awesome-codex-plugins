# Security Policy

Andon is local-first: the shipped hooks read local transcript and memory files and
write local JSONL logs. They do not call external services or send telemetry.

## Reporting a vulnerability

If you find a vulnerability or unsafe default, please open a GitHub security
advisory if the repository supports it. If the issue is not sensitive, a normal
GitHub issue is fine.

Please do not paste private transcripts, API keys, access tokens, customer data,
or proprietary project files into a public issue. A minimal reproduction with
dummy content is enough.

## Scope

Useful reports include:

- A hook can block when it should fail open.
- A hook reads or writes a surprising path.
- Documentation encourages unsafe installation or overwriting existing config.
- A command can expose private local data by accident.
- A hook accidentally prints private transcript content into a terminal, a log,

  CI output, or a public example.

Out of scope:

- A malicious local user who can already edit your hook files or shell config.
- Problems caused by installing modified third-party copies of the hooks.

## Fixed issues

- **2026-11-05 · auto_orient followed symlinks out of the project (MEDIUM).** Before this
  fix, `hooks/auto_orient.py` loaded `memory/MEMORY.md` or `MEMORY.md` from the open folder
  even when it was a symlink. A hostile repo could link it to a local file outside the
  project and get up to 8,000 bytes of that file into the agent's context. The hook now
  refuses symlinks, real paths outside the project, and non-regular files, and reads only
  the byte cap. If you cloned untrusted repos while running an older copy, check what
  their `MEMORY.md` points to. Marker files left in your temp folder by older copies
  (`auto_orient_*`) are safe to delete.

## Supported versions

Only the current `main` branch is supported before the first tagged release.
