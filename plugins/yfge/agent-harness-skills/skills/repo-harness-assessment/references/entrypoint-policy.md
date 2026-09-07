# Entrypoint Policy

Use this when a repository has multiple agent instruction surfaces or needs a first agent entrypoint.

## Canonical Surface

- Choose one primary entrypoint, normally `AGENTS.md` or an explicitly mapped equivalent.
- Keep it to scope, source-of-truth links, hard boundaries, minimum validation, and relevant skill routing.
- Put stricter local rules in subtree entrypoints instead of expanding the root file.
- Treat filename casing as part of the contract; do not create case-only variants.

## Mirrors And Pointers

- Prefer a short pointer when another runtime can follow the canonical file.
- Use symlinks only where the target runtime and platform support them reliably.
- Generated mirrors must name their source and generation command.
- Exact-copy mirrors need a byte-for-byte drift check.

## Validation

- List every agent-facing instruction file and classify it as canonical, subtree override, symlink, generated mirror, or pointer.
- Confirm an agent can find first-read docs, edit boundaries, and minimum validation in under one minute.
- Run the mirror or generation check when one exists; otherwise compare targets manually.

## Do Not Include

- Independent copies of the same rules.
- Product secrets, credentials, private hosts, or local machine assumptions.
- Long architecture, release, or operational procedures that belong in linked source-of-truth documents.
