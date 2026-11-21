---
name: update-deps
description: "Use when the user asks to update Python dependencies or pre-commit hooks, keeping the project's pin and configuration style."
user-invocable: true
---

# Update dependencies

For `.pre-commit-config.yaml` or hooks, run `pre-commit autoupdate`, confirm the revision-only diff, then run all configured hooks. If unavailable, resolve GitHub tags while preserving `v` prefixes and quoting.

Otherwise update Python dependencies to latest PyPI releases while preserving each pin style. Use `$ARGUMENTS` or detect the stack:

- `[project].dependencies` plus `uv.lock`: uv;
- otherwise `requirements*.in`: legacy;
- both: uv, with a warning about stray `.in` files.

Shared rules (both stacks):

- Preserve wildcard depth: `0.128.*` → `0.130.*`, `4.*` stays `4.*`, exact stays exact.
- Skip comments and unversioned extras. Report Git dependencies separately instead of resolving them from PyPI; update them by hand and keep their URL form and an exact tag.
- Show the diff, apply on confirmation, then regenerate the lockfile.

When a Gunicorn-hosted ASGI service updates `gunicorn`, `uvicorn`,
`uvicorn-worker`, or `uvloop`, treat the installed server set as one runtime change. A dependency bump
does not authorize changing worker class or entrypoint. Run the
`Connection: close`, graceful-shutdown, and exact Linux-image proof before
declaring success.

## uv stack (standard)

Update `[project].dependencies` and every `[dependency-groups]` list, or only the requested section. Then:

```bash
uv lock --upgrade
uv sync --locked
```

Run configured tests, ruff, and mypy.

## Legacy stack (`*.in` files)

Update the selected `*.in`, then run `uv pip compile <file>.in -o <file>.txt --upgrade`. The `.in` is source; `.txt` is the runtime lock. Suggest a migration to uv.
