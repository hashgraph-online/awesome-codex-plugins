# Korean Break Quality

Read when the product language is Korean and a headline, label, action, empty or error state, or section text is written or reviewed. This covers how Korean text breaks across lines and what breaks there. Scripting a font-size or line-height change is not in scope; that lives in `rules/craft-floor.md` §6.

## Contents

- 1. What blocks delivery
- 2. How to look

## 1. What blocks delivery

Each defect below names the break it produces. Fix the break, not the wording, before delivery.

**Orphaned particle or ending.** A particle (이, 가, 은, 는, 을, 를, 에, 서, 도, 만, 부터, 까지, 보다, 처럼, 붙은 어미) or a sentence ending is left alone on the next line, cut off from the word it closes.

| Before | After |
|---|---|
| "무료로 시작하세\n요" | "무료로 시작하세요" |
| "설정을 저장하\n고" | "설정을 저장하고" |

**Clause split from its predicate.** A modifier clause breaks away from the predicate it belongs to, leaving a line that ends on a dangling modifier.

| Before | After |
|---|---|
| "결제가 완료되\n기 전에 카드 정보를 입력해주세요" | "결제가 완료되기 전에 카드 정보를 입력해주세요" |

**Citation string broken mid-token.** A citation, version number, code-like token, number with its unit, or an embedded foreign word splits inside the token itself.

| Before | After |
|---|---|
| "연도별 보고서 v2026-\n11-09" | "연도별 보고서 v2026-11-09" |
| "잔액 1,234,567\n원" | "잔액 1,234,567원" |

**A line that ends on a bare word.** A line ends on a loanword or a noun whose particle begins the next line; the break is the orphaned-particle case above.

**Forced break of a short phrase.** A headline, button label, state message, or two- to four-syllable noun phrase wraps earlier than the container requires, for example with an explicit break or with `keep-all` removed.

| Before | After |
|---|---|
| "지금\n시작하기" | "지금 시작하기" |

Keep `word-break: keep-all` with `overflow-wrap: anywhere` (or `break-word`) for long tokens so a long token overflows rather than wrapping mid-token; widening the container beats re-breaking the phrase. `rules/craft-floor.md` §6 carries the baseline.

## 2. How to look

1. Read the rendered line, not the source. Check the same phrase at each checked width named in `rules/rendered-evidence.md`.
2. For every break, name the defect from §1, fix the largest visible one first, then re-check from the top at every width.
3. If a line looks broken but none of the §1 defects applies, report the break in words and invent no label for it.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| The blocking set (orphaned particle or ending, clause split from its predicate, broken citation string) and the before/after examples | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored in this package's own words; the source repository has no license and no text or code was copied |
| `word-break: keep-all` breaks only at spaces, and `overflow-wrap: anywhere` lets a long token overflow | <https://developer.mozilla.org/en-US/docs/Web/CSS/word-break> |
| The CSS baseline the reference builds on | `rules/craft-floor.md` §6, this package |

### Evidence grade

The examples are marked up by eye; the three defects are the rule, and the wording is this package's own. Reference comparison without a comparison tool is reported `unavailable`, never passed.
