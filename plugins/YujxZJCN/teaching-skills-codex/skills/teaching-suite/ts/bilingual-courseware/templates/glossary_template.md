# Course Terminology Glossary: {{course_code}} — {{course_title}}

**Language pair:** {{lang_A}} ⇄ {{lang_B}} {{e.g. EN ⇄ zh-CN}}
**Authority hierarchy:** {{per references/emi_conventions.md for EN⇄zh-CN, or the
professor-supplied conventions file for other pairs — proposals ranked, professor confirms}}
**Version:** {{n}} · **Last updated:** {{date}} · **Maintained by:** glossary_keeper_agent

> This glossary is the contract. Only `confirmed` entries bind translation; `proposed`
> entries are open questions and must not be used as settled terms.

## Entries

| # | Term ({{lang_A}}) | Term ({{lang_B}}) | Status | Authority basis | Register / usage notes | Do-not-translate | First-mention format |
|---|-------------------|-------------------|--------|-----------------|------------------------|------------------|----------------------|
| 1 | {{e.g. machine learning}} | {{e.g. 机器学习}} | {{confirmed | proposed}} | {{e.g. CNCTST list; assigned textbook ch.1}} | {{e.g. term, not everyday 学习; deprecated variant: 机器学习法}} | {{— | yes: reason}} | {{e.g. 机器学习 (machine learning) at first occurrence per artifact}} |
| 2 | {{e.g. pandas}} | {{e.g. pandas}} | confirmed | {{library name}} | {{code identifier — lowercase always}} | yes: code identifier | {{verbatim}} |
{{…one row per term; assessment-bearing terms get a ⚑ in usage notes}}

## Pending confirmation queue

| Term pair proposed | Found in | Authority basis | Proposed on | Blocking |
|--------------------|----------|-----------------|-------------|----------|
| {{pair}} | {{artifact + location}} | {{basis or "none found — professor's call"}} | {{date}} | {{which translation is paused on this entry}} |

## Conflicts log

{{a new proposal that contradicts an earlier confirmed entry — surfaced, never overwritten}}

| Date | Entry # | Confirmed rendering (date) | Conflicting proposal (source) | Professor resolution |
|------|---------|---------------------------|-------------------------------|----------------------|

## Change history

| Version | Date | Change (entries added / amended / deprecated) | Confirmed at checkpoint |
|---------|------|-----------------------------------------------|------------------------|
| {{n}} | {{date}} | {{summary}} | {{yes/date}} |

## Consumption note

The following bind to this glossary's `confirmed` entries — keep the table shape stable:

- `bilingual-courseware`: translator_agent (hard binding), terminology_auditor_agent
  (violation checks), parallel_sync_agent (delta translation)
- `media-scripter`: transcript_editor (caption and transcript terminology)
- `course-publisher`: announcement and FAQ drafting in the paired language
- {{other consumers the professor registers}}
