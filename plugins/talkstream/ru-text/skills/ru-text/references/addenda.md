# Addenda — rules added from usage experience

The rules below were added later, from real editorial practice, and were not part of the
plugin's initial rule set. Like the rest of the plugin, they are independently formulated; the
16 sources in `sources.md` informed the work, but no rule is taken or copied from them. They are
supported by academic references. Kept separate for traceability: initial rule set vs. experiential
additions.

## Table of Contents

- [AD-1. Excessive em dashes](#ad-1-excessive-em-dashes-избыточные-тире)
- [AD-2. Excessive parcellation](#ad-2-excessive-parcellation-избыточная-парцелляция)
- [AD-3. Patronizing explanation](#ad-3-patronizing-explanation-разжёвывание-очевидного)
- [AD-4. Unprovoked rebuttal](#ad-4-unprovoked-rebuttal-возражение-без-предпосылок)
- [AD-5. Subject-predicate semantic mismatch](#ad-5-subject-predicate-semantic-mismatch-семантическое-несоответствие-субъекта-и-предиката)
- [AD-6. Manufactured antithesis](#ad-6-manufactured-antithesis-ложная-антитеза)
- [AD-7. Preemptive virtue qualifier](#ad-7-preemptive-virtue-qualifier-непрошенная-оговорка-без-воды)
- [AD-8. Assistant-register meta-commentary](#ad-8-assistant-register-meta-commentary-сервисные-реплики-ассистента)
- [AD-9. Hollow opener](#ad-9-hollow-opener-пустой-зачин)
- [Neuroslop index](#neuroslop-index)

## Neuroslop index

A compact catalogue of the recurring tells of AI-generated Russian prose, each routed to the rule
that is its canonical home. These tells skew by training era and instruction-tuning style rather
than by any single vendor; a breakdown by specific model family is intentionally omitted as
unverifiable and fast-dating.

| Tell | Canonical home |
|---|---|
| Manufactured antithesis — «не X, а Y» / «не просто X, а Y» with no antecedent | AD-6 |
| Preemptive virtue qualifier — «без воды», «чётко, по делу», «коротко и ясно» | AD-7 |
| Assistant-register meta-commentary — «Отличный вопрос!», «Надеюсь, это помогло» | AD-8 |
| Hollow opener — «давайте разберёмся», «погрузимся», «важно понимать, что» | AD-9 |
| Excessive em dashes — staccato dash rhythm | AD-1 |
| Throat-clearing stop-words — «стоит отметить, что», «нельзя не отметить» | `info-style.md` §B |
| Empty universal preamble — «в современном мире», «не секрет, что» | `info-style.md` §B |
| Unproven-claim adjectives — «качественный», «надёжный», «эффективный» | `info-style.md` §B |
| Generic conclusion — «таким образом, подводя итог» | `anti-patterns.md` |
| Artificial liveliness — exclamation stacks and emoji as a substitute for detail | `info-style.md` §F |

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

**Replacement strategies:**

| Pattern with dash | Alternative | When to use alternative |
|---|---|---|
| Москва — столица России | Москва, столица России, … | Appositive, not emphasis |
| Это — важно | Это важно | No emphasis needed, conversational |
| Он пришёл — и замолчал | Он пришёл и замолчал | No dramatic pause needed |
| Результат — рост продаж | Результат: рост продаж | Explanation follows |
| Всё готово — можно начинать | Всё готово; можно начинать | Two independent clauses |
| Скилл — набор правил — помогает | Скилл (набор правил) помогает | Aside, not emphasis |

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
- «и без всякой магии» / «без всяких фокусов» / «без нервов» appended to a claim about one's own product or method
- «чётко, по делу» / «коротко и ясно» / «простыми словами» / «разложу по полочкам» / «на пальцах» — a positive-form flourish praising the author's own delivery (the polarity twin of «без воды»)
- a self-praise tricolon about one's own product or method — «быстро, качественно, надёжно» — where each adjective is itself an unproven claim (cf. `info-style.md` §B) and the rule-of-three stacking is the added tell
- a virtue adverb stacked on a self-statement where deleting it loses no fact

**Rules:**

AD-7.1. Flag a «без [vice]» or «[virtue] говоря» qualifier when it (1) characterises the author's own delivery or method, (2) denies a fault the text never raised, and (3) carries no information — deleting it loses no fact.

AD-7.2. Rewrite by deleting the qualifier and letting the statement stand; the virtue is demonstrated by the writing. «Соберу мысль, без виляния» → «Соберу мысль».

AD-7.3. Allow informative «без»: «кофе без сахара», «работает без интернета», «ноль vi.*-моков, без заглушек», «без регистрации» — here «без» names a real removed ingredient, dependency, or feature, not a manner.

AD-7.4. Allow a genuine epistemic qualifier that carries information: «строго говоря, это аппроксимация», «по сути» when it narrows the claim (cf. AD-6.4). These calibrate meaning; they do not advertise sincerity.

AD-7.5 (register). Conversational and literary registers: «честно говоря», «прямо скажем», «по правде сказать» as natural discourse markers of live speech or a character's voice — not a statement about the author's own product or method — are not flagged. The target is the *self-promotional* manner-flourish (AD-7.1, condition 1), not ordinary spoken connective tissue. When in doubt, apply AD-7.1: if the qualifier praises the author's own delivery, flag it; if it merely colours conversational tone, leave it (cf. AD-2.3, which likewise spares the literary register).

AD-7.6. Single-count with neighbours. A «без [vice]» flourish can also be caught by AD-2 (parcellation / filler rhythm in Structure) — the «без воды» tail in «Расскажу последовательно, доступно, без воды» is one fragment, not two faults. Count one violation per fragment: charge it to AD-7 (**Ч — Clarity**) when the defect is the empty self-virtue, to AD-2 (**С — Structure**) when the defect is the staccato or filler rhythm. Never double-charge the same fragment across Ч and С.

AD-7.7. Positive-form delivery self-praise is flagged on the same AD-7.1 test: it (1) characterises the author's own delivery or method, (2) names a virtue the writing should simply demonstrate, and (3) carries no fact — deleting it loses nothing. «Объясню чётко, по делу» → «Объясню» (then actually do). Do NOT flag a qualifier that previews concrete content that immediately follows: «Объясню коротко: значение лежит в стеке» carries information about what comes next and stays. An established genre or rubric label — a column or book title «… на пальцах», «… простыми словами» — is a recognised popular-science convention, not a delivery flourish, and is not flagged.

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
