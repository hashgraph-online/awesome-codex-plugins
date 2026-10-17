---
name: bilingual-courseware
description: "Bilingual course-material maintenance for university professors — default EN ⇄ 简体中文, language-pair agnostic. 4-agent team covering the course terminology glossary (the contract every translation binds to), glossary-bound translation with pedagogical-equivalence checks, paired-version synchronization with drift detection, and read-only terminology consistency audits. Triggers on: translate course materials, bilingual course, English-medium instruction, EMI, terminology glossary, Chinese version, parallel syllabus, 双语教学, 双语课程, 全英文授课, 术语表, 专业术语, 翻译课件, 中英对照, 中文版."
metadata:
  version: "1.0.0"
  last_updated: "2026-06-10"
  status: active
  pipeline_stage: support
  related_skills:
    - course-designer
    - lesson-builder
    - course-publisher
    - media-scripter
---

# Bilingual Courseware — Terminology & Paired-Version Team

Maintains bilingual course materials with terminology discipline. Other skills produce
the artifacts; this skill keeps their two language versions saying the same thing — same
terms every time, same pedagogical demand on both sides, and a recorded pairing so that
neither version quietly outruns the other. Default pair is EN ⇄ 简体中文 (the conventions
file covers it deeply); any pair works with professor-supplied conventions.

> **Prime rule:** the glossary is the contract. Translation without a confirmed glossary
> produces drift — the same concept rendered three ways across a semester, and 90
> students learning the wrong standard term. Glossary-first is this skill's
> blueprint-first rule: no term-bearing material is translated until its terms are
> confirmed, and new terms encountered mid-translation pause for confirmation rather
> than being improvised inconsistently.

## Quick Start

```
Build a terminology glossary for my machine learning course
Translate my syllabus into Chinese — the English version is the original
把这门课的教学大纲翻译成英文，专业术语要统一
I updated the English syllabus to v2 — bring the Chinese version up to date
检查我所有课件里的术语是否一致
Check whether my slides and exam use the glossary terms consistently
```

## Modes

| Mode | Trigger intent | Output |
|------|---------------|--------|
| `glossary` | "Build/extend a glossary", new course going bilingual, new unit's terms, 术语表 | Course terminology glossary: candidate terms extracted from course materials, translations proposed with authority notes, professor confirms each entry; maintained artifact, versioned |
| `translate` | "Translate X", 翻译课件 / 中文版 — one artifact: outcomes, syllabus, slides source, handouts, exam instructions | Glossary-bound translation + pedagogical-equivalence pass + divergence log + pairing-registry entry |
| `parallel` | "Update the other version", "keep both in sync", 中英对照 maintenance | Paired-version create/update: change one side → propagate to the other; drift report when versions evolved independently |
| `check` | "Are my terms consistent?", pre-semester sweep, 检查术语 | Read-only terminology consistency audit across ALL course materials in one language or across the pair — every finding located, no rewrites |

**Mode dispatch rule:** a translation request for an artifact whose domain terms are not
yet covered by a confirmed glossary routes through `glossary` first — on the new terms
only, incrementally, never a restart. Detect intent in any language.

### Does NOT trigger

| Scenario | Use instead |
|----------|-------------|
| Writing the original materials (syllabus, lessons, exams, scripts) | The producing skill: `course-designer`, `lesson-builder`, `assessment-architect`, `media-scripter` |
| Translating student-facing communications (announcements, emails, FAQ) | `course-publisher`, binding to this skill's glossary |
| General translation unrelated to a course | Out of scope for this suite |

## Agent Team (4)

| Agent | Role |
|-------|------|
| `glossary_keeper_agent` | Extracts candidate terms, proposes pairs with authority notes, runs batched professor confirmation, maintains the versioned glossary other skills consume |
| `translator_agent` | Glossary-bound translation with pedagogical-equivalence checks: cultural accessibility, difficulty shift, register, length expansion; logs every deliberate divergence |
| `parallel_sync_agent` | Pairing registry, change propagation, three-way drift reports; professor chooses merge direction — never auto-merges |
| `terminology_auditor_agent` | Read-only consistency audit: glossary violations, intra-language inconsistency, untranslated strays, script/punctuation discipline — every finding located |

## Workflow (`translate` mode)

```
Phase 0  GLOSSARY GATE — check the confirmed glossary covers the artifact's domain
                         terms. Missing or stale coverage → `glossary` mode on the new
                         terms only (incremental — not a restart of the glossary)
Phase 1  DRAFT         — translator_agent produces the glossary-bound translation with
                         pedagogical-equivalence notes: examples that don't cross
                         cultures flagged with a proposed local equivalent; instructions
                         whose difficulty shifts in translation flagged
Phase 2  TERM AUDIT    — terminology_auditor_agent passes over the draft: every
                         confirmed term rendered exactly, near-misses are defects
         🧑 checkpoint: translation + divergence log — every deliberate non-literal
            choice listed with location and reason; the professor approves or redirects
Phase 3  REGISTER      — parallel_sync_agent records the pairing: which exact version
                         of the source this translation matches, in the sync register
                         and passport artifacts[]
```

`glossary` mode runs glossary_keeper end-to-end (extract → propose → 🧑 batched
confirmation → version). `parallel` mode diffs the changed side, translates the delta
through Phases 1–2, patches the pair, and updates the register; independently-evolved
sides produce a drift report instead of a patch. `check` mode runs
terminology_auditor_agent alone, read-only, findings located like `submission-auditor`.

## Iron rules

1. **Glossary-first.** No translation of term-bearing material without confirmed
   glossary coverage. A new term encountered mid-translation pauses for confirmation —
   it is never improvised inconsistently, because the improvisation becomes the term
   students learn.
2. **The professor confirms terminology.** Discipline terminology is the professor's
   domain. Candidate pairs ship with an authority basis — standard textbook usage,
   national standards-body patterns, common EMI practice — but their status is
   `[NEEDS PROFESSOR INPUT]` until confirmed. A wrong standard term taught to 90
   students is expensive; a confirmation batch costs minutes.
3. **Pedagogical equivalence over literalism.** Translated artifacts must make the same
   pedagogical demand, not the same words. Divergences are deliberate and logged —
   location, what changed, why — never accidental. Assessment translations are checked
   for difficulty shift: an exam that is harder in one language is an equity defect,
   not a style choice.
4. **Version pairing is recorded.** Every translated artifact records the exact source
   version it matches. Sync status is checkable at any time; drift is loud. The
   `parallel` mode exists because v2 of the English syllabus WILL forget the Chinese
   one — silence is the failure mode, the register is the cure.
5. **Language-pair agnostic, EN⇄zh-CN tuned.** `ts/bilingual-courseware/references/emi_conventions.md` covers
   the default pair deeply — register, punctuation, authority hierarchy, code-switching.
   Other pairs work with professor-supplied conventions, recorded per course; the skill
   never pretends its zh-CN depth transfers automatically.

## Outputs

- `bilingual/glossary.md` — the confirmed terminology glossary (from
  `ts/bilingual-courseware/templates/glossary_template.md`), versioned, consumed by other skills
- `bilingual/<artifact>_<lang>.md` — translated artifacts, each with its divergence log
- `bilingual/sync_register.md` — pairing registry (from
  `ts/bilingual-courseware/templates/sync_register_template.md`): what matches what, at which version
- `bilingual/drift_report.md` (`parallel` mode, when sides evolved independently)
- `bilingual/terminology_audit.md` (`check` mode) — located findings, ordered by
  student impact
- Passport: paired artifacts cross-referenced in `artifacts[]`

## References

- `ts/bilingual-courseware/references/emi_conventions.md` — EN⇄zh-CN register mapping, punctuation/typography,
  terminology authority hierarchy, assessment-translation equity, layout expansion,
  classroom code-switching conventions
- `ts/bilingual-courseware/templates/glossary_template.md`
- `ts/bilingual-courseware/templates/sync_register_template.md`
- Shared: `ts/shared/course_passport_schema.md` (note `course.language_of_instruction`),
  `ts/shared/checkpoint_protocol.md`, `ts/shared/quality_gate_protocol.md`
