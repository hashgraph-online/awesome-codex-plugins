# Context policy

## Cheap discovery order

1. `AGENTS.md` / project instructions.
2. `git status --short` and `git diff --stat`.
3. top-level manifests (`package.json`, `pyproject.toml`, `go.mod`, etc.).
4. targeted `rg` for the symbol/route/component/error.
5. open only matching files and immediate dependencies.
6. expand outward only when evidence requires it.

## Usually ignore

`.git`, `node_modules`, `.next`, `dist`, `build`, `coverage`, `.venv`, `vendor`, caches, binaries, source maps, minified files, large lockfiles.

Lockfiles may need to be changed by package tooling, but usually do not need to be read into model context.

## Large-file rule

If a file is large, find symbols/line ranges first. Read slices rather than dumping the entire file.

## Long-task checkpoint

Keep a compact state:

- Objective
- Constraints
- Confirmed architecture
- Touched files
- Verification status
- Next action

This checkpoint should replace repeated re-explanation.
