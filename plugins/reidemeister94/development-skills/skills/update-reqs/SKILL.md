---
name: update-reqs
description: "Use when user wants to update a pip requirements .in file (requirements.in or requirements-dev.in) with the latest PyPI versions while preserving each line's version-specifier pattern."
user-invocable: true
---

# Update Requirements

Bump packages in a `*.in` file (`requirements.in`, `requirements-dev.in`, or any other) to their latest PyPI versions, preserving each line's wildcard depth. Target file from `$ARGUMENTS`, else `requirements.in`.

- Preserve wildcard depth: `fastapi==0.128.*` + latest `0.130.0` → `fastapi==0.130.*`; `commitizen==4.*` stays `4.*`; an exact pin (`pkg==1.2.3`) bumps to the new exact.
- Skip: comments, blank lines, git deps (`@` / `git+`), and `pkg[extra]` lines without a version.
- Show the diff, apply on confirmation, then recompile the lockfile: `uv pip compile <file>.in -o <file>.txt --upgrade`.

The `.in` is hand-edited; the `.txt` is the generated lockfile installed by the runtime/Dockerfile (and, for `requirements-dev.txt`, by local dev and the CI test image).
