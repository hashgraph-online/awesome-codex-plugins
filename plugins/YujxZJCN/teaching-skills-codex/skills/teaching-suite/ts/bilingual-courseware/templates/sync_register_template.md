# Paired-Version Sync Register: {{course_code}} — {{course_title}}

**Language pair:** {{lang_A}} ⇄ {{lang_B}}
**Authoritative side (default propagation direction):** {{professor decision — often the
`language_of_instruction` side; recorded here, confirmed per change when the edit
originates on the other side}}
**Glossary version bound:** {{glossary version this register's last syncs used}}
**Last updated:** {{date}} · **Maintained by:** parallel_sync_agent

## Paired artifacts

| Artifact A ({{lang_A}}) | Version A | Artifact B ({{lang_B}}) | Version B | Sync status | Last sync | Divergence log |
|--------------------------|-----------|--------------------------|-----------|-------------|-----------|----------------|
| {{path, e.g. syllabus.md}} | {{hash/date, e.g. v2 2026-06-08}} | {{path, e.g. bilingual/syllabus_zh.md}} | {{hash/date}} | {{in-sync | ahead: A | ahead: B | drifted | untracked}} | {{date}} | {{path#section}} |
{{…one row per pair; an artifact with a translation not listed here is untracked, not "probably fine"}}

## Drift report format

{{emitted as bilingual/drift_report.md when both sides changed independently; never auto-merged}}

```
### Drift: {{artifact A}} ⇄ {{artifact B}}
Common base: {{last-synced versions, date}}

| # | Location | Side A change | Side B change | Conflict? | Severity |
|---|----------|---------------|---------------|-----------|----------|
| 1 | {{§/heading}} | {{what A changed}} | {{what B changed | —}} | {{yes/no}} | {{assessment/policy text > prose}} |

Professor decides per change: keep A | keep B | merge both | neither.
```

## Merge-decision log

| Date | Pair | Drifted change (location) | Professor's direction | Applied |
|------|------|---------------------------|----------------------|---------|
| {{date}} | {{pair}} | {{§ + one-line summary}} | {{keep A / keep B / merge / neither + reason}} | {{date}} |

## Passport integration

Paired artifacts cross-reference each other in `course_passport.yaml` `artifacts[]`
(each entry notes its pair's path); this register is itself ledgered there
(`produced_by: bilingual-courseware`). Standalone (no passport): this file is
self-contained; passport integration offered at exit per Passport Iron Rule 5.
