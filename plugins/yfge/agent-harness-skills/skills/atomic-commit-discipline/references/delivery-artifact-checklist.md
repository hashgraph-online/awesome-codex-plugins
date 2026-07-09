# Delivery Artifact Checklist

Use this when a commit is part of a release, deploy, package, or handoff flow.

## Minimum Evidence

- Artifact identity: version, tag, package name, bundle name, or run ID.
- Build command and result.
- Validation command and result.
- Target channel or audience, described generically.
- Rollback, restore, or follow-up note when the delivery can affect users.

## Commit Grouping

- Keep release metadata separate from unrelated implementation work unless the repository explicitly requires one commit.
- Keep generated artifacts out of source commits unless they are versioned outputs by policy.
- Link large artifacts by path or run ID instead of committing them by default.

## Validation

- Re-read staged files and confirm they match one delivery purpose.
- Confirm the artifact can be reproduced from committed sources and documented commands.
- Confirm ledger or handoff records reference the artifact identity and validation.

## Do Not Include

- Unrelated formatting or cleanup.
- Local-only build products.
- Delivery claims without artifact identity.
