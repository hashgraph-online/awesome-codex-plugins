---
name: update-deps
description: "Update Python dependencies or pre-commit hooks while preserving the project's pin and configuration style."
user-invocable: true
---

# Update dependencies

For `.pre-commit-config.yaml` or hooks, run `pre-commit autoupdate`, confirm the revision-only diff, then run all configured hooks.
If the command is unavailable, resolve official Git tags while preserving `v` prefixes and quoting.

Otherwise, update Python dependencies to current PyPI releases while preserving each pin style.
Use `$ARGUMENTS` or detect the stack:

- `[project].dependencies` plus `uv.lock`: uv;
- otherwise `requirements*.in`: compiled requirements;
- both: uv, with a warning about stray `.in` files.

Shared rules:

- Preserve wildcard depth: `0.128.*` can become `0.130.*`, `4.*` stays `4.*`, and exact stays exact.
- Skip comments and unversioned extras.
- Report Git dependencies separately. Preserve their transport and exact-tag style unless the user changes it.
- Show the diff, apply it on confirmation, then regenerate the lockfile.
- A dependency bump does not authorize an entrypoint, process model, or runtime topology change.

## uv projects

Update `[project].dependencies` and each selected `[dependency-groups]` list. Then run:

```bash
uv lock --upgrade
uv sync --locked
```

Run the configured tests, lint, and type checks.

## Compiled requirements

Update the selected `*.in`, then run `uv pip compile <file>.in -o <file>.txt --upgrade`.
The `.in` file is the source and the `.txt` file is the generated lock.
