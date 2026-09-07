# Portable exports

Exports are explicit snapshots for onboarding, review, handoff, or audit. They do not replace the vault.

## Modes

- `onboarding`: project, current state, handoff, and accepted decisions.
- `decision-log`: accepted and superseded decision notes, clearly labelled by status.
- `audit`: a JSON manifest containing relative note paths, metadata, and SHA-256 hashes; no note bodies.
- `context`: project and current state plus only explicitly selected, inspected note paths.

Run the vault health checker first. Do not export when possible-secret findings remain. Choose an output location the user placed in scope. The export helper refuses to overwrite by default.

Markdown exports include provenance, creation time, source-relative paths, and a snapshot warning. Audit exports contain no absolute vault path. Treat every export as potentially shareable and apply the user's confidentiality rules.
