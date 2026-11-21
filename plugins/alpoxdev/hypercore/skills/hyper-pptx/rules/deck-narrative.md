# Deck Narrative

Use this rule file before writing any spec. It owns what goes on a slide, in what order, and what gets cut.

## 1. One Slide, One Claim

A slide carries one sentence the audience should remember. If you cannot say it in one sentence, the slide holds two claims and becomes two slides.

- The claim goes in `title` as a full sentence or a noun phrase with a verb of judgement ("결제 실패는 3개 구간에서 발생한다"), never a topic label ("결제 현황").
- Body content is evidence for the title, not a second argument. A bullet that does not support the title is deleted, not moved.
- A slide with a table, chart, or image and three bullets is two slides.

## 2. The Order That Works

| Position | Slide kind | Job |
|---|---|---|
| 1 | `title` | what this is, for whom, as of when |
| 2 | `bullets` or `stats` | the answer, in the first 30 seconds |
| 3-6 | one kind per claim | evidence, each slide answering one question |
| second to last | `section` or `bullets` | what changes next |
| last | `quote` or `bullets` | the single line to remember |

Put the conclusion second, not last. A deck that saves the answer for the end is read as a mystery, and decision makers leave before the reveal.

`section` slides mark chapters in a deck longer than eight slides. Below that, they cost a slide and buy nothing.

## 3. Kind Selection

| The reader must | Use | Avoid |
|---|---|---|
| follow an argument | `bullets` | paragraphs of 3+ lines |
| compare parallel options | `columns` | a table with one row per option |
| feel the size of a number | `stats` | the number buried in a bullet |
| check exact values | `table` | a chart of five values |
| see a trend or a gap | `chart` | a table of twenty rows |
| see a real thing | `image` | a description of the thing |
| remember one sentence | `quote` | the sentence as a bullet |

A chart is for shape, a table is for values. Above about six categories, a table or a split into two charts beats a crowded axis.

## 4. Words

- Say the number and its unit: `47%`, `12만 건`, `3주`. A percentage without a base ("47% 증가") is not a fact.
- Name the actor: "카드 인증에서 47%가 끊긴다", not "47%의 이탈이 발생한다".
- Delete intensifiers. "매우", "상당히", "혁신적인", "다양한" carry no information and read as filler.
- Keep one term per concept across the deck. Switching between "실패율" and "에러율" for the same measure makes the reader doubt both.
- Speaker notes carry the reasoning and the sources; the slide carries the claim. Do not put a source line on a slide when `notes` can hold it.

## 5. Size Budget

| Element | Limit |
|---|---|
| `bullets` | 4 at level 0, or 3 with 2 sub-lines each |
| bullet text | one line at 18 points in the text column, about 34 Korean characters |
| `columns` | 3, each with a heading and 2-3 short bullets |
| `stats` | 4, each a value under 6 characters plus a label |
| `table` | 6 columns, 8 rows |
| `chart` | 6 categories, 3 series |
| `title` | one line at 30 points, about 20 Korean characters |
| `quote` | one sentence, under about 60 characters |

Over a limit, split the slide. Shrinking type to fit is how a deck becomes unreadable from the third row of a room.

## 6. What To Cut

- Agenda slides, "thank you" slides, and a table of contents the audience can see in the file name.
- A slide that repeats the previous slide in different words.
- Decoration with no meaning: a stock photo of a handshake, an icon row that labels nothing.
- Any bullet that starts with "또한" or "추가로": it is a second claim wearing a connector.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| One message per slide and the conclusion-early order | <https://www.duarte.com/resources/books/slideology/> |
| Chart for shape, table for values | <https://www.edwardtufte.com/tufte/books_vdqi> |
| Text alternative and readable description for a complex visual | <https://www.w3.org/WAI/tutorials/images/complex/> |
| Speaker notes carry reasoning, slide carries the claim | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-notes-slides> |

### Evidence grade

`LOCAL` — the limits in §5 were calibrated against the geometry in `assets/runtime/layout.jq` and checked by rendering decks at each limit on 2026-11-13; the narrative rules are this package's editorial position.
