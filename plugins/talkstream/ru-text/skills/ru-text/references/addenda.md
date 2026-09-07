# Addenda — rules added from usage experience

The rules below were added later, from real editorial practice, and were not part of the
plugin's initial rule set. Like the rest of the plugin, they are independently formulated; the
16 sources in `sources.md` informed the work, but no rule is taken or copied from them. They are
supported by academic references. Kept separate for traceability: initial rule set vs. experiential
additions.

## Table of Contents

- [Neuroslop index](#neuroslop-index)
- [Two rules that govern all the others](#two-rules-that-govern-all-the-others)
- [AD-1. Excessive em dashes](#ad-1-excessive-em-dashes-избыточные-тире)
- [AD-2. Excessive parcellation](#ad-2-excessive-parcellation-избыточная-парцелляция)
- [AD-3. Patronizing explanation](#ad-3-patronizing-explanation-разжёвывание-очевидного)
- [AD-4. Unprovoked rebuttal](#ad-4-unprovoked-rebuttal-возражение-без-предпосылок)
- [AD-5. Subject-predicate semantic mismatch](#ad-5-subject-predicate-semantic-mismatch-семантическое-несоответствие-субъекта-и-предиката)
- [AD-6. Manufactured antithesis](#ad-6-manufactured-antithesis-ложная-антитеза)
- [AD-7. Preemptive virtue qualifier](#ad-7-preemptive-virtue-qualifier-непрошенная-оговорка-без-воды)
- [AD-8. Assistant-register meta-commentary](#ad-8-assistant-register-meta-commentary-сервисные-реплики-ассистента)
- [AD-9. Hollow opener](#ad-9-hollow-opener-пустой-зачин)
- [AD-10. Declared sincerity](#ad-10-declared-sincerity-объявленная-искренность)
- [AD-11. Mandatory tricolon](#ad-11-mandatory-tricolon-обязательная-триада)
- [AD-12. Hollowed mechanism](#ad-12-hollowed-mechanism-выхолощенность)
- [AD-13. Phantom attribution](#ad-13-phantom-attribution-неопределённая-атрибуция)
- [AD-14. Chat transcript as the artifact](#ad-14-chat-transcript-as-the-artifact-диалог-с-нейросетью-вместо-текста)
- [AD-15. Search-engine addressee](#ad-15-search-engine-addressee-адресат--поисковик-а-не-читатель)
- [AD-16. Additive pseudo-pair](#ad-16-additive-pseudo-pair-не-только-x-но-и-y)
- [AD-17. Comma welded to a dash](#ad-17-comma-welded-to-a-dash-запятая-сомкнутая-с-тире)
- [AD-18. Uppercase band vs. deliberate emphasis](#ad-18-uppercase-band-vs-deliberate-emphasis-капслок-полоса-против-выделения)

## Neuroslop index

A compact catalogue of the recurring tells of AI-generated Russian prose, each routed to the rule
that is its canonical home. These tells skew by training era and instruction-tuning style rather
than by any single vendor; a breakdown by specific model family is intentionally omitted as
unverifiable and fast-dating.

| Tell | Canonical home |
|---|---|
| Manufactured antithesis — «не X, а Y» / «не просто X, а Y» with no antecedent | AD-6 |
| Declared sincerity — «честный разбор», «давайте будем честны», «рассказываю как есть» | AD-10 |
| Mandatory tricolon — «инновационный, трансформирующий, прорывной» | AD-11 |
| Hollowed mechanism — «зависит от различных факторов», «свои особенности» | AD-12 |
| Phantom attribution — «исследования показывают», «эксперты отмечают» | AD-13 |
| Chat transcript as the artifact — «Я: … / Модель: …» as the document's skeleton | AD-14 |
| Search-engine addressee — the query phrase repeated where a pronoun would serve | AD-15 |
| Additive pseudo-pair — «не только X, но и Y» where Y adds nothing | AD-16 |
| Preemptive virtue qualifier — «без воды», «чётко, по делу», «коротко и ясно» | AD-7 |
| Assistant-register meta-commentary — «Отличный вопрос!», «Надеюсь, это помогло» | AD-8 |
| Hollow opener — «давайте разберёмся», «погрузимся», «важно понимать, что» | AD-9 |
| Excessive em dashes — staccato dash rhythm | AD-1 |
| Comma welded to a dash — «…, — …» inside one sentence | AD-17 |
| Throat-clearing stop-words — «стоит отметить, что», «нельзя не отметить» | `info-style.md` §B |
| Empty universal preamble — «в современном мире», «не секрет, что» | `info-style.md` §B |
| Unproven-claim adjectives — «качественный», «надёжный», «эффективный» | `info-style.md` §B |
| Generic conclusion — «таким образом, подводя итог» | `anti-patterns.md` |
| Artificial liveliness — exclamation stacks and emoji as a substitute for detail | `info-style.md` §F |

## Two rules that govern all the others

**Density raises severity; it never replaces the findings.** Several rules here treat a
cluster as their main signal — AD-1, AD-2, AD-6, AD-9, AD-11, AD-16. Once a rule has
decided that it fires, report every instance, individually, with its own quoted fragment,
and let the count govern how far the score moves. One line saying «два и более на текст» in
place of the four fragments is a loss of coverage wearing the clothes of a summary: the
person fixing the text is left without the list of lines to fix.

This says nothing about **whether** a rule fires. Two of the six — AD-11 and AD-16 — put
density into the flag condition itself, so an isolated triple or an isolated pair is not a
finding at all; that is their own text and it stands. The rule here governs what happens
after a rule has decided to fire, never before.

Nor is the score card a limit on what the check reports: `scoring.md` asks for one to
three issues per dimension in the scored output; that is the size of a table cell, not the
size of the check. `/ru-text:ru-check` lists what it found; `/ru-text:ru-score` quotes the
most telling of them per dimension. Neither number licenses dropping a finding.

**A document-level charge adds; it never replaces.** AD-14 and AD-15 are charged to the
piece as a whole. Each absorbs only its own evidence — the repetitions that demonstrate it
— and absorbs nothing else. Every ordinary finding in that text stands: stop-words,
unproven claims, passive voice, punctuation, typography. Both statements exist because a
measured run did the opposite: it replaced ten ordinary findings with three document-level
ones, and the text came out looking better for it.

---

## AD-1. Excessive em dashes (избыточные тире)

**Problem:** multiple em dashes in a paragraph create choppy rhythm, monotony, and an affected (mannered) tone.

**Sources:**
- Chekhov cautioned against overusing italics and dashes, treating the habit as mannered (letters/notebooks)
- Rozental "Практическая стилистика": dashes should serve clear semantic function, not be default punctuation
- Gramota.ru: some writers abuse dashes; the 1956 Rules of Russian Orthography note both extremes
- Gorky, Dostoevsky used excessive dashes as INTENTIONAL literary device — not a model for non-literary prose
- Milchin/Cheltsova: restraint in editorial formatting

**Rules:**

AD-1.1. Limit to 1–2 em dashes per paragraph in non-literary prose. Three or more is a signal to restructure.

AD-1.2. Never use em dashes as default punctuation when a more precise mark exists:
- Explanation/enumeration → colon `:`
- Stronger pause between independent clauses → semicolon `;`
- Aside/clarification → parentheses `()`
- Complex sentence → restructure into two sentences

AD-1.3. Consecutive sentences with em dashes = monotonous pattern. Vary punctuation across sentences.

AD-1.4. "Dash between subject and predicate" (тире между подлежащим и сказуемым) is often skippable in conversational register — Rozental notes it's usually NOT placed in simple conversational-style sentences.

AD-1.5. Test for "mannered" tone (манерность): read aloud. If dashes create a staccato rhythm that feels artificial, replace some with other constructions.

AD-1.6 (what the budget counts — a parallel row is one dash). AD-1.1 is a budget on choices, and a
series is one choice made once. Two or more em dashes are ONE ROW when all three hold:

- they sit inside one paragraph or one list block — a row never spans paragraphs;
- every dash carries the same syntactic role;
- the text itself anchors them as a series. The anchor is one of: a count announced before them
  («решение состоит из трёх частей»); ordinals, dates or numbers standing in the same position in
  every member; list markup; the same word or phrase repeated after every dash.

A row counts as ONE dash toward AD-1.1. **The list of anchors is closed**, and it governs the count
in AD-1.1 and nothing else: AD-1.2 reaches a row whatever the count says, charged once, to the row
(AD-1.7). An anchor a reader has to argue for is not an anchor — the test is a string another person
can point at, not the author's statement that a series was intended. Looking enumerable is not an
anchor either: «Отчёт — на почте. Правки — в комментариях. Сборка — завтра утром» has no announced
count, no ordinal, no list markup and no phrase repeated after the dashes, so it is three sentences
sharing a shape and not a row. That shape is AD-1.3's own territory, and AD-1.3 fires on it. Nor
does repetition across a junction anchor anything: a word that closes one member and opens the next
stands in two different positions rather than the same one.

Two constructions stay outside this clause. A paired aside («Скилл — набор правил — помогает») is one
construction spending two marks, not a series, and counts as the two it is written with. And the
budget governs running prose: a table is not a paragraph and is not counted, because AD-1's signal is
the rhythm of running prose and cells have no rhythm across them.

AD-1.7 (a row is edited whole or left whole). Where a row is charged — because it carries the
paragraph over the limit, or because AD-1.2 finds a more precise mark for it — the charge is made to
the row, and the replacement applies to every member or to none. Varying the mark among members costs
more than the density it cures: «Первая — очередь запросов… Вторая: переработка шага… Третья:
повторный прогон…» takes away the parallel the reader was using to hold the list. Inside one row
AD-1.3 does not apply — there the repetition IS the structure. Between rows, and between independent
sentences, AD-1.3 stands unchanged.

AD-1.8 (trim to the limit, never to zero). AD-1.1 sets a budget of one to two, not of none. A
paragraph over the limit comes down to one or two dashes and stops there; a paragraph left with none,
where the dashes were carrying structure, is a new defect and not a fix. Measured over ten texts on
01.08.2026: the dash count fell in seven of them, and one paragraph of three anaphoric «— потому что»
went to zero — past this rule's own budget. AD-1 was the mechanic that did it, which is why the floor
is written here instead of being left to judgement.

AD-1.9 (marks the norm prescribes are not counted). The budget is on dashes the author chose. The
dialogue dash, and the dashes that set off the author's words in direct speech — the one before them
and the one resuming the speech after them, as in R19's «— Добрый день! — сказал он» and the
broken-quote schema «П, — а, — п» — are prescribed and have no alternative mark: they do not count
toward AD-1.1 at all. This is the reasoning AD-17.1 already applies to the same construction.
Charging them would fine a text for obeying this corpus.

Order of application, because four clauses now touch one number: exclude the prescribed marks
(AD-1.9), then collapse rows (AD-1.6), then count what is left against AD-1.1.

**Acknowledged:** the blind reading of 01.08.2026, where readers were given ten pairs without being
told which side had been edited and preferred the unedited side.

**Replacement strategies:**

| Pattern with dash | Alternative | When to use alternative |
|---|---|---|
| Москва — столица России | Москва, столица России, … | Appositive, not emphasis |
| Это — важно | Это важно | No emphasis needed, conversational |
| Он пришёл — и замолчал | Он пришёл и замолчал | No dramatic pause needed |
| Результат — рост продаж | Результат: рост продаж | Explanation follows |
| Всё готово — можно начинать | Всё готово; можно начинать | Two independent clauses |
| Скилл — набор правил — помогает | Скилл (набор правил) помогает | Aside, not emphasis |


**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Причины две. Первая — цена. Вторая — сроки. | Announced count and ordinals: one row, one dash toward the budget (AD-1.6). |
| «4 августа — стенд», «11 августа — приёмка», «20 августа — отчёт» одним списком | Dates in the same position inside one list block: one row (AD-1.6). |
| — Смету пересчитали к утру, — доложил прораб. | Direct speech: the marks are prescribed, not chosen (AD-1.9). |
---

## AD-2. Excessive parcellation (избыточная парцелляция)

**Problem:** splitting a single clause into several independent fragments for dramatic effect produces a choppy, affected rhythm typical of online copywriting. Parcellation is a legitimate stylistic device (Розенталь, «Справочник», ГЛАВА L) — the issue is overuse in registers where it does not fit.

**Sources:**
- Розенталь Д. Э. «Справочник по правописанию и стилистике», ГЛАВА L — parcellation as a stylistic figure of expressive syntax
- `info-style.md` section D: sentences should be compact but carry full meaning; parcellation is «неуместна» in info-style
- See also AD-1: analogous staccato-rhythm diagnosis for em dashes

**Rules:**

AD-2.1. In informational, UX, and business-writing registers: merge parcellated fragments back into a single clause with appropriate conjunctions or punctuation.

AD-2.2. In publicism: 1–2 parcellated constructions per article are acceptable as a rhythmic device; more signals overuse.

AD-2.3. In literary/artistic prose: parcellation is a legitimate author's device and is not penalized.

AD-2.4. Diagnostic test: read aloud. If several consecutive sentences are subject-less fragments or single-phrase rebuttals, the rhythm is staccato and likely excessive.

**Examples (info-style / UX / business context):**

| Wrong | Correct |
|---|---|
| Не шум и не артефакт. Воспроизводимый механизм. | И это не шум или артефакт, а воспроизводимый механизм. |
| Не потому что злой умысел. А потому что невозможно. | …не из-за злого умысла, а потому что это невозможно. |
| Расскажу последовательно, доступно, без воды. | Постараюсь объяснить доступным языком. |
| Это было не случайно. Это было продумано. Каждое слово. | Это было не случайно — каждое слово продумано. |

**Severity:** Low. Secondary signal in the **С — Structure** dimension (supporting **Ч — Clarity**). Cannot trigger non-compensatory caps alone.

**Acknowledged:** proposed by @V8-Software in issue #9 (2026-04-16).

---

## AD-3. Patronizing explanation (разжёвывание очевидного)

**Problem:** explaining what the context has already conveyed treats the reader as unable to make simple inferences. Over-explanation lowers pace, lowers trust, and adds words without information.

> **Not to be confused with** *примитивизация* as used in `info-style.md` section A, point 2: «Сокращение — забота о читателе, **не примитивизация**.» There «примитивизация» means oversimplification at the cost of meaning (e.g., removing necessary qualifiers). This rule concerns the opposite failure: redundant explanation of what the sentence has already conveyed. Both rules defend reader intelligence — from different directions.

**Sources:**
- Editorial practice around «respect the reader's intelligence»: cf. N. Gal, Ilyakhov
- Over-explaining in writing: liminalpages.com, writing.codidact.com/posts/75048
- `info-style.md` section A, point 2 — companion principle (against the opposite failure)

**Rules:**

AD-3.1. If a sentence already conveys a fact, do not immediately re-state it in a simpler metaphor or reformulation.

AD-3.2. Numeric comparisons that are self-evident to the reader do not need verbal paraphrase.

AD-3.3. Qualifiers like «то есть», «другими словами», «проще говоря» are warning signs — verify that the following clause actually adds information, not just rewords the preceding one.

**Examples:**

| Wrong | Correct |
|---|---|
| Конверсия выросла с 2% до 8%, то есть стала в четыре раза больше. | Конверсия выросла с 2% до 8%. |
| Мы сократили расходы на 30% — это почти треть бюджета. | Мы сократили расходы на 30%. |
| Пользователи тратят 12 минут, другими словами, больше десяти. | Пользователи тратят 12 минут. |

**Severity:** Low. Secondary signal in the **Ч — Clarity** dimension. Cannot trigger non-compensatory caps alone.

**Acknowledged:** proposed by @V8-Software in issue #9 (2026-04-16) as «Примитивизация»; renamed to avoid terminological collision with `info-style.md` A.2.

---

## AD-4. Unprovoked rebuttal (возражение без предпосылок)

**Problem:** constructions like «а это уже…», «но на самом деле…», «однако в реальности…» presuppose a prior claim that the writer is now refuting. When no such claim exists in the preceding text, the rebuttal invents an imaginary opponent and creates a non-existent conflict (cf. straw man / non-sequitur).

**Sources:**
- Straw-man fallacy and non-sequitur: Grammarly; Scribbr; Excelsior Online Writing Lab
- The rhetorical idea that a speaker argues against an opponent who may be real or imagined: HSE «Риторика» (nnov.hse.ru)

**Trigger constructions:**

- «а это уже [нечто важное/серьёзное]»
- «но на самом деле…», «на самом-то деле…»
- «однако в реальности…», «однако на практике…»
- «но при этом нужно понимать, что…»
- «только вот…»

**Rules:**

AD-4.1. Before any adversative construction, verify that the preceding text (within the same section or 1–2 paragraphs back) contains a claim that is actually being rebutted.

AD-4.2. If no antecedent exists, rewrite as a direct positive statement — remove the pseudo-rebuttal scaffolding.

AD-4.3. Legitimate use: rebutting a cited source, an earlier paragraph of the same text, or a reader expectation that the context makes explicit.

**Examples:**

| Wrong | Correct |
|---|---|
| …а это уже реальный сценарий, в котором модели постоянно обучают друг друга. | …данных, которыми модели постоянно обучают друг друга. |
| Но на самом деле алгоритм обрабатывает 10 000 запросов в секунду. | Алгоритм обрабатывает 10 000 запросов в секунду. |
| Однако в реальности пользователь открывает приложение раз в день. | Пользователь открывает приложение раз в день. |

**Severity:** Low. Secondary signal in the **С — Structure** dimension (supporting **Ч — Clarity**). Cannot trigger non-compensatory caps alone.

**Acknowledged:** proposed by @V8-Software in issue #9 (2026-04-16).

---

## AD-5. Subject-predicate semantic mismatch (семантическое несоответствие субъекта и предиката)

**Problem:** using a predicate whose semantics imply volition, consciousness, resistance, or goal-directed intent, applied to a subject that has none of these. A narrow subset of the broader phenomenon of lexical-semantic compatibility (лексическая сочетаемость / семантическая валентность — Текстология.ру; studme.org).

**Scope restriction (important):** this rule targets only cases where the mismatch creates a **false implication of will, consciousness, resistance, or intent**. It does **not** condemn technical or mathematical personification that has become normative terminology.

**Sources:**
- Лексическая сочетаемость и семантическая валентность: Текстология.ру; studme.org/43201; sci.house/russkiy-yazyik
- Antropomorphism as a recognized cognitive/linguistic phenomenon: Большая Российская Энциклопедия, article «Антропоморфизм»

**Rules:**

AD-5.1. Do not use verbs implying conscious will, resistance, or goal-seeking for subjects that lack them (abstract entities, software without an agent, inanimate processes in non-technical prose).

AD-5.2. **Exception — normative technical terminology.** In mathematical, algorithmic, ML, and general technical writing, the following are legitimate and do not trigger this rule:

  - сходимость алгоритма, последовательность сходится
  - алгоритм стремится к оптимуму / к пределу (mathematical «limit» sense)
  - модель обучается, сеть обучается
  - программа / система принимает решение
  - память компьютера, ответ системы, запрос пользователя

  Rule of thumb: if a domain textbook uses the construction, it is terminology, not anthropomorphism.

AD-5.3. Apply the diagnostic: would a reader infer conscious will or resistance from the predicate? If yes and the subject lacks these properties, rewrite. If the predicate is a technical term or a well-established metaphor (already catalogued in domain usage), leave it.

**Examples:**

| Wrong | Correct | Why |
|---|---|---|
| Модель заставили генерировать числа. | Модели дали задачу генерировать числа. | «заставить» presupposes will to resist |
| Программа не хочет сохранять файл. | Программа не может сохранить файл / отказывается сохранять файл. | «хотеть» implies conscious desire |
| Модель осознала ошибку и исправилась. | Модель выдала ошибку и на следующей итерации — корректный результат. | «осознание» implies reflective consciousness |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Алгоритм стремится к оптимуму. | Standard optimization terminology (mathematical limit sense). |
| Градиентный спуск сходится к локальному минимуму. | Standard calculus/optimization term. |
| Машина решает задачу за 3 секунды. | Established technical usage — in technical writing such anthropomorphic terms rest on an objective similarity rather than literal animacy (cf. БРЭ, «Антропоморфизм»). |
| Сеть обучается на 10 000 примеров. | Standard ML terminology. |

**Severity:** Low. Secondary signal in the **Ч — Clarity** dimension (supporting **Г — Grammar**), with explicit technical-context exception. Cannot trigger non-compensatory caps alone.

**Acknowledged:** proposed by @V8-Software in issue #9 (2026-04-16) with the example «Алгоритм стремится → Алгоритм становится». That example is preserved here as a *counter-example* illustrating the exception boundary, per deep-research review of mathematical and ML usage norms.


---

## AD-6. Manufactured antithesis (ложная антитеза)

**Problem:** a symmetric contrastive-negation pair — «не X, а Y», «это не X, это Y», «X — это не Y. Это Z», «не про X, а про Y», «не потому что X, а потому что Y», «не там, где X, а там, где Y» — where the negated pole X was never voiced in the preceding text and is not a reader expectation the context made explicit. The pair invents a rejected pole only to throw the «true» pole Y into relief, manufacturing rhetorical tension and arguing against an opponent who never spoke. It is one of the strongest machine-generation tells in Russian prose: in measured corpora it appears far more densely in generated text than in live human writing, where the natural device is the opposite: asymmetric self-correction («вернее…», «то есть…», «не то чтобы X, но Y») that refines what was just said. AD-6 targets the manufactured symmetric replacement; the asymmetric refinement is always allowed.

**Sources:**
- Antithesis as a rhetorical figure and the cost of its hollow imitation: editorial practice, informed by Розенталь «Практическая стилистика» on противопоставление
- Distinct from AD-4: AD-4 is a one-sided rebuttal of an unvoiced claim; AD-6 is a two-pole symmetric fork
- Independently formulated from corpus analysis of AI-generated Russian prose

**Trigger constructions:**

- «не X, а Y» / «X, а не Y» — X has no antecedent within the preceding 1–2 paragraphs
- «это не …, это …» / «X — это не Y. Это Z» — two equiweight definitions of one subject, often split by a period
- «не про X, а про Y» / «дело не в X, а в Y» / «вопрос не в X, а в Y» / «суть не в X, а в Y» — the topic swapped through a phantom rejected topic
- «не просто X, а Y» — the hype escalation; flag on the AD-6.1 test, especially when Y is itself inflated («целый», «настоящий», «полноценный»). Hype in Y is a signal, not a standalone trigger
- «не потому что X, а потому что Y» — a cause X that no one supposed
- «не там, где X, а там, где Y» — a locative pseudo-antithesis with no premise
- «не паранойя и не „всё видят“» — a pre-emptive string negating labels nobody put forward
- a cluster of two or more such pairs within ~150 words — density is the strongest signal

**Rules:**

AD-6.1. Flag only when all three conditions hold (any one failing → leave): (1) **no antecedent** — X was not voiced in the preceding 1–2 paragraphs and is not an explicit reader expectation; (2) **symmetry** — X and Y form an equiweight binary of comparable rank and parallel grammar, not a narrowing; (3) **zero increment** — drop the «не X» clause and no fact is lost, Y stands whole.

AD-6.2. Rewrite a flagged pair as a direct positive statement: keep Y, drop the phantom X. «X — это не Y, а Z» → «X — это Z». Do not trade one machine construction for another — removing «не X, а Y» must not introduce «но на самом деле Y» (that is AD-4). Carry the assertion with a fact, a number, an image, or rhythm.

AD-6.3. If the contrast is genuinely needed, earn it: let X be voiced first as a real thesis, a citation, or a reader expectation the context made explicit (the AD-4.3 mechanism). With an antecedent in place, «а Y» is a legitimate antithesis.

AD-6.4. Asymmetric self-correction is never flagged: «вернее…», «то есть…», «по сути…», «не то чтобы X, но Y». Here X is physically present in the preceding clause and the second clause narrows or qualifies the first (refinement, not replacement).

AD-6.5 (quota). Headings: **0** — antithesis in a heading is the loudest tell and reads as clickbait. Sub-headings and leads: rare, and only with a real antecedent in the body (default 0). Body: **0–2** legitimate pairs per article (antecedent present, or concrete data on both poles). Manufactured pairs are always 0 regardless of the limit; self-corrections and antecedent-backed antitheses are not counted toward it.

AD-6.6. Single-count with neighbours. A phantom contrast can also read as AD-4 (one-sided rebuttal) or AD-2 (parcellation when split on periods). Count one violation per fragment: AD-6 takes precedence for a symmetric two-pole fork; a one-sided «но на самом деле…» with no named counter-pole stays AD-4. Do not double-charge Structure.

AD-6.7 (scope of strengthening). The trigger set now includes «не просто X, а Y» and «вопрос/суть не в X, а в Y». Two look-alikes are NOT auto-flagged: «не столько X, сколько Y» (a degree-narrowing, cf. AD-6.4) and «важно не X, а Y» without an antecedent (often a real reader priority). A cluster of manufactured pairs bites harder in **С — Structure** (see `scoring.md`); the carve-outs hold — asymmetric self-correction (AD-6.4) and the 0–2 legitimate antecedent-backed body pairs (AD-6.5) are never penalised, and the construction is never banned outright.

AD-6.8 (the quota is not a finding). AD-6.5 sets how many pairs a text may carry; it is not a line to report in place of them. Report each manufactured pair with its own fragment and let the count raise the weight in **С — Structure**. In a measured run a checker reported «два и более на ~150 слов» and dropped one of the pairs it was counting.

**Examples:**

| Wrong | Correct |
|---|---|
| Это не баг, а фича. | Так и задумано. |
| Это не про скорость, а про надёжность. | Это про надёжность. |
| ИИ — это не инструмент. Это образ мышления. | ИИ меняет то, как я думаю о задаче. |
| Дело не в модели, а в промпте. | Всё решает промпт. |
| Не медленно, а быстро. | Отвечает за 200 мс. |
| Это не просто инструмент, а целая экосистема. | Это экосистема: редактор, отладчик, пакетный менеджер. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Хочу и буду. Вернее, буду, когда хочу. | Asymmetric self-correction: X is present, the second clause narrows it. |
| Это не неуверенность — это точность мышления вслух. | The negated pole is a real reader misreading the context invites (antecedent satisfied). |
| Выросло не на 2%, а на 40%. | Both poles carry data; deletion loses information. |
| Не мытьём, так катаньем. | Fixed idiom. |
| Не оферта, а приглашение делать оферты. | Legal formula where the binary is operative semantics. |
| Не столько баг, сколько недокументированное поведение. | Degree-narrowing («не столько… сколько»): X is present and partly true, the clause refines rather than replaces (cf. AD-6.4). |
| Он сделал это не просто так, а с умыслом. | «не просто так» is a fixed idiom («for a reason»), not the «не просто X, а Y» hype escalation. |

**Severity:** Medium — the manufactured antithesis is the single strongest machine-generation tell in this addenda set, and density compounds fast. Primary signal in the **С — Structure** dimension (supporting **Ч — Clarity**), reflected in the С rubric anchors. A cluster of manufactured pairs materially lowers the С score; a single antecedent-backed pair does not. Still cannot, by itself, trigger a non-compensatory cap — that stays reserved for the hard dimensions and the global < 3.0 floor.

**Acknowledged:** identified from corpus analysis of AI-generated Russian prose (2026-06); the contrastive-negation antithesis runs at high density in machine drafts and near-zero in human reference corpora.


---

## AD-7. Preemptive virtue qualifier (непрошенная оговорка «без воды»)

**Problem:** a trailing manner-flourish that asserts the author's virtue by denying a fault the reader never raised — «без воды», «без виляния», «без лишних слов», «начистоту», «честно говоря», «прямо скажем», «не побоюсь этого слова», «и без всякой магии». The statement reassures the reader against a vice nobody suspected, so the qualifier carries no information and only performs sincerity. It is a cousin of AD-4: where AD-4 rebuts an unvoiced external claim, AD-7 denies an unvoiced fault of the author's own delivery. The same flourish also appears in positive polarity — «чётко, по делу», «коротко и ясно», «простыми словами», «разложу по полочкам» — naming a delivery virtue the text should simply demonstrate; it is flagged identically. Virtue is shown by the writing, never announced.

**Sources:**
- Telling vs. showing, and self-praise as an empty signal: editorial practice, informed by Нора Галь «Слово живое и мёртвое» on needless self-qualification
- Adjacent to AD-4 (unprovoked rebuttal) and AD-3 (patronizing explanation)
- Independently formulated from corpus analysis of AI-generated Russian prose

**Trigger constructions:**

- «без воды» / «без виляния» / «без лишних слов» / «без обиняков» — a manner-flourish denying a vice of delivery
- «честно говоря» / «начистоту» / «прямо скажем» / «не побоюсь этого слова» — announced sincerity
- «скажу честно» / «если честно» / «честно» / «по-честному» / «не буду врать» / «откровенно говоря» / «положа руку на сердце» — the same announced sincerity in the forms a model reaches for most. Where the sincerity is predicated of the whole piece rather than of one statement — «честный разбор», «давайте будем честны» — the home is AD-10; charge the fragment once (AD-10.6)
- «и без всякой магии» / «без всяких фокусов» / «без нервов» appended to a claim about one's own product or method
- «чётко, по делу» / «коротко и ясно» / «простыми словами» / «разложу по полочкам» / «на пальцах» — a positive-form flourish praising the author's own delivery (the polarity twin of «без воды»)
- a self-praise tricolon about one's own product or method — «быстро, качественно, надёжно» — where each adjective is itself an unproven claim (cf. `info-style.md` §B) and the rule-of-three stacking is the added tell
- a virtue adverb stacked on a self-statement where deleting it loses no fact

**Rules:**

AD-7.1. Flag a preemptive virtue qualifier — whatever its surface form, including a «без [vice]» phrase, announced sincerity in any syntactic form (parenthetical «честно говоря», finite verb «скажу честно», bare adverb «честно»), a positive-form delivery flourish, a self-praise tricolon, and a virtue adverb stacked on a self-statement — when it (1) characterises the author's own product, delivery or method, (2) answers an objection the text never raised, whether by denying the vice or by asserting its opposite, and (3) carries no information — deleting it loses no fact. The carve-outs of AD-7.3, AD-7.4, AD-7.5 and AD-7.7 apply to every branch of this test, the positive-polarity branch included: an informative «без», a genuine epistemic qualifier, a speaker inside the text, a qualifier previewing concrete content that immediately follows, and an established genre or rubric label are not flagged.

AD-7.2. Rewrite by deleting the qualifier and letting the statement stand; the virtue is demonstrated by the writing. «Соберу мысль, без виляния» → «Соберу мысль».

AD-7.3. Allow informative «без»: «кофе без сахара», «работает без интернета», «ноль vi.*-моков, без заглушек», «без регистрации» — here «без» names a real removed ingredient, dependency, or feature, not a manner.

AD-7.4. Allow a genuine epistemic qualifier that carries information: «строго говоря, это аппроксимация», «по сути» when it narrows the claim (cf. AD-6.4). These calibrate meaning; they do not advertise sincerity.

AD-7.5 (register — whose voice it is). The carve-out holds when the construction belongs to a **speaker inside the text**: a line of dialogue, a quotation, an interviewee, a character. «— Скажу честно, я не знаю, — ответил инженер» is speech and is not flagged. It does **not** hold when the author says it about their own text, in any register — an author addressing the reader in a conversational tone is still the author, and «скажу честно» in a lead is the self-promotional flourish AD-7.1 describes, not spoken connective tissue. This is a deliberate narrowing: the earlier wording exempted the conversational register as such, and the assistant register — a monologue written to sound like speech — fell straight through it, which is how a construction listed among the triggers went unflagged for a year. AD-10.4 is the canonical statement of this boundary; it governs both rules, and is stated there in full because a rule read on its own must decide on its own.

AD-7.6. Single-count with neighbours. A «без [vice]» flourish can also be caught by AD-2 (parcellation / filler rhythm in Structure) — the «без воды» tail in «Расскажу последовательно, доступно, без воды» is one fragment, not two faults. Count one violation per fragment: charge it to AD-7 (**Ч — Clarity**) when the defect is the empty self-virtue, to AD-2 (**С — Structure**) when the defect is the staccato or filler rhythm. Never double-charge the same fragment across Ч and С.

AD-7.7. Positive-form delivery self-praise is flagged under AD-7.1: it is the positive-polarity branch of clause (2), and two carve-outs apply to it specifically. «Объясню чётко, по делу» → «Объясню» (then actually do). Do NOT flag a qualifier that previews concrete content that immediately follows: «Объясню коротко: значение лежит в стеке» carries information about what comes next and stays. An established genre or rubric label — a column or book title «… на пальцах», «… простыми словами» — is a recognised popular-science convention, not a delivery flourish, and is not flagged.

AD-7.8 (single-count with info-style §B). The unproven-claim tricolon «быстро, качественно, надёжно» is also three §B unproven adjectives (`info-style.md` §B, «качественный»/«надёжный»/«эффективный» family). Count it once in **Ч — Clarity**: charge AD-7 when the defect is the self-virtue rule-of-three, or info-style §B when the defect is the missing evidence per the domain brief — never both for the same fragment.

**Examples:**

| Wrong | Correct |
|---|---|
| Соберу мысль, без виляния. | Соберу мысль. |
| Отвечу честно, без воды: дедлайн сорван. | Дедлайн сорван. |
| Скажу прямо, без обиняков: тест не проходит. | Тест не проходит. |
| Это работает, и без всякой магии. | Это работает. |
| Max 20× закрывает запрос начисто, без нервов. | Max 20× закрывает запрос. |
| Объясню чётко, по делу, без воды. | Объясню. |
| Расскажу простыми словами, разложу по полочкам. | Расскажу. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Кофе без сахара. | «без» names a real removed ingredient. |
| Ноль vi.*-моков — без заглушек. | «без» names a real removed thing. |
| Сервис работает без интернета. | «без» names a real capability. |
| Строго говоря, это аппроксимация. | Epistemic qualifier carrying real information. |
| Объясню коротко: значение лежит в стеке. | «коротко» previews concrete content that immediately follows (AD-7.7). |
| Работает быстро: ответ за 200 мс. | A speed claim backed by a number, not a self-virtue flourish. |

**Severity:** Low. Secondary signal in the **Ч — Clarity** dimension (supporting **С — Structure**). Cannot trigger non-compensatory caps alone.

**Acknowledged:** identified from corpus analysis of AI-generated Russian prose (2026-06); the «без [vice]» self-virtue flourish recurs in machine drafts and reads as announced rather than demonstrated quality.


---

## AD-8. Assistant-register meta-commentary (сервисные реплики ассистента)

**Problem:** a chatbot-persona flourish that addresses the reader as a live interlocutor or narrates the helping transaction instead of carrying the subject — a sycophantic acknowledgement of the question («Отличный вопрос!», «Прекрасная идея», «Вы абсолютно правы»), or an assistant sign-off offering further help («Надеюсь, это помогло», «Готов помочь», «Обращайтесь, если что»). It breaks the fourth wall of written prose: it talks about the helping exchange rather than delivering content. A cousin of AD-7 — both perform a stance instead of demonstrating it — but distinct in that AD-7 praises the text's quality while AD-8 performs the assistant's service persona.

**Sources:**
- Telling vs. showing, and respect for the reader's time: editorial practice, informed by Нора Галь «Слово живое и мёртвое»
- Adjacent to AD-7 (preemptive virtue) and to business-writing email-closing norms
- Independently formulated from corpus analysis of AI-generated Russian prose

**Trigger constructions:**

- «Отличный вопрос!» / «Прекрасный вопрос» / «Хороший вопрос» / «Прекрасная идея» / «Вы абсолютно правы» — a sycophantic acknowledgement of the reader as interlocutor
- «Надеюсь, это помогло» / «Надеюсь, было полезно» / «Готов помочь» / «Обращайтесь, если что» / «Если будут вопросы — спрашивайте» — an assistant sign-off offering further help
- «Сейчас всё объясню» / «Давайте я расскажу» narrating the helping process where no real internal cross-reference is meant

**Rules:**

AD-8.1. Flag a flourish that (1) addresses the reader as a conversational interlocutor or narrates the helping transaction, and (2) carries zero subject content — deleting it loses no fact and the surrounding text stands whole.

AD-8.2. Rewrite by deleting the flourish: open with the answer, end on the last substantive point. «Отличный вопрос! Давайте посмотрим…» → start with the answer.

AD-8.3. Cross-reference, not double-charge. A genuine call to action with a real channel in correspondence — «пишите на support@…», «звоните в будни» — is business-writing territory, and an over-bloated email closing is already covered (cf. `business-writing.md:158`, `anti-patterns.md:90`). AD-8 targets the persona leak into article or documentation prose, not a real email CTA; charge a given fragment once.

AD-8.4 (register carve-out). Not flagged in genuine live dialogue, chat-support exchanges, or interview and quoted registers, where the speaker is responding to a real interlocutor: a support reply «Спасибо за обращение! Подскажите номер заказа», or «„Хороший вопрос“, — ответил инженер», is natural discourse (cf. AD-2.3, AD-7.5). A standalone «Готов помочь» in a real contact or footer block is a genuine offer, not meta-commentary. A sincere authorial wish in a book preface, foreword, or acknowledgements («надеюсь, книга окажется полезной») is a conventional register, not a chat-persona leak. The target is the assistant persona injected into monologue or educational prose, not a one-way FAQ that answers anticipated questions.

AD-8.5. Single-count with neighbours. A sign-off that also reads as filler rhythm can be caught by AD-2; charge the empty-persona defect to AD-8 (**Ч — Clarity**), the staccato or filler defect to AD-2 (**С — Structure**). Never double-charge the same fragment.

**Examples:**

| Wrong | Correct |
|---|---|
| Отличный вопрос! Давайте разберёмся. | (delete; open with the answer) |
| Вы абсолютно правы, и вот почему. | Вот почему. |
| Надеюсь, это было полезно. Обращайтесь! | (delete; end on the last substantive point) |
| Готов помочь с любыми вопросами по теме. | (delete) |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Спасибо за обращение! Подскажите номер заказа. | Real support dialogue with a live user. |
| Если остались вопросы по договору — пишите на support@example.com. | Genuine CTA with a real channel (cf. business-writing.md:158). |
| «Хороший вопрос», — ответил инженер. | Quoted dialogue / interview register. |
| Вы правы: в расчёте действительно ошибка. | A genuine concession in real correspondence, carrying a fact. |

**Severity:** Low. Secondary signal in the **Ч — Clarity** dimension (supporting **С — Structure** at lead and closer position). Cannot trigger non-compensatory caps alone.

**Acknowledged:** identified from corpus analysis of AI-generated Russian prose (2026-06); the assistant-persona flourish leaks the chat register into monologue text and reads as service performance rather than content.


---

## AD-9. Hollow opener (пустой зачин)

**Problem:** an opening or transitional flourish that announces explanation instead of delivering it — «давайте разберёмся», «давайте погрузимся», «копнём глубже», «разложим по полочкам», «важно понимать, что», and «итак» used as filler. The lead carries no fact; it only clears the throat before the real first sentence. It works against the inverted pyramid (`info-style.md` §D: the main point goes first, and the first sentence is the paragraph's thesis). The strongest signal is density — a cluster of such openers, one per paragraph, padding a text that never quite begins.

**Sources:**
- Main point first, first sentence as thesis: `info-style.md` §D (structure)
- The throat-clearing openers «стоит отметить, что» / «не секрет, что» are already catalogued as stop-words in `info-style.md` §B (see AD-9.3)
- Independently formulated from corpus analysis of AI-generated Russian prose

**Trigger constructions:**

- «давайте разберёмся» / «давайте погрузимся» / «копнём глубже» / «разложим по полочкам» — a narrated descent into the topic with no content
- «важно понимать, что» / «здесь важно понять» / «нужно понимать» — a hedged preamble before a claim
- «итак,» / «как известно,» used as a paragraph opener that introduces nothing new
- a lead whose only content is the promise to explain
- the strongest signal: a cluster of two or more such openers within a short section (~200 words)

**Rules:**

AD-9.1. Flag an opener or transition that (1) announces explanation rather than delivering it, and (2) carries zero increment — deleting it loses no fact and the next sentence stands as the real lead. A cluster of two or more hollow openers in a paragraph or short section is the primary signal; an isolated instance is weak.

AD-9.2. Rewrite by deleting the flourish and promoting the first substantive sentence to the lead (`info-style.md` §D).

AD-9.3 (single-count with info-style §B). The throat-clearing openers «стоит отметить, что», «следует подчеркнуть», «нельзя не отметить», «не секрет, что», «в современном мире» are already stop-words in `info-style.md` §B — apply them there and count once. AD-9 adds the dive-in family («давайте разберёмся», «погрузимся», «важно понимать») not listed in §B, plus the cluster signal. Never charge one fragment to both §B and AD-9.

AD-9.4 (carve-out — genuine connective). «Итак» as a real summative connective that closes a reasoning chain, or a resumptive connective that picks up a narrative thread (cf. `editorial-punctuation.md:119`), is not flagged; only the empty opener «Итак,» that introduces nothing.

AD-9.5 (carve-out — real tutorial). «Давайте разберём» / «давайте посмотрим» in a genuine step-by-step walkthrough, where the next sentence actually begins with concrete steps, is not flagged. The target is the decorative promise with no follow-through.

AD-9.6 (carve-out — informative «важно»). «Важно понимать разницу между TCP и UDP — от неё зависит выбор протокола» carries a real consequence and is not flagged (analogous to AD-7.4). Flag only the empty hedge.

AD-9.7 (carve-out — dialogue register). «Давайте разберёмся» / «давайте посмотрим» in genuine live dialogue or a quoted or interview register, where a real interlocutor proposes to look into something together, is natural speech, not a hollow opener (cf. AD-7.5, AD-8.4).

**Examples:**

| Wrong | Correct |
|---|---|
| Давайте разберёмся, как это работает. | Алгоритм делает три вещи: … |
| В этой статье мы погрузимся в мир машинного обучения. | Машинное обучение… (open with the subject) |
| Важно понимать, что скорость зависит от железа. | Скорость зависит от железа. |
| Итак, что же мы имеем? | (delete; state what we have) |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Итак, из трёх замеров следует: задержка не выше 200 мс. | Genuine summative connective closing a chain (cf. editorial-punctuation.md:119). |
| Давайте разберём по шагам. Шаг 1: откройте файл. | Real tutorial; the next sentence delivers concrete steps. |
| Важно понимать разницу между TCP и UDP — от неё зависит выбор протокола. | The «важно» clause carries a real consequence (cf. AD-7.4). |

**Severity:** Low. Secondary signal in the **С — Structure** dimension (supporting **Ч — Clarity**). A cluster lowers Structure; an isolated opener does not. Cannot trigger non-compensatory caps alone.

**Acknowledged:** identified from corpus analysis of AI-generated Russian prose (2026-06); the hollow opener announces explanation instead of leading with the point and clusters densely in machine drafts.


---

## AD-10. Declared sincerity (объявленная искренность)

**Problem:** the text asserts its own honesty as a property of itself — «честный разбор», «давайте
будем честны», «рассказываю как есть», «без прикрас», «вся правда о…». Sincerity is what a reader
infers from what a text does with an inconvenient fact; announced, it is a claim with no evidence,
and it takes the place of the evidence that would have earned it. AD-7 catches the same reflex
attached to one statement («скажу честно: дедлайн сорван»); AD-10 catches it when honesty is
predicated of the piece or of the block that follows. The label form is the louder of the two and is
graded accordingly, and giving it its own name is what lets the carve-out be stated once instead of
twice.

**Sources:**
- Telling vs. showing, and self-praise as an empty signal: editorial practice, informed by Нора Галь «Слово живое и мёртвое»
- Platform moderation practice treats stylistic resemblance as sufficient grounds on its own, without proof of generation — Habr's site rules as they stood on 27.07.2026, the version announced in the platform's own post of 17.06.2026 (paraphrased, not quoted); this is external evidence that a style-level rule has a real object
- Adjacent to AD-7 (delivery-virtue qualifier) and AD-13 (phantom attribution): all three perform a stance instead of demonstrating it
- Independently formulated from the 2026 review of AI-generated Russian prose

**Trigger constructions:**

- «честный разбор» / «честный обзор» / «честно о…» / «вся правда о…» / «без прикрас» — the piece labelled honest, most often in a title
- «давайте будем честны» / «будем откровенны» / «скажем прямо» opening a paragraph or a section
- «рассказываю как есть» / «пишу как думаю» / «без купюр» / «начистоту»
- a title or lead whose only claim is the author's own sincerity
- the strongest signal: the label in a heading, where the reader has been given nothing yet against which to weigh it

**Rules:**

AD-10.1. Flag a construction when all three hold: (1) it predicates honesty, frankness or candour of the text, of the author's account, or of the block that follows; (2) the author is speaking about their own text; (3) it carries no fact — deleting it loses nothing.

AD-10.2. Rewrite by deleting the label and letting the inconvenient fact do the work it was standing in for. «Честный разбор: почему сроки срываются» → «Почему сроки срываются» — and then name the reason.

AD-10.3. Honesty is demonstrated specifically: an admitted mistake, a number that costs the author something, a stated limit of what is known. Where the demonstration is present the label is redundant; where it is absent the label is false.

AD-10.4 (carve-out — the speaker inside the text). Not flagged when the construction belongs to a speaker inside the text: a line of dialogue, a quotation, an interviewee, a character. «— Скажу честно, я не знаю, — ответил инженер» is speech, not a label. This is the canonical statement of the boundary the narrowed AD-7.5 applies: the carve-out protects a voice inside the text, never the author speaking about their own text.

AD-10.5 (carve-out — informative «честный»). «Честная цена» meaning a price with no hidden fees, «честный вес», «честный тест» meaning one whose method is published — here «честный» names a checkable property of the object, not a virtue of the prose (compare AD-7.3).

AD-10.6 (single-count with AD-7). One fragment, one charge. AD-10 takes it when honesty is predicated of the text or frames what follows; AD-7 takes it when the qualifier modifies a single statement in the flow. Never both.

**Examples:**

| Wrong | Correct |
|---|---|
| Честный разбор: почему проекты срываются | Почему проекты срываются |
| Давайте будем честны — планировать умеет не каждая команда. | Из двенадцати команд в срок уложились три. |
| Рассказываю как есть, без прикрас. | (delete; then tell it) |
| Вся правда о подписках. | Что входит в подписку и что нет. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| — Скажу честно, я не знаю, — ответил инженер. | Speech of a person inside the text (AD-10.4). |
| Честная цена: 4 900 ₽, доставка входит. | «Честный» names a checkable property of the object (AD-10.5). |
| Мы ошиблись в расчёте на 30% и потеряли квартал. | Honesty demonstrated rather than announced (AD-10.3). |
| Строго говоря, это аппроксимация. | Epistemic qualifier carrying information (cf. AD-7.4). |

**Severity:** Medium — the label form is the most conspicuous member of the declared-sincerity family and the one a reader notices first. Primary signal in the **Ч — Clarity** dimension (supporting **Ц — Reader precision**), reflected in the Ч rubric anchors. A label in a heading, or two instances in one text, materially lowers Ч; a single one in the body does not. Still cannot, by itself, trigger a non-compensatory cap.

**Acknowledged:** identified in the 2026 neuroslop review, from a reader-complaint channel and from a probe the author supplied — «скажу честно». That exact form was in no trigger list; its close relative «честно говоря» was, among AD-7's, and the register carve-out then exempted it. So the family was named and the coverage was not, which is the same failure the probe exposed.


---

## AD-11. Mandatory tricolon (обязательная триада)

**Problem:** enumerations that arrive in threes because three is the shape, not because the subject has three parts — «инновационный, трансформирующий, прорывной». The rule of three is a real device with a long rhetorical history; the tell is its automatic application. The giveaways are that the third member rewords the first two, that the members are of unequal rank, and above all that the pattern repeats: a text where every list is three items long is being written by a form, not about a subject.

**Sources:**
- Expressive syntax and the cost of a figure applied mechanically: editorial practice, informed by Розенталь «Справочник по правописанию и стилистике»
- `info-style.md` §B — the unproven-claim adjectives that most often fill the three slots
- AD-7 already names the self-praise tricolon about one's own product; AD-11 is the general case and the two are kept apart by AD-11.5
- Independently formulated from the 2026 review of AI-generated Russian prose

**Trigger constructions:**

- three adjectives in a row, none of them measurable — «инновационный, трансформирующий, прорывной»
- three noun phrases where the third rewords the first two
- every heading in a section followed by exactly three bullets
- «во-первых… во-вторых… в-третьих» where the third point restates the first
- the strongest signal: two or more forced triples in one text

**Rules:**

AD-11.1. Flag a triple when all three hold: (1) the subject does not have exactly three parts — a fourth could be added, or one dropped, with nothing lost; (2) the members are not distinct — one repeats or contains another; (3) deleting a member loses no fact. Density is part of the test, not a separate remark: a cluster of two or more such triples in one text is the primary signal, and an isolated triple is flagged only when every member is an unproven claim from `info-style.md` §B.

AD-11.2. Rewrite by keeping what carries information: two members with distinct content, or one member with a number behind it.

AD-11.3 (density raises severity; it never replaces the findings). Report **each** forced triple with its own fragment and let the cluster raise the weight in **С — Structure**. See «Two rules that govern all the others» for why.

AD-11.4 (carve-out — the subject has three). An exhaustive enumeration — «рожковые, капсульные и автоматические» — three real steps, three measurements, three named parties: not flagged. This is AD-11.1's first test decided the other way: no fourth member could exist, so the three belong to the subject rather than to the form.

AD-11.5 (single-count with AD-7). A triple that praises the author's own product or delivery — «быстро, надёжно, красиво» — is AD-7's self-praise tricolon and is charged there, in **Ч — Clarity**. AD-11 takes the forced triple that is not self-praise, in **С — Structure**. Never both for one fragment.

AD-11.6 (single-count with info-style §B — the SAME fragment only). Where the members of the triple are §B unproven adjectives, count that fragment once: §B when the defect is the missing evidence, AD-11 when it is the forced count. Never both **for that fragment**. An unproven adjective elsewhere in the sentence — «хороший процесс должен быть прозрачным, предсказуемым и управляемым», where «хороший» is the subject and not a member — is a separate defect and is reported separately. Single-count means one charge per fragment, never one charge per sentence.

AD-11.7 (carve-out — oratorical and literary register). The tricolon is a legitimate figure in speeches, manifestos and literary prose, where rhythm is part of the work (cf. AD-2.3, which likewise spares the literary register).

**Examples:**

| Wrong | Correct |
|---|---|
| Инструмент инновационный, трансформирующий и прорывной. | Инструмент собирает отчёт за 4 с вместо 3 мин. |
| Процесс должен быть прозрачным, предсказуемым и управляемым. | Процесс должен быть предсказуемым: срок известен на старте. |
| Он меняет подход к планированию, к оценке и к контролю. | Он меняет оценку сроков. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Кофемашины бывают рожковые, капсульные и автоматические. | Exhaustive enumeration: no fourth type exists (AD-11.4). |
| Задержку определяют три вещи: расстояние, загрузка канала и версия протокола. | Three distinct mechanisms, each named (AD-11.4, cf. AD-12.3). |
| Сначала открываем конфиг, затем меняем порт, затем перезапускаем сервис. | Three real steps of a procedure. |
| Мы измеряли в Москве, Франкфурте и Сингапуре. | Three named places, each carrying its own datum. |

**Severity:** Low. Secondary signal in the **С — Structure** dimension (supporting **Ч — Clarity**). A cluster lowers Structure; an isolated triple does not. Cannot trigger non-compensatory caps alone.

**Acknowledged:** identified in the 2026 neuroslop review, from a reader-complaint channel where the forced three was named repeatedly and independently of any single model family.


---

## AD-12. Hollowed mechanism (выхолощенность)

**Problem:** a claim that something matters, with the operative term replaced by a placeholder — «зависит от различных факторов», «есть целый ряд причин», «имеет свои особенности», «определённая специфика». The sentence has the shape of an explanation and none of its content: the reader cannot act on it, check it, or disagree with it, because nothing has been said. It is the most economical way for a paragraph to pass for informative. Not to be confused with AD-3: AD-3 says the same thing twice, AD-12 says nothing once.

**Sources:**
- `info-style.md` §E — a claim without a number or a source is an opinion; §B lists «определённый» among the stop-words with the instruction to name the specific thing
- `info-style.md` §D — the worked contrast between «различные проблемы» and a problem named
- `editorial-grammar.md` §E.2 — «следует учитывать следующие факторы» is catalogued there as a tautology (the cognate pair «следует… следующие»): the neighbouring defect is the wording, the defect here is the emptiness
- Independently formulated from the 2026 review of AI-generated Russian prose

**Trigger constructions:**

- «различные факторы» / «ряд факторов» / «целый ряд причин» / «по ряду причин»
- «свои особенности» / «своя специфика» / «определённая специфика» / «известные нюансы»
- «многие аспекты» / «те или иные» / «в той или иной степени» / «разный эффект»
- «зависит от многого» / «всё индивидуально» / «зависит от ситуации» as a whole answer
- «играет важную роль» / «имеет большое значение» where neither the role nor the significance is named (cf. AD-13)

**Rules:**

AD-12.1. Flag a clause when all three hold: (1) it asserts influence, dependence, importance or difficulty; (2) the term carrying the mechanism is a placeholder rather than a name — «факторы», «аспекты», «особенности», «специфика», «моменты», «нюансы» are the common ones, and so is any bare quantifier or degree word standing in for the mechanism: «многое», «те или иные», «в той или иной степени», «разный», «большое значение». The list is open; the test is whether the word tells the reader WHICH; (3) nothing in the piece names what the placeholder stands for — not this sentence, not its neighbours, and not a section, table or source the sentence points to (AD-12.3).

AD-12.2. Rewrite by naming: replace the placeholder with the two or three actual items. If they cannot be named, the sentence was not knowledge, and deleting it loses nothing.

AD-12.3 (carve-out — the placeholder is cashed out, here or elsewhere). «Задержку определяют три вещи: расстояние до дата-центра, загрузка канала и версия протокола» — the placeholder is a colon away from its content. It counts just as much when the cash-out is deferred by an explicit pointer: «объясняется рядом факторов, разобранных в разделе 4», a reference to a table, an appendix, or a named source. That is the normal convention of technical, normative and academic writing, and the window is the whole document — the same reach AD-13.3 gives an attribution named once and referred to later. The defect is the placeholder that stays empty, not the one answered on another page.

AD-12.4 (carve-out — honest uncertainty). A stated limit of knowledge that says what is unknown and why — «мы не знаем, откуда разброс: замеры шли на разном железе» — is information. The target is a pretence of an answer, never the admission that there is none.

AD-12.5 (single-count with info-style §B). «Определённый» is already a §B stop-word. Charge the fragment once: §B when the defect is the empty determiner, AD-12 when it is the unnamed mechanism. Never both.

AD-12.6 (single-count with AD-13). A clause can carry both defects in two different fragments — «исследования показывают, что влияют различные факторы» is AD-13 on the attribution and AD-12 on the mechanism, which is two fragments and two charges. One fragment is never charged to both.

**Examples:**

| Wrong | Correct |
|---|---|
| Результат зависит от различных факторов. | Результат зависит от версии протокола и от загрузки канала. |
| У каждого проекта своя специфика. | В этом проекте два подрядчика и общий репозиторий. |
| Многие аспекты процесса изучены недостаточно. | Мы не измеряли, как влияет размер команды. |
| Мотивация имеет большое значение. | Команды с недельным циклом обратной связи закрывали задачи на 20% быстрее. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Задержку определяют три вещи: расстояние, загрузка канала и версия протокола. | The placeholder is cashed out in the same sentence (AD-12.3). |
| Мы не знаем, откуда разброс: замеры шли на разном железе. | Honest uncertainty, with the reason named (AD-12.4). |
| Специфика ГОСТ 8.417 в том, что единицы пишутся без точки. | «Специфика» followed by the specific thing. |

**Severity:** Medium — a text made of these sentences is indistinguishable in shape from an informative one, which is exactly what makes it expensive. Primary signal in the **Ц — Reader precision** dimension (supporting **Ч — Clarity**), reflected in the Ц rubric anchors. Two or more hollowed clauses land Ц in the 5–6 band or lower. Cannot trigger a non-compensatory cap alone.

**Acknowledged:** identified in the 2026 neuroslop review from a reader-complaint channel; checked against the corpus before proposing, where the pattern was found absent — the nearest neighbours are a tautology entry about the wording and a worked example about a different point.


---

## AD-13. Phantom attribution (неопределённая атрибуция)

**Problem:** the gesture of citing, without a source — «исследования показывают», «эксперты отмечают», «учёные доказали», «по мнению аналитиков». The sentence borrows the authority of a body of work that is never identified, so the reader cannot go and look. This is worse than an unsupported claim, not better: a bare claim invites the question «откуда это?», while a dressed one discourages it. Distinct from the unproven-claim adjectives of `info-style.md` §B — there no source is offered at all, here a source is imitated.

**Sources:**
- `info-style.md` §E — a number or claim without a source is an opinion, not a fact
- Adjacent to AD-10: both perform an authority instead of holding one
- Independently formulated from the 2026 review of AI-generated Russian prose

**Trigger constructions:**

- «исследования показывают» / «согласно исследованиям» / «учёные доказали»
- «эксперты отмечают» / «специалисты рекомендуют» / «аналитики прогнозируют»
- «принято считать» / «общеизвестно, что» / «как показывает практика» / «статистика говорит»
- «играет ключевую роль» — a rank assigned with nobody ranking and no criterion given. Where the defect is the missing mechanism rather than the missing source, AD-12 is the home; charge the fragment once
- the strongest signal: an attribution that no sentence in the piece ever redeems

**Rules:**

AD-13.1. Flag an attribution when the source is not identifiable anywhere in the text: no author, organisation, publication, date or link, here or elsewhere in the piece.

AD-13.2. Rewrite by naming the source, or by dropping the attribution and owning the claim. «Исследования показывают, что удалёнка снижает продуктивность» → «По данным опроса N (2025, 1 200 респондентов), …» or «На наших четырёх проектах продуктивность упала».

AD-13.3 (carve-out — a real source). Named, dated and checkable — «По данным Росстата за 2025 год» — is not flagged, and neither is a later reference to a source the piece named once.

AD-13.4 (carve-out — consensus with a citation). Where the existence of a consensus is itself the point and a citation follows, «принято считать» is a legitimate framing move rather than a phantom.

AD-13.5 (carve-out — marked personal experience). «По моему опыту», «у нас на проекте», «в трёх наших внедрениях» attribute to the author, who is identifiable and answerable. That is a source.

AD-13.6 (single-count with info-style §B). An unproven adjective and a phantom attribution in one fragment are one charge: §B when the defect is the unevidenced claim, AD-13 when it is the imitated citation. Never both.

**Examples:**

| Wrong | Correct |
|---|---|
| Исследования показывают, что удалёнка снижает продуктивность. | По данным опроса Института X (2025, 1 200 респондентов), продуктивность упала на 8%. |
| Эксперты отмечают: рынок вырастет. | ЦБ в июльском прогнозе ждёт роста на 3%. |
| Учёные доказали, что кофе полезен. | (delete, or cite the study) |
| Мотивация играет ключевую роль. | Без обратной связи в первую неделю уходит каждый третий новичок. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| По данным Росстата за 2025 год, зарплата выросла на 12%. | Named, dated, checkable (AD-13.3). |
| По моему опыту, миграции такого размера занимают неделю. | Attributed to the author, who is answerable (AD-13.5). |
| Принято считать, что индексы ускоряют чтение; замер ниже это опровергает. | Consensus named in order to be tested, and it is (AD-13.4). |

**Severity:** Medium — an imitated citation does more damage than a missing one, because it suppresses the reader's question. Primary signal in the **Ц — Reader precision** dimension (supporting **Ч — Clarity**), reflected in the Ц rubric anchors. Cannot trigger a non-compensatory cap alone.

**Acknowledged:** identified in the 2026 neuroslop review from a reader-complaint channel; checked against the corpus before proposing, where the pattern had no entry of any kind.


---

## AD-14. Chat transcript as the artifact (диалог с нейросетью вместо текста)

**Problem:** the published piece is the log of a conversation with a model. Its skeleton is a sequence of turns rather than an argument: questions become headings, answers become sections, and the piece ends when the conversation did. The reader is handed the raw material and asked to do the author's work on it. This is one of the set's two rules charged to the **document** rather than to a fragment — the other is AD-15 — and no local edit removes either, because the defect is the shape.

**Sources:**
- Platform editorial policy names this artifact directly: Habr's site rules as they stood on 27.07.2026 (the version announced 17.06.2026) list, among material that should not be posted, pieces that are the author's dialogues with neural networks and pieces consisting only of model answers; a separate section of the same rules restricts unfinished drafts and streams of consciousness (paraphrased, not quoted)
- Distinct from AD-8, which flags an assistant reply leaking into monologue prose: that is a sentence, this is a skeleton (see AD-14.5)
- `info-style.md` §D — the inverted pyramid a transcript cannot have, because a conversation is ordered by turns
- Independently formulated from the 2026 review of AI-generated Russian prose

**Trigger constructions:**

- alternating speaker labels — «Я:» / «Модель:», «Пользователь:» / «Ответ:», «Промпт:» / «Результат:»
- the piece's headings are the questions that were asked
- prompt echo: each answer restates the question before answering it
- the closing is the end of the exchange — «Спасибо, теперь понятно» — rather than a conclusion
- no sentence in the piece is a claim of the author's own

**Rules:**

AD-14.1. Charge the document when both hold: (1) its structure is a sequence of exchanges rather than an exposition; (2) the author contributes no claim of their own — no thesis, no synthesis, no assessment of what the model said.

AD-14.2. Rewrite by writing the piece: state what you learned, in the order a reader needs it, and keep from the transcript only what a reader must see in order to check you.

AD-14.3 (level — the document charge ADDS, it never replaces). AD-14 is a property of the whole document: attach it once, not to an individual line, and a single quoted exchange inside an ordinary article is not this rule at all. The charge adds one finding and replaces none: every defect inside the transcript is reported as it would be otherwise (see «Two rules that govern all the others»).

AD-14.4 (carve-out — the transcript as evidence). A log published as evidence for the author's own finding, with the finding stated and the log subordinate to it, is not flagged: a prompt-engineering write-up, a documented experiment, a bug report, a reproduction. The test is one deletion: remove the log — does a claim of the author's remain? If yes, the log was evidence.

AD-14.5 (relationship to AD-8 — not a double charge). AD-8 flags individual assistant replies inside a text; AD-14 flags the text's shape. Repair every AD-8 flourish and an AD-14 document is still a transcript; repair the shape and the flourishes were never the problem. The two defects survive each other's repair, so both are charged — this is not one fragment counted twice.

AD-14.6 (carve-out — human dialogue). An interview, a Q&A with a human respondent, a play, a chat-support excerpt, a quoted exchange: dialogue between people is a genre, not a tell (cf. AD-8.4).

AD-14.7 (carve-out — the transcript was what was asked for). Where the user's brief is a transcript — documentation of a session, a teaching example showing prompts and outputs — the style priority stated in `SKILL.md` applies and these defaults do not override the request.

**Examples:**

| Wrong | Correct |
|---|---|
| **Я:** Объясни кеширование. **Модель:** Отличный вопрос! … | ETag сравнивает версию ресурса; при совпадении сервер отвечает 304. (then the author's own account) |
| Заголовок раздела: «А что такое ETag?» | Заголовок раздела: «ETag: когда сервер отвечает 304» |
| Закрытие: «Спасибо, теперь понятно.» | Закрытие: вывод, ради которого текст написан. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Ниже — расшифровка: я задал модели один вопрос трижды и свёл ответы в таблицу. Разброс — вывод статьи. | The log is evidence for the author's own finding (AD-14.4). |
| «Хороший вопрос», — ответил инженер. | Quoted human dialogue (AD-14.6, cf. AD-8.4). |
| Интервью с разработчиком, вопрос — ответ. | An interview is a genre. |

**Severity:** High — the highest in this addenda set, and it means something specific: the defect is not a fragment to repair but the form of the piece, so no sequence of local edits removes it. Primary signal in the **С — Structure** dimension (supporting **Ц — Reader precision**), reflected in the С rubric anchors: a document charged with AD-14 does not reach the upper Structure bands. It does **not** introduce a new non-compensatory cap — those stay reserved for the hard dimensions and the global floor (see `scoring.md`). Severity here says how far the dimension moves, not that a new cap exists.

**Acknowledged:** identified in the 2026 neuroslop review from the editorial-policy channel, where a Russian platform names the artifact in its own rules rather than in commentary.


---

## AD-15. Search-engine addressee (адресат — поисковик, а не читатель)

**Problem:** the implied reader is a crawler. Nothing in the text is ungrammatical and no single sentence is wrong; the piece is simply not addressed to a person. The query phrase is repeated verbatim where a language addressed to a reader would use a pronoun; sections are variants of one question rather than steps of an argument; and after reading, the reader still cannot do the thing the piece is about. Two platforms formulate the test the same way, and both formulate it as a question of **addressee** rather than of provenance.

**Sources:**
- Habr's site rules as they stood on 27.07.2026 (the version announced 17.06.2026) name material aimed at search engines rather than living readers among the content it restricts (paraphrased, not quoted)
- Яндекс Вебмастер lists automatically generated *and* useless-to-the-user content among the examples its algorithms may restrict; the conjunction is operative — machine origin alone is not the stated violation (paraphrased, not quoted)
- `info-style.md` §A (полезное действие) and §D (main point first) — the two properties such a text lacks
- `scoring.md` notes that formula tools score an SEO text highly without any real quality; that is the observation, and this rule is the judgement it calls for
- **The sentence-level signature below is this corpus's own formulation.** Neither platform states what the tell looks like inside a sentence; only the criterion of addressee is theirs

**Trigger constructions:**

- the exact query phrase repeated verbatim in the title, in a heading, and again in the body
- headings that are variants of one another rather than steps — «как выбрать X», «какие бывают X», «сколько стоит X»
- the subject named by its full noun phrase where a pronoun or a short form would serve
- a «выводы» section that restates the headings and adds no number
- length without a fact: the piece answers a query and leaves the reader unable to act

**Rules:**

AD-15.1. Charge the document when all three hold: (1) a query phrase is repeated where the language would use a pronoun or a short form; (2) sections are variants of one question rather than steps of an argument; (3) after reading, a reader cannot do the thing the piece is about — no number, no criterion, no named option.

AD-15.2. Rewrite by answering the question once and with specifics: name the options and the criterion by which one is chosen, with prices where they decide it.

AD-15.3 (carve-out — the user's explicit brief). Where the user asks for SEO copy, the style priority stated in `SKILL.md` applies: their request overrides these defaults. State what the trade-off costs and write what was asked.

AD-15.4 (carve-out — functional repetition). Technical writing repeats an identifier because a pronoun would be ambiguous — «поле `updated_at` меняется при каждой записи, поле `created_at` — нет». Reference works, glossaries and legal texts repeat the term by design. The defect is the addressee, not the repetition.

AD-15.5 (carve-out — optimisation that still serves the reader). Keyword research legitimately shapes what a useful text covers. A piece that answers the query with facts is not flagged for having the query in its title.

AD-15.6 (level — the document charge ADDS, it never replaces). A note on what the repetition is and is not: `editorial-grammar.md` §E defines tautology as ADJACENT cognates and pleonasm as words duplicating each other's meaning, so a query phrase repeated across four paragraphs is neither, and the corpus has no separate rule for distant lexical repetition. That repetition is AD-15's own evidence and belongs to AD-15 alone — do not borrow a Г finding the corpus does not carry. Like AD-14, this rule is charged to the document, and the repetitions are the evidence for that one charge rather than one AD-15 finding each. That is the **only** thing it absorbs. Every other defect in the same text is reported exactly as it would be without this rule: the stop-words and unproven claims in **Ч**, any pleonasm or tautology the corpus already catalogues in **Г** (`editorial-grammar.md` §E), the passive constructions, the missing полезное действие, the headings that are not theses. A summary that costs the writer the list of lines to fix is not a summary (see «Two rules that govern all the others»).

**Examples:**

| Wrong | Correct |
|---|---|
| Купить кофемашину в Москве: как выбрать кофемашину для дома | Как выбрать кофемашину для дома |
| Цена кофемашины зависит от типа кофемашины и производителя кофемашины. | Цена зависит от типа и производителя: рожковые — от 12 000 ₽, автоматические — от 40 000 ₽. |
| Раздел «Как выбрать кофемашину для дома: выводы», пересказывающий предыдущие заголовки | Раздел с рекомендацией: какая модель кому подходит и почему |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Поле `updated_at` меняется при каждой записи, поле `created_at` — нет. | Repetition because a pronoun would be ambiguous (AD-15.4). |
| Заголовок «Как выбрать кофемашину» над текстом с ценами и критериями | The query is answered with facts (AD-15.5). |
| Глоссарий, где термин повторён в каждой статье | Reference format (AD-15.4). |

**Severity:** High — like AD-14, the defect is the piece rather than a phrase in it, and the reader's loss is total: the text is about their question and gives them nothing. Primary signal in the **Ц — Reader precision** dimension (supporting **С — Structure**), reflected in the Ц rubric anchors: a document charged with AD-15 does not reach the upper Ц bands. It does **not** introduce a new non-compensatory cap (see `scoring.md`).

**Acknowledged:** identified in the 2026 neuroslop review from the editorial-policy channel, where two platforms independently formulated the same test of implied addressee.


---

## AD-16. Additive pseudo-pair («не только X, но и Y»)

**Problem:** a pair joined by «не только… но и», «как… так и», «и… и», in which the second pole adds nothing — it rewords the first, or is contained in it, or both are empty. The construction promises an increment and delivers a rhythm. It is the neighbour of AD-6 and not the same rule: there an opposition with no antecedent, here an addition with no content.

**Sources:**
- `editorial-grammar.md` — the corpus's only «не только… но и» entry is a predicate-agreement rule, a different subject entirely; the two do not collide
- Informed by a 2025 linguo-pragmatic study of AI-assisted Russian social-media posts (cf. Оломская, Юрова; CyberLeninka), which counts the construction among the clichés it treats as markers of generated text. **The density threshold is this corpus's own caution, not the study's finding:** the study measured 38 posts of one political-SMM channel, a genre that reaches for the construction anyway, so the frequency it reports cannot carry a per-sentence rule and the threshold keeps an isolated pair out of the flag
- Distinct from AD-6 (see AD-16.5)
- Independently formulated from the 2026 review of AI-generated Russian prose

**Trigger constructions:**

- «не только X, но и Y» where Y rewords X or is contained in it
- «как X, так и Y» with the same defect
- «и X, и Y» with synonymous poles
- a cluster of two or more such pairs in a short text — density is the signal

**Rules:**

AD-16.1. Flag a pair when all three hold: (1) **no increment** — Y states nothing X did not; (2) **not a contrast** — this is addition, so it is not AD-6 and must not be charged there; (3) **deletable** — drop «не только» and one pole, and no fact is lost. Density belongs to the test: two or more such pairs in one text is the signal, and an isolated pair is not flagged.

AD-16.2. Rewrite as the single claim that survives, and give it something to stand on: «не только удобный, но и комфортный» → name what the interface does, in one step, with a number if there is one.

AD-16.3 (carve-out — a real pair). «Не только в Москве, но и в Новосибирске: 12 мс и 47 мс» — AD-16.1's increment test decided the other way: each pole carries its own number, and deleting either loses it.

AD-16.4 (carve-out — scope). «Не только для физлиц, но и для ИП» defines who is covered. Scope-widening is operative content, frequently legal, and is never flagged.

AD-16.5 (single-count with AD-6). A fragment is charged once. AD-6 takes a symmetric opposition whose negated pole has no antecedent; AD-16 takes an addition whose second pole has no content. If a construction reads as both, it is almost always AD-6 — check for a rejected pole before charging here.

AD-16.6 (single-count with info-style §B — the SAME fragment only). Where both poles are §B unproven adjectives, count that fragment once: §B for the missing evidence, AD-16 for the empty pair. An unproven adjective outside the pair stays its own finding; single-count is per fragment, never per sentence.

AD-16.7 (density raises severity; it never replaces the findings). Report **each** pair with its own fragment and let the count raise the weight. See «Two rules that govern all the others».

AD-16.8 (the pair and the synonymy are two defects, not one). «Не только удобный, но и комфортный» carries both: the poles are synonyms, which is a pleonasm and belongs where pleonasms have always belonged — `editorial-grammar.md` §E, in **Г — Grammar** — and the frame adds nothing, which is AD-16, in **С — Structure**. They are separable, and that is the test: «Сервис удобный и комфортный» is the pleonasm with no pair; «не только быстрее, но и дешевле» with two real numbers behind it is neither. Where both hold, report both. In a measured run, folding the pleonasm into AD-16 scored the same text **higher than before the rule against it existed** — Grammar recovered its points because the finding had moved to a Low signal in another dimension. A new rule against a text must never make that text score better.

**Examples:**

| Wrong | Correct |
|---|---|
| Сервис не только удобный, но и комфортный. | Сервис открывает отчёт в два клика вместо семи. |
| Платформа помогает не только экономить время, но и тратить его меньше. | Платформа сокращает сборку отчёта с 3 мин до 4 с. |
| Мы предлагаем как качественные решения, так и решения высокого уровня. | Мы делаем интеграции с 1С и с SAP. |
| Обновление затрагивает не только интерфейс, но и внешний вид. | Обновление меняет интерфейс. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Мы измеряли не только в Москве, но и в Новосибирске: 12 мс и 47 мс. | Both poles carry data (AD-16.3). |
| Скидка действует не только для физлиц, но и для ИП. | Scope-widening: operative content (AD-16.4). |
| Не только студенты, но и преподаватель присутствовал. | The corpus's agreement example: a different rule about a different thing. |

**Severity:** Low. Secondary signal in the **С — Structure** dimension (supporting **Ч — Clarity**). Density is the signal; an isolated pair is not flagged at all. Cannot trigger non-compensatory caps alone.

**Acknowledged:** identified in the 2026 neuroslop review from the linguistic channel; checked against the corpus before proposing, where the construction appears exactly once and as a rule about predicate agreement.

## AD-17. Comma welded to a dash (запятая, сомкнутая с тире)

**Problem:** a clause closes with a comma and the next thought opens with an em dash, so the two
marks end up side by side inside one sentence: «перечисление, у которого правда три элемента, —
выписано в самом правиле». Each mark is correct on its own. Together they are a junction a
person almost never reaches, because a person restructures the sentence first. A model does not
restructure — it applies both rules and prints both marks. The tell is not an error of grammar;
it is the fingerprint of rule-following without an ear.

**Sources:**
- Rozental, §64 «Запятая и тире»: «При „встрече“ внутри предложения запятой и тире сначала
  ставится запятая, а затем тире». **The norm permits the junction** — this rule does not
  contradict the reference, it observes that living prose avoids what the norm allows
- Checked and NOT found: Lebedev's Ководство §143 «Знаки препинания в нестандартных ситуациях»
  does not discuss combining marks at all, and no statement on the subject was found from
  Ilyakhov. **No source forbids the construction, and this rule does not claim one does**
- `editorial-punctuation.md` — the corpus has no rule producing the junction: it emerges from
  two correct rules applied together, which is why nothing caught it
- Independently formulated from the 2026 review of AI-generated Russian prose

**Trigger construction:** `U+002C` followed by any run of horizontal whitespace — none, an
ordinary space, `U+00A0` or `U+202F` — and then `U+2014`, inside a sentence, where the comma
closes a subordinate clause, a participial phrase or an aside, and the dash opens what follows:
a predicate, an aside, a summary, or a second independent clause.

Two things in that sentence were wrong when this rule shipped, and a measurement found both.
«Immediately followed» excluded the non-breaking space R16/R44 REQUIRE before an em dash — so
the rule, as first written, could not fire on a single correctly typeset junction. And the
dash-side list omitted the independent clause, which the Wrong table below has carried from the
start («…только если они уже существуют, — сама она их не создаёт»): the trigger excluded an
example of itself. The list is illustrative; the test is that both marks are demanded by ONE
construction rather than by two, which is what separates this from direct speech (AD-17.1).

**What to do:** remove the need for one of the marks. Split the sentence, or reorder it so the
junction never forms. Do not break the norm by deleting the comma and keeping the dash — that
produces an error where there was only an infelicity.

AD-17.1 (the trigger is a JUNCTION, not the pair of characters). Two marks that each belong to a
different construction are not this rule. Direct speech is the case that matters: in «„Хороший
вопрос“, — ответил инженер» the comma closes the quoted reply and the dash introduces the
author's words. That is the punctuation of direct speech, prescribed and universal, and it is
**never** flagged. Every occurrence of `, —` in this corpus outside this rule's own examples is of that kind — direct speech, in AD-7.5, AD-8.4, AD-10.4, AD-14.6 and their tables.

AD-17.2 (carve-out — homogeneous subordinate clauses before a main clause). Rozental §40 and §46
describe a construction where comma-plus-dash works as a single mark: a run of homogeneous
subordinate clauses closing before the main clause. «Кто виноват, кто прав, — судить не нам».
Not flagged.

AD-17.3 (carve-out — a book, or a text edited as one). The director's scope: the tell is about
the register of everyday professional writing. In literary prose, in a printed book, or when the
task is explicitly the copy-editing of one, the junction is a legitimate authorial rhythm and is
left alone. Where the genre is unclear, ask rather than flag.

AD-17.4 (carve-out — quotation). A junction inside quoted material stays. See «Someone else's
words stay theirs» in `SKILL.md`: an issue in a third party's text may be reported, never edited.

AD-17.5 (single-count with AD-1). A sentence can carry both: AD-1 counts em dashes per paragraph,
AD-17 takes one junction. Where a paragraph is over the dash limit **and** holds a junction,
report AD-1 for the density and AD-17 for the junction — the fixes differ, and removing the
junction usually removes one dash, which is why the order matters: fix AD-17 first, then re-count
for AD-1.

**Examples:**

| Wrong | Correct |
|---|---|
| Перечисление, у которого три элемента, — выписано в самом правиле. | Перечисление из трёх элементов выписано в самом правиле. |
| Команда наполняет каталоги, только если они уже существуют, — сама она их не создаёт. | Команда наполняет каталоги, только если они уже существуют. Сама она их не создаёт. |
| Отчёт, собранный за ночь, — на столе у заказчика. | Отчёт, собранный за ночь, лежит на столе у заказчика. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| «Хороший вопрос», — ответил инженер. | Direct speech: two constructions, not a junction (AD-17.1). |
| — Скажу честно, я не знаю, — ответил инженер. | Same, with a dialogue dash (AD-17.1). |
| Кто виноват, кто прав, — судить не нам. | Homogeneous subordinate clauses before the main clause (AD-17.2). |
| A junction inside a passage being copy-edited as a book. | Literary register (AD-17.3). |

**Severity:** Low. Secondary signal in the **С — Structure** dimension. A single junction is
worth a remark and no more; the signal is density, and the fix is a rewrite the author would
have made anyway. Cannot trigger non-compensatory caps alone.

**Acknowledged:** raised by the director, 29.07.2026, on reading a junction in this project's own
README: normative, and still a tell — «люди так не пишут в живой жизни, даже профессионалы
языка». The research behind it, including what the named sources do **not** say, is recorded in
`~/.claude/plans/ru-text-v2/comma-dash-research.md`.

---

## AD-18. Uppercase band vs. deliberate emphasis (капслок: полоса против выделения)

**Problem:** Russian keyboards have no italic key. In a chat, a ticket, a working plan or a
message to a colleague, uppercase is often the only emphasis a writer has, and it carries load:
urgency, a risk marker, the word the reader must not skip. The corpus used to answer this with a
single unconditioned line — replace uppercase with bold — and the check obeyed it on live texts:
`Вернись к задачам из моего запроса и РАБОТАЙ` became `и **работай**`, `выпущен ПОЛНОСТЬЮ` became
`выпущен **полностью**`, and a working plan lost `БЕЗ`, `УЖЕ`, `НИКОГДА`, the markers by which
that plan was read. Three blind judges, independently, named uppercase turned into italics as a
reason the checked text reads deader than the original.

Two runs over the same source disagreed with each other: one converted six uppercase tokens in an
audit, the other converted none, and inside a single run the same word was lowered in prose and
kept in a status-table cell. The improvisation was sensible and was written down nowhere. An
unconditioned line does not decide — it makes each run guess.

**Sources:** the emphasis convention itself is not disputed by any style authority in this corpus;
what is new here is the boundary. Checked and NOT found: no source in this corpus rules on
uppercase used as emphasis where no other emphasis is available, and none distinguishes a one-word
marker from a shouted paragraph.

**Trigger construction:** a run of **three or more consecutive words** set entirely in uppercase
Cyrillic, each word two letters or longer. Ordinary punctuation attached to a word — a comma, a
colon, a dash between words — does not break the run. A lowercase word breaks it, and **so does a
line break**: a run never spans two lines. That second clause is load-bearing rather than tidy.
Without it an uppercase heading and the uppercase word opening the paragraph below it merge into
one run, and a marker the carve-outs protect gets swallowed by a band it does not belong to.
Count words, not characters: the defect is a band, not a capital letter.

**What to do:** offer to lower the band and mark the load some other way. Offer — the replacement
is proposed, never asserted as the only correct form.

AD-18.1 (carve-out — short emphasis). One or two uppercase words are **never** flagged, whatever
they are and wherever they stand. `СРОЧНО: сервер лежит`, `РАБОТАЙ, не ленись`, `нет ли ЭТИХ ЖЕ
классов` are deliberate emphasis and stay. This is the branch that matters most: the one-word
marker is what the flattening was made of.

AD-18.2 (carve-out — abbreviations). Acronyms and initialisms are outside the rule entirely and do
not count toward the run: `БАМ`, `ВОВ`, `ЕГРЮЛ`, `ЕГРИП`, `ОКВЭД`, `ГОСТ`, `НДС`. Three of them in
a row are three abbreviations, not a band.

AD-18.3 (carve-out — machine text and status cells). Identifiers, constants, environment
variables, SQL keywords, file names and the status words inside a table cell (`ПРИСУТСТВУЕТ`,
`ОТСУТСТВУЕТ`, `НЕТ`) are not prose emphasis and are not flagged. A run of Latin uppercase is not
this rule's subject at all.

AD-18.4 (carve-out — headings). A heading set in uppercase is a layout decision, not a sentence,
and belongs to the design of the document rather than to its prose.

AD-18.5 (single-count with `anti-patterns.md`). The summary table entry for uppercase points here
and carries no policy of its own. Charge a fragment once, under AD-18.

**Examples:**

| Wrong | Correct |
| --- | --- |
| ЭТО НУЖНО СДЕЛАТЬ СЕГОДНЯ, ИНАЧЕ РЕЛИЗ СОРВЁТСЯ | Это нужно сделать сегодня, иначе релиз сорвётся |
| ПРОСЬБА ВНИМАТЕЛЬНО ПРОЧИТАТЬ ВЕСЬ РАЗДЕЛ ЦЕЛИКОМ | Просьба прочитать весь раздел |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
| --- | --- |
| СРОЧНО: сервер лежит | one word, AD-18.1 |
| нет ли ЭТИХ ЖЕ классов в нашем биллинге | two words, AD-18.1 |
| выписка из ЕГРЮЛ и ЕГРИП по коду ОКВЭД | abbreviations, AD-18.2 |
| в ячейке статуса — ПРИСУТСТВУЕТ | status cell, AD-18.3 |
| `SAVE_PAYMENT_METHOD=true` | machine text, AD-18.3 |

**Severity:** Low. Secondary signal in the **Ч — Clarity** dimension. Cannot trigger
non-compensatory caps alone.

**Not a neuroslop tell, deliberately.** This rule is absent from the Neuroslop index above, and
that absence is load-bearing. Uppercase emphasis is a mark of a person typing in a hurry on a
keyboard with no italic key; a model does not shout. Listing it among the tells of machine prose
would route the fast triage path — which reads that index and does not read this file — toward
treating human emphasis as a machine artefact, which is the exact inversion of what this rule is
for.

**Acknowledged:** ruled by the director, 09.08.2026, on two fragments of his own: `СРОЧНО: сервер
лежит` — «намеренная эмоциональность, а не слоп или ошибка, живость языка так поддерживается».
The measurement behind the threshold is recorded in
`~/Projects/_scratch/ru-text-flattening/inventory-15-registers.md`: the longest uppercase run in
the live corpora is two words, and every one of the sixteen conversions the check performed was
one or two words long.
