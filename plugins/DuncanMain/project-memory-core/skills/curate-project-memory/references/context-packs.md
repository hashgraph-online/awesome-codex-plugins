# Context packs

A context pack is a small, task-specific selection of durable notes. It prevents full-vault loading and makes retrieval understandable.

## Candidate ranking

Run `scripts/build_context_pack.py` to rank candidates transparently. Its lexical ranking is intentionally local and rebuildable. It rewards:

- foundational project and current-state notes;
- exact repository-relative code-path matches;
- query matches in titles, properties, and text;
- conservative fuzzy similarity between the task and note title;
- matching workstreams and tags;
- active and accepted status;
- recent updates.

It penalizes rejected, deprecated, and superseded notes. Ranking is a retrieval aid, not authority; inspect selected notes before relying on them.

## Selection order

1. Load `Project Home.md`, `Project.md`, and `Current State.md` for the stable project ID.
2. Extract task terms, named components, workstreams, and repository-relative file paths.
3. Follow direct links and backlinks that match those signals.
4. Prefer accepted, active, confirmed, and recently reviewed notes.
5. Include proposed or conflicting notes only when the task concerns the unresolved issue.
6. Exclude rejected, deprecated, and superseded notes unless explaining history.

Stop when the selected notes are sufficient to act safely. Do not browse unrelated vault areas.

Use five additional notes as a normal ceiling. Exceed it only when the task genuinely crosses several components or a safety-critical decision requires broader history.

## Retrieval explanation

For each non-foundational note, give a short reason such as:

```text
Loaded [[ADR-012 Token expiry]] because it references src/tokens/issuer.ts.
```

Mention important unavailable or stale context. Do not expose hidden reasoning or produce a long retrieval report.
