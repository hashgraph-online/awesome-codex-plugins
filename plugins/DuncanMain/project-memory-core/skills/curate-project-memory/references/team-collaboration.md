# Team collaboration

Keep shared durable notes merge-friendly and reviewable.

## Shared metadata

Use stable IDs that do not depend on filenames or machines:

```yaml
knowledge_id: adr-auth-001
owner: platform-team
reviewers:
  - security-team
review_status: approved
last_reviewed_by: security-team
last_reviewed_at: 2026-08-05
```

Allowed review states are `draft`, `requested`, `approved`, and `changes-requested`. A Git merge is not knowledge approval unless the project explicitly adopts that policy.

## Merge-safe practice

- Keep one decision per file and avoid large shared log files.
- Use descriptive filenames plus a stable `knowledge_id`.
- Use `Inbox/<contributor-id>.md` for concurrent candidate capture; contributor IDs should be non-sensitive aliases.
- Keep generated `Handoff.md` and `Coverage.md` reproducible; regenerate after resolving merges rather than hand-merging conflicting generated prose.
- Do not store personal email addresses unless the team explicitly requires them and policy permits it.
- Preserve rejected and superseded rationale when it remains useful, but exclude it from default retrieval.

Before promoting a team candidate, check ownership, requested reviewers, conflicts, branch scope, and evidence. Record approval metadata only from an explicit review action.
