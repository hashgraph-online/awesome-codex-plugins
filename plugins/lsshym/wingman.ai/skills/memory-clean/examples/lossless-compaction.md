# Lossless Compaction Examples

Use these examples only when `SKILL.md` says compaction candidates include current rules, ADRs, domain truths, or evidence-bearing logs.

## Current Rule

Bad compaction:

```markdown
- upload has scan status rules.
```

Why bad: loses the canonical field, forbidden fallback, evidence, and applicability.

Lossless compaction:

```markdown
- `upload`: `scan_status` is the canonical scan field; do not fall back to `file_status`.
  Evidence: 2026-05-10 upload contract review. Applies when rendering scan UI, callback results, or file detail processing state.
```

## Superseded Rule

Before:

```markdown
- Upload UI may fall back from missing `scan_status` to `file_status`.
- Upload UI must render absence when `scan_status` is missing; `file_status` is not a scan proxy.
```

Lossless compaction:

```markdown
- Upload UI must render absence when `scan_status` is missing; `file_status` is not a scan proxy.
  Status: current. Supersedes: old fallback rule from 2026-05-04.
- Old fallback rule: superseded by the current `scan_status` canonical-field rule.
```

## Evidence-Bearing Context Log

Before:

```markdown
### 2026-05-18 Upload status fix
- Investigated the ready badge bug. The frontend was checking `file_status` because it was present in old fixtures. The backend contract review confirmed `scan_status` is the scan-specific field. Updated `src/upload/ScanBadge.tsx` and tests.
- Follow-up: remove stale fixture comments later.
```

Lossless compaction:

```markdown
### 2026-05-18 Upload status fix
- Confirmed `scan_status` is the scan-specific field; `file_status` fixture usage was stale. Updated `src/upload/ScanBadge.tsx` and tests.
- Follow-up: remove stale fixture comments.
```

## ADR

Bad compaction:

```markdown
- Use upload worker.
```

Lossless compaction:

```markdown
- ADR: upload processing stays in the worker boundary to avoid UI-thread retries and preserve resumable-upload queue semantics.
  Status: accepted. Applies to chunk retry, pause/resume, and queue persistence.
```

## Rule

If the compacted text cannot answer "what exactly must future agents do, why, when, and where is the evidence?", it is too lossy.
