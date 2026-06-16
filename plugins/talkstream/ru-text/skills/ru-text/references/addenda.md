# Addenda — rules added from usage experience

Rules below were NOT part of the initial distillation from 16 canonical sources.
They emerged from real editorial practice and are supported by academic references.
Kept separate for traceability: original corpus vs. experiential additions.

---

## AD-1. Excessive em dashes (избыточные тире)

**Problem:** multiple em dashes in a paragraph create choppy rhythm, monotony, and an affected (mannered) tone.

**Sources:**
- Chekhov: «Поменьше употребляйте курсивов и тире — это манерно»
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
- Rhetorical concept of «ритор и оппонент, реальный или фиктивный»: HSE «Риторика» (nnov.hse.ru)

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
| Машина решает задачу за 3 секунды. | Established technical usage (БРЭ «Антропоморфизм»: «в технической литературе антропоморфное употребление понятий основано на объективном сходстве»). |
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
- «не про X, а про Y» / «дело не в X, а в Y» — the topic swapped through a phantom rejected topic
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

**Examples:**

| Wrong | Correct |
|---|---|
| Это не баг, а фича. | Так и задумано. |
| Это не про скорость, а про надёжность. | Это про надёжность. |
| ИИ — это не инструмент. Это образ мышления. | ИИ меняет то, как я думаю о задаче. |
| Дело не в модели, а в промпте. | Всё решает промпт. |
| Не медленно, а быстро. | Отвечает за 200 мс. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Хочу и буду. Вернее, буду, когда хочу. | Asymmetric self-correction: X is present, the second clause narrows it. |
| Это не неуверенность — это точность мышления вслух. | The negated pole is a real reader misreading the context invites (antecedent satisfied). |
| Выросло не на 2%, а на 40%. | Both poles carry data; deletion loses information. |
| Не мытьём, так катаньем. | Fixed idiom. |
| Не оферта, а приглашение делать оферты. | Legal formula where the binary is operative semantics. |

**Severity:** Medium — the manufactured antithesis is the single strongest machine-generation tell in this addenda set, and density compounds fast. Primary signal in the **С — Structure** dimension (supporting **Ч — Clarity**), reflected in the С rubric anchors. A cluster of manufactured pairs materially lowers the С score; a single antecedent-backed pair does not. Still cannot, by itself, trigger a non-compensatory cap — that stays reserved for the hard dimensions and the global < 3.0 floor.

**Acknowledged:** identified from corpus analysis of AI-generated Russian prose (2026-06); the contrastive-negation antithesis runs at high density in machine drafts and near-zero in human reference corpora.


---

## AD-7. Preemptive virtue qualifier (непрошенная оговорка «без воды»)

**Problem:** a trailing manner-flourish that asserts the author's virtue by denying a fault the reader never raised — «без воды», «без виляния», «без лишних слов», «начистоту», «честно говоря», «прямо скажем», «не побоюсь этого слова», «и без всякой магии». The statement reassures the reader against a vice nobody suspected, so the qualifier carries no information and only performs sincerity. It is a cousin of AD-4: where AD-4 rebuts an unvoiced external claim, AD-7 denies an unvoiced fault of the author's own delivery. Virtue is shown by the writing, never announced.

**Sources:**
- Telling vs. showing, and self-praise as an empty signal: editorial practice, informed by Нора Галь «Слово живое и мёртвое» on needless self-qualification
- Adjacent to AD-4 (unprovoked rebuttal) and AD-3 (patronizing explanation)
- Independently formulated from corpus analysis of AI-generated Russian prose

**Trigger constructions:**

- «без воды» / «без виляния» / «без лишних слов» / «без обиняков» — a manner-flourish denying a vice of delivery
- «честно говоря» / «начистоту» / «прямо скажем» / «не побоюсь этого слова» — announced sincerity
- «и без всякой магии» / «без всяких фокусов» / «без нервов» appended to a claim about one's own product or method
- a virtue adverb stacked on a self-statement where deleting it loses no fact

**Rules:**

AD-7.1. Flag a «без [vice]» or «[virtue] говоря» qualifier when it (1) characterises the author's own delivery or method, (2) denies a fault the text never raised, and (3) carries no information — deleting it loses no fact.

AD-7.2. Rewrite by deleting the qualifier and letting the statement stand; the virtue is demonstrated by the writing. «Соберу мысль, без виляния» → «Соберу мысль».

AD-7.3. Allow informative «без»: «кофе без сахара», «работает без интернета», «ноль vi.*-моков, без заглушек», «без регистрации» — here «без» names a real removed ingredient, dependency, or feature, not a manner.

AD-7.4. Allow a genuine epistemic qualifier that carries information: «строго говоря, это аппроксимация», «по сути» when it narrows the claim (cf. AD-6.4). These calibrate meaning; they do not advertise sincerity.

AD-7.5 (register). Conversational and literary registers: «честно говоря», «прямо скажем», «по правде сказать» as natural discourse markers of live speech or a character's voice — not a statement about the author's own product or method — are not flagged. The target is the *self-promotional* manner-flourish (AD-7.1, condition 1), not ordinary spoken connective tissue. When in doubt, apply AD-7.1: if the qualifier praises the author's own delivery, flag it; if it merely colours conversational tone, leave it (cf. AD-2.3, which likewise spares the literary register).

AD-7.6. Single-count with neighbours. A «без [vice]» flourish can also be caught by AD-2 (parcellation / filler rhythm in Structure) — the «без воды» tail in «Расскажу последовательно, доступно, без воды» is one fragment, not two faults. Count one violation per fragment: charge it to AD-7 (**Ч — Clarity**) when the defect is the empty self-virtue, to AD-2 (**С — Structure**) when the defect is the staccato or filler rhythm. Never double-charge the same fragment across Ч and С.

**Examples:**

| Wrong | Correct |
|---|---|
| Соберу мысль, без виляния. | Соберу мысль. |
| Отвечу честно, без воды: дедлайн сорван. | Дедлайн сорван. |
| Скажу прямо, без обиняков: тест не проходит. | Тест не проходит. |
| Это работает, и без всякой магии. | Это работает. |
| Max 20× закрывает запрос начисто, без нервов. | Max 20× закрывает запрос. |

**Counter-examples (do NOT flag):**

| Acceptable | Reason |
|---|---|
| Кофе без сахара. | «без» names a real removed ingredient. |
| Ноль vi.*-моков — без заглушек. | «без» names a real removed thing. |
| Сервис работает без интернета. | «без» names a real capability. |
| Строго говоря, это аппроксимация. | Epistemic qualifier carrying real information. |

**Severity:** Low. Secondary signal in the **Ч — Clarity** dimension (supporting **С — Structure**). Cannot trigger non-compensatory caps alone.

**Acknowledged:** identified from corpus analysis of AI-generated Russian prose (2026-06); the «без [vice]» self-virtue flourish recurs in machine drafts and reads as announced rather than demonstrated quality.
