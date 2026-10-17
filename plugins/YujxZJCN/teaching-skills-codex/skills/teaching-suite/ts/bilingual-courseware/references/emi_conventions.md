# EN ⇄ zh-CN Conventions for Course Materials

Working conventions for `translator_agent` and `terminology_auditor_agent` on the
suite's default language pair. Other pairs: the professor supplies the equivalent
conventions, recorded per course; this file's *structure* (register, typography,
authority, equity, layout, code-switching) is the checklist of what those conventions
must cover.

## Academic register mapping

Academic register is a function, not a literal style — translate the function.

| Function | EN academic habit | zh-CN academic habit |
|----------|------------------|---------------------|
| Hedging | "may suggest", "appears to", "is likely to" | 或许/可能/在一定程度上 — hedge once, not stacked; literal stacking of EN hedges reads as evasive in zh |
| Instructions to students | Imperative is normal and not rude: "Submit by Friday." | Bare imperative can read curt in student-facing prose; 请 + verb (请于周五前提交) is the neutral register. Exam-item stems stay imperative (计算/证明/简述) — that IS the convention |
| Passive voice | Common in methods/描述 ("the data were collected") | zh tolerates agentless actives and 被-free passives (数据采集自…); mechanical 被 insertion reads translated, not academic |
| First person | "we" conventional in technical exposition | 我们 acceptable; 本课程/本文 common where EN says "this course/paper" |
| Politeness in policy text | Plain statement of rules | Plain statement also correct — do not soften policy into suggestion; a softened late policy is a difficulty/clarity shift |

## Punctuation and typography

Mechanical rules — `terminology_auditor_agent` checks these as facts:

- **Full-width punctuation in zh text:** ，。：；？！（）《》 — half-width `,.;:?!()` inside
  zh sentences is a defect. Exception: punctuation inside embedded EN fragments, code,
  and math stays half-width.
- **Spacing between zh and Latin/digits:** one half-width space between a zh character
  and an adjacent Latin word, identifier, or number (共 90 名学生使用 Python 完成).
  No space before/after full-width punctuation.
- **Quotation marks:** zh text uses “ ” (and ‘ ’ for nesting) or 《 》 for
  titles of works/courses/laws; never straight `"` inside zh prose.
- **Units and numbers:** Arabic numerals with SI units in technical text (10 MB,
  3 学分 both fine); be consistent within an artifact about 百分号 style (15% not
  百分之十五 in tables/items). Dates in student-facing zh text: 2026年6月10日 form,
  not 06/10 (ambiguous across the pair — a real exam-logistics hazard).
- **Ellipsis and dashes:** zh uses …… (double) and ——; EN uses … and —.

## Terminology authority hierarchy (zh-CN)

For `glossary_keeper_agent` authority notes — strongest first:

1. **National term-standardization patterns** — 全国科学技术名词审定委员会 (CNCTST)
   published term lists are the standard reference for discipline terminology in
   zh-CN; where a term has an approved rendering, propose it and say so.
2. **Standard textbook usage** — the dominant zh textbook(s) in the discipline,
   especially the one the course actually assigns; a CNCTST term that no textbook
   uses is a flag worth surfacing, not silently picking either way.
3. **Established field practice** — what published zh literature and practitioners
   actually write, including stable loanwords kept in EN.

**Caveat, always:** the hierarchy ranks *proposals*. The professor confirms every
entry — they know which rendering their department, their textbook, and their exam
tradition actually use, and that knowledge outranks any list (Iron Rule 2).

## Assessment-translation equity

An assessment item that shifts difficulty in translation is an equity defect.
Known shift patterns to check item-by-item:

- **Vocabulary load** — the zh rendering of an EN stem may use rarer characters than
  the EN used rare words, or vice versa; the glossary term may be one word in one
  language and a noun phrase in the other (working memory cost under time pressure).
- **Syntactic complexity** — EN nested relative clauses flatten naturally in zh;
  zh topic-comment chains can turn into garden-path EN. An item whose stem doubled
  its clause depth in translation got harder.
- **Culturally-loaded contexts** — word problems and cases set in one culture's
  institutions (baseball statistics, 高考 logistics) carry hidden reading cost for
  the other side; flag with a proposed equivalent context, professor picks.
- **Distractor damage** (selected-response items) — a distractor that works because
  of an EN near-synonym trap may become obviously wrong in zh, or accidentally
  correct. Distractors are checked individually, not as prose.

Mitigations to propose at the checkpoint: parallel piloting (a TA or colleague takes
both versions, times and miss-patterns compared), providing students the glossary
itself for term-heavy exams (removes vocabulary as a confound where vocabulary is not
the construct), and writing items glossary-first so both versions grow from the same
blueprint.

## Layout expansion factors

Where space is real — slides, captions, table cells, fixed-format handouts:

- **EN → zh:** character count drops sharply (~50–70% of EN character count), but
  *rendered width* is roughly 0.7–0.9× — CJK glyphs are full-width. Line counts
  usually survive; dense EN slide bullets often fit.
- **zh → EN:** expect ~1.2–1.6× rendered width. zh-designed slides and caption
  timings frequently overflow in EN — flag, propose the compression, never truncate
  silently.
- **Captions** (with `media-scripter`): zh reads faster per displayed line but
  per-cue character limits differ (commonly ~16–20 full-width characters/line vs
  ~42 Latin characters); re-time, don't just re-fill cues.

These are planning factors, not laws — `[VERIFY]` against the actual rendered artifact.

## EMI classroom patterns — when to keep EN terms in zh discourse

Code-switching for technical terms is established EMI practice, not sloppiness —
when it is *conventional*, which the glossary records per term:

- **First-mention bilingual format:** 机器学习 (machine learning) — zh term first,
  EN in parentheses at first occurrence per artifact; subsequent mentions use the
  glossary's chosen primary rendering.
- **Keep EN verbatim:** code identifiers, API/library names, file formats, standard
  abbreviations students must recognize in EN literature (SQL, p-value, BERT) — these
  carry do-not-translate flags in the glossary.
- **Exam consistency rule:** whatever convention lecture discourse uses, the exam
  uses the *glossary* rendering — students must not meet a term for the first time in
  a new language inside a timed assessment. If lectures code-switch and the exam is
  monolingual, providing the glossary to students is the standard mitigation.

## What this file does NOT decide

- **Institutional language policy** — whether the course is EMI by mandate, which
  artifacts must exist in which languages, degree-program language requirements:
  professor/institution decisions, recorded in the passport
  (`course.language_of_instruction`, `institution_constraints`).
- **Which side is authoritative** for each artifact pair — a professor decision,
  recorded per course in the sync register header, applied by `parallel_sync_agent`.
- **Discipline terminology itself** — this file ranks authorities; it confirms
  nothing. Confirmation is the professor's, entry by entry.
