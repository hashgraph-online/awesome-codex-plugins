# Lossless Compaction Examples

Use these examples only when `SKILL.md` says compaction safety is unclear.

## Current Truth

Bad compaction:

```markdown
- upload has scan status rules.
```

Why bad: loses the canonical field, forbidden fallback, applicability, status, relation, and evidence.

Lossless current truth:

```markdown
- **ID**: `mem:upload:scan-status-field`
- **Subject**: `upload.scan.status-field`
- **Status**: `current`
- **Rule**: `scan_status` is the canonical scan field; do not fall back to `file_status`.
- **Applies When**: Rendering scan UI, callback results, or file detail processing state.
- **Evidence**: 2026-05-10 upload contract review.
- **Confidence**: `confirmed`
- **Relation**: `None`
- **Since**: 2026-05-10
- **History**: `history/events/2026/05/2026-05-10-upload-scan-status-contract.md`
```

## Superseded Rule

Before:

```markdown
- Upload UI may fall back from missing `scan_status` to `file_status`.
- Upload UI must render absence when `scan_status` is missing; `file_status` is not a scan proxy.
```

Lossless current truth repair:

```markdown
- **ID**: `mem:upload:scan-status-field`
- **Subject**: `upload.scan.status-field`
- **Status**: `current`
- **Rule**: Upload UI must render absence when `scan_status` is missing; `file_status` is not a scan proxy.
- **Relation**: `updates mem:upload:scan-status-file-status-fallback`

- **ID**: `mem:upload:scan-status-file-status-fallback`
- **Subject**: `upload.scan.status-field`
- **Status**: `superseded`
- **Rule**: Old fallback rule from 2026-05-04.
- **Relation**: `None`
```

## Context Body To Pointer

Before:

```markdown
### 2026-05-18 Upload status fix
- Investigated the ready badge bug. The frontend was checking `file_status` because it was present in old fixtures. The backend contract review confirmed `scan_status` is the scan-specific field. Updated `src/upload/ScanBadge.tsx` and tests.
- Follow-up: remove stale fixture comments later.
```

Preserve durable meaning first:

```markdown
domains/upload.md
= current truth body for `mem:upload:scan-status-field`

history/events/2026/05/2026-05-18-upload-status-fix.md
= event body explaining stale fixture usage and the ready badge correction
```

Then compact context:

```markdown
- Remove stale upload fixture comments; current truth: `mem:upload:scan-status-field`; event: `history/events/2026/05/2026-05-18-upload-status-fix.md`; next: update fixture comments.
```

If there is no active follow-up, remove the context entry after durable meaning is preserved.

## Project Decision

Bad compaction:

```markdown
- Use upload worker.
```

Lossless current truth:

```markdown
- **ID**: `mem:project:upload-worker-boundary`
- **Subject**: `upload.worker.boundary`
- **Status**: `current`
- **Rule**: Upload processing stays in the worker boundary to avoid UI-thread retries and preserve resumable-upload queue semantics.
- **Applies When**: Chunk retry, pause/resume, and queue persistence.
- **Evidence**: implementation contract
- **Confidence**: `implementation-backed`
- **Relation**: `None`
- **Since**: 2026-05-18
- **History**: `None`
```

## Rule

If the compacted result cannot answer "what owns the body, what exactly is true, why, when it applies, and where evidence lives?", it is too lossy.
