# Scoring: text quality assessment (0–10)

Analytic rubric for evaluating Russian text quality across 5 dimensions.
Context-aware LLM evaluation based on ~1 044 rules from 16 sources.

## Table of Contents

- [Algorithm overview](#algorithm-overview)
- [Dimensions](#dimensions)
  - [T — Typography](#t--typography-weight-015)
  - [Ч — Clarity](#ч--clarity-weight-025)
  - [Г — Grammar](#г--grammar-weight-020)
  - [С — Structure](#с--structure-weight-020)
  - [Ц — Reader precision](#ц--reader-precision-weight-020)
- [Composite score](#composite-score)
- [Non-compensatory rules](#non-compensatory-rules)
- [Score interpretation](#score-interpretation)
- [Output format](#output-format)
- [Limitations](#limitations)

## Algorithm overview

### Step-by-step procedure

1. **Input.** Russian text of any length.
2. **Domain routing.** Determine text domain (article, UI, business email, general) to load domain-specific rules into the Reader Precision dimension.
3. **Dimension-by-dimension evaluation.** Score each of the 5 dimensions independently using the rubric anchors below. For each dimension, record 1–3 specific issues with the problematic text fragment quoted.
4. **Non-compensatory check.** Apply floor caps if any dimension falls below threshold.
5. **Composite score.** Weighted average of 5 dimensions, rounded to one decimal place.
6. **Diagnostic output.** Total + 5 dimensions + verbal label + specific issues per dimension. Every deducted point is explained.

### Why context-aware evaluation

Formula-based tools (Glavred, Turgenev, Advego) count surface features: stop-words, sentence length, keyword density. Removing «очень» raises the score without improving the text. An SEO text scored 9.1 on Glavred without any real quality.

This rubric evaluates text contextually against ~1 044 rules. «Очень» in quoted direct speech is not penalized. «Инновационный» without evidence is penalized. Five orthogonal dimensions cannot be optimized simultaneously without genuinely improving the text.

The only way to raise the score is to write better.

### Research basis

- Readability formulas are unreliable: different formulas diverge by 2–3 grade levels on the same text (Zhou, Jeong, Green 2017). Texts revised for formula scores showed worse reader comprehension (Duffy & Kabance; Olsen & Johnson). 7 reasons to avoid readability formulas (UXmatters 2019).
- LLM-Rubric (ACL 2024): RMSE < 0.5; inter-rater reliability for Structure exceeded human judges (QWK 0.584 vs 0.541).
- Hybrid penalty + bonus + non-compensatory floors: best architecture per analysis of sports judging (gymnastics, figure skating) and academic essay scoring systems.
- Goodhart's Law: «when a measure becomes a target, it ceases to be a good measure.» Five orthogonal dimensions are the primary defense.

---

## Dimensions

### T — Typography (weight 0.15)

Type: hard (objective). Rule source: [typography.md](typography.md) (96 rules).

| Score | Criteria |
|---|---|
| 9–10 | Guillemets for quotes, correct dash types (em/en/hyphen), NBSP after prepositions, special characters (№, ©, °, ×) correct, numbers formatted |
| 7–8 | 1–2 minor issues: missing NBSP, one wrong dash type. Overall picture correct |
| 5–6 | Several systematic errors: mixed dashes and hyphens, some straight quotes |
| 3–4 | Pervasive errors: straight quotes throughout, hyphens instead of dashes, three dots instead of ellipsis glyph |
| 1–2 | No typographic formatting at all: plain ASCII characters |

### Ч — Clarity (weight 0.25)

Type: soft (expert). Rule sources: [info-style.md](info-style.md) (197 rules), [anti-patterns.md](anti-patterns.md) (138 rules). Secondary signals (low weight): [addenda.md](addenda.md) AD-3 (patronizing explanation), AD-5 (subject-predicate mismatch, with technical-context exception).

| Score | Criteria |
|---|---|
| 9–10 | No stop-words, no bureaucratic language, no clichés. Active voice. Every word works. No false intensifiers or unsubstantiated claims |
| 7–8 | 1–3 minor stop-words or passive constructions. Overall tone is clean |
| 5–6 | Noticeable stop-words (5+), several passive constructions, 1–2 clichés. Readable but loose |
| 3–4 | Bureaucratic language dominates: deverbal nouns, genitive chains, split predicates |
| 1–2 | Bureaucratic soup: «осуществление мероприятий по обеспечению надлежащего функционирования» |

### Г — Grammar (weight 0.20)

Type: hard (objective). Rule sources: [editorial-grammar.md](editorial-grammar.md) (171 rules), [editorial-punctuation.md](editorial-punctuation.md) (88 rules).

| Score | Criteria |
|---|---|
| 9–10 | Punctuation flawless, agreement correct, no tautology or pleonasm, capitalization per rules |
| 7–8 | 1–2 minor punctuation errors (missing comma with introductory word). Grammar correct |
| 5–6 | Several punctuation errors, 1–2 agreement errors or tautology |
| 3–4 | Systematic punctuation errors, agreement violations, pleonasms |
| 1–2 | Grammatically illiterate: errors in every sentence |

### С — Structure (weight 0.20)

Type: soft (expert). Rule sources: [info-style.md](info-style.md) (structure section), [addenda.md](addenda.md) — AD-1 (dash overuse), plus secondary signals (low weight): AD-2 (excessive parcellation), AD-4 (unprovoked rebuttal).

| Score | Criteria |
|---|---|
| 9–10 | Inverted pyramid (main point first). One paragraph = one idea. Logical transitions. Headings where needed. No monotonous dash rhythm |
| 7–8 | Logical structure, but 1–2 overloaded paragraphs or implicit transitions |
| 5–6 | Structure is guessable but ideas are mixed, uneven paragraphs |
| 3–4 | No structure: stream of consciousness without paragraph breaks |
| 1–2 | Chaotic exposition, impossible to identify the main point |

### Ц — Reader precision (weight 0.20)

Type: soft (expert). Rule sources: [info-style.md](info-style.md) (facts/evidence section), domain-specific file when applicable.

Domain routing for this dimension:

| Text type | Additional rules from |
|---|---|
| UI text, buttons, errors, microcopy | [ux-writing.md](ux-writing.md) |
| Email, messenger, business | [business-writing.md](business-writing.md) |
| General / article / documentation | info-style.md only |

| Score | Criteria |
|---|---|
| 9–10 | Concrete facts and numbers. Clear reader benefit. Examples and evidence. No empty declarations. Actionable for the reader |
| 7–8 | Mostly concrete, but 1–2 claims without evidence or abstract phrases |
| 5–6 | Mix of concrete and abstract. Some claims are unsubstantiated. Reader benefit unclear |
| 3–4 | Declarations and promises dominate over facts. Text says nothing |
| 1–2 | Fully abstract: «Мы предлагаем комплексные решения для вашего бизнеса» |

---

## Composite score

```
S = round₁(T × 0.15 + Ч × 0.25 + Г × 0.20 + С × 0.20 + Ц × 0.20)
```

Where `round₁` = round to one decimal place.

Total weight: 0.15 + 0.25 + 0.20 + 0.20 + 0.20 = 1.00.

## Non-compensatory rules

These caps prevent high scores in other dimensions from masking critical weaknesses.

| Condition | Cap | Reason |
|---|---|---|
| Any dimension < 3.0 | Total ≤ 5.0 | Critical weakness is not compensable |
| Typography < 4.0 | Total ≤ 7.0 | Basic typography is mandatory |
| Grammar < 4.0 | Total ≤ 7.0 | Basic grammar is mandatory |

Apply the most restrictive cap when multiple conditions trigger.

## Score interpretation

| Score | Label (RU) | Label (EN) | Meaning |
|---|---|---|---|
| 9.0–10.0 | Эталонный | Benchmark | Ready to publish. Rare result — a reference point, not a target |
| 7.0–8.9 | Хороший | Good | Minor improvements needed. Target range for working texts |
| 5.0–6.9 | Средний | Average | Noticeable issues, editing needed |
| 3.0–4.9 | Слабый | Weak | Significant issues, rewriting needed |
| 0.0–2.9 | Критический | Critical | Full rewrite required |

A score of 8+ is a strong result. 10.0 is a theoretical ideal, not a practical target.

## Output format

```
## Оценка: X.X / 10 — [Label]

| Измерение | Балл | Замечания |
|---|---|---|
| Типографика | X.X | [1–3 specific issues with quoted fragments] |
| Чистота языка | X.X | [1–3 specific issues] |
| Грамотность | X.X | [1–3 specific issues] |
| Структура | X.X | [1–3 specific issues] |
| Точность для читателя | X.X | [1–3 specific issues] |

**Формула:** T×0.15 + Ч×0.25 + Г×0.20 + С×0.20 + Ц×0.20 = X.X
[Non-compensatory cap note, if triggered]

### Что оценка не измеряет
[Limitations list]
```

For texts under 50 words, prepend: «Текст короткий — оценка менее надёжна. Для точной оценки рекомендуется текст от 50 слов.»

## Limitations

The score does NOT measure:

- **Factual accuracy** — numbers and dates may be false but beautifully formatted
- **Audience tone fit** — appropriateness for the specific target audience
- **Creativity and voice** — authorial style and originality
- **Effectiveness** — conversion, engagement, persuasion outcomes
- **Brief compliance** — whether the text meets the client's assignment

These limitations are stated explicitly in every scoring output to prevent overreliance on the score (Goodhart's Law defense).
