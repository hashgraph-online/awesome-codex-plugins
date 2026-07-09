# Build When Missing

Use this when a repository has no usable agent entrypoint. Pattern sources include first-read guidance, mirror policies, and subtree overrides in larger repositories.

## Equivalent Artifacts

- Existing agent instruction files, contributor guides, or runtime-specific rule files may already satisfy the entrypoint role.
- Record the chosen artifact under `Detected Mapping` before creating a default file.
- Use `templates/AGENTS.md` only when no equivalent entrypoint exists.

## Minimum Files

- Root `AGENTS.md` or an explicitly mapped equivalent entrypoint.
- Optional mirrors: `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, or `.github/instructions/*`.
- Optional subtree `AGENTS.md` only where a directory has stricter local rules.

## Bootstrap Steps

1. Map any existing first-read guidance to the entrypoint role.
2. If no equivalent exists, create a root entrypoint from `templates/AGENTS.md`.
3. Declare instruction precedence: system/developer, user, nearest agent file, linked docs.
4. Add a mirror policy: symlink, exact copy with generation marker, or explicit "read the primary entrypoint first" pointer.
5. Add only high-signal navigation; link deeper docs instead of embedding long procedures.
6. Add a drift check if mirrors are generated or exact-copy files.

## Validation

- Confirm an agent can identify first-read docs, edit boundaries, and minimum validation in under one minute.
- Run the mirror/drift checker if present.
- If no checker exists, compare mirror contents or symlink targets manually.

## Do Not Include

- Product secrets, credentials, local machine paths, or private environment assumptions.
- Long project encyclopedia content that belongs in architecture or runbook docs.
- Business-specific requirements that should live in design docs or task boards.
