# Mirror Policy

Use this when a repository has more than one agent instruction surface.

## Canonical File

- Choose one primary entrypoint, normally `AGENTS.md`.
- Treat name casing as part of the contract. Do not create parallel files whose names differ only by case.
- If a runtime expects another filename, make that file a symlink, generated mirror, or short pointer to the primary entrypoint.

## Drift Prevention

- Generated mirrors should include a marker that names the source file and generation command.
- Exact-copy mirrors need a check that compares content byte-for-byte.
- Symlink mirrors need a check that verifies the target path.
- Pointer mirrors should be short and should not duplicate rules.

## Validation

- List every agent-facing instruction file.
- Confirm each file is canonical, a symlink, a generated mirror, or a pointer.
- Run the mirror check if one exists; otherwise compare targets manually.

## Do Not Include

- Multiple independent sources of truth for the same rule.
- Case-only filename variants.
- Runtime-specific rules that should live in the primary entrypoint or a subtree entrypoint.
