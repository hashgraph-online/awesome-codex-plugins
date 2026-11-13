# The Markdown dialect

The pipeline reads a fixed subset of Markdown. Anything outside it is rendered as plain text rather than dropped, so an unsupported construct shows up in the output as literal characters and is easy to spot.

## Contents

- [1. Supported blocks](#1-supported-blocks)
- [2. Directives](#2-directives)
- [3. Inline formatting](#3-inline-formatting)
- [4. The source file](#4-the-source-file)
- [5. What silently surprises authors](#5-what-silently-surprises-authors)
- [6. A worked example](#6-a-worked-example)
- [7. Sources](#sources)

## 1. Supported blocks

| Construct | Syntax | Renders as |
|---|---|---|
| Heading | `#`, `##`, `###`, `####` | `h1`–`h4`; `h1` and `h2` also enter the table of contents |
| Paragraph | a blank-line-separated run of text | `p` |
| Bullet list | `- item`, nested with two-space indent | `ul` with nested `ul` |
| Ordered list | `1. item` | `ol` |
| Blockquote | `> text` | `blockquote` |
| Fenced code | triple backticks with an optional language | `pre > code` |
| Table | GFM pipe table with a `---|---` separator row | `table` with `thead` and `tbody` |
| Thematic break | `---` on its own line | `hr` |
| Image | `!` + `[caption]` + `(path.png)` alone on its line | `figure` with `figcaption` |
| Inline image | `!` + `[alt]` + `(path.png)` inside a sentence | `img` |
| Table of contents | `[TOC]` alone on its line | `nav` filled after pagination |
| Raw HTML | a line starting with `<` | passed through untouched |

## 2. Directives

Three colon directives cover what Markdown cannot express.

```
:::kpi
매출 성장 | +32%
이탈률 | 4.1%
:::
```

Renders one row of large key figures. Label on the left of the pipe, value on the right. Three or four is the useful maximum; more than four stops being at-a-glance.

```
:::callout 결정
A안을 8주 안에 착수한다.
:::
```

Renders a bordered aside with the label as its heading. Use it for the decision, the risk, or the condition — not for ordinary emphasis.

```
:::pagebreak
:::
```

Forces the next block onto a new page. Use it before an appendix, never inside flowing body text.

## 3. Inline formatting

| Syntax | Renders as | Note |
|---|---|---|
| `**bold**` | `strong` | Needs a non-space right after the opening `**` |
| `*italic*` | `em` | Single asterisks only |
| `` `code` `` | `code` | Backtick content is protected from every other rule |
| `[text]` + `(url)` | `a` | Opens with the URL as written |
| `!` + `[alt]` + `(path)` | `img` | Path is relative to the output directory |
| `[S1]` | citation marker | Rendered as a superscript span |

**Underscore emphasis is deliberately unsupported.** `snake_case_name` and `__init__` render as written, because identifiers in technical reports are far more common than underscore italics, and silently italicising half an identifier is a bug the reader cannot see.

## 4. The source file

The file starts with a frontmatter block. Every key is optional except that a report without a title falls back to the file name.

```markdown
---
title: "시장 진입 분석 보고서"
subtitle: "2026년 4분기 후보 3안 비교"
author: "양민열"
date: "2026-11-13"
theme: "editorial"
footer: "시장 진입 분석 — 내부 검토용"
---

# 결론

A안을 8주 범위로 승인하는 것을 권한다. …
```

| Key | Used for |
|---|---|
| `title` | Cover heading, document title, default footer |
| `subtitle` | Cover second line |
| `author` | Cover metadata |
| `date` | Cover metadata |
| `theme` | Default theme, overridable by the command |
| `footer` | Left side of every page footer |

The cover is not automatic: write an HTML block at the top of the body if you want the full cover treatment. A plain `# title` first heading is a perfectly good report opener for short documents.

## 5. What silently surprises authors

- A blank line between list items starts a new list. Keep list items contiguous.
- A table needs its separator row; a pipe-heavy paragraph is not a table.
- An image on its own line with text after it is not a figure; the caption is the alt text, and the alt text must be there.
- Two spaces of indent nest a list; four spaces do not create a code block.
- A heading is never the last block on a page: the paginator pulls it forward. If a heading must end a page, follow it with an explicit `:::pagebreak` after the content that belongs with it.
- Raw HTML blocks must start at column zero and run to a blank line.

## 6. A worked example

```markdown
---
title: "온보딩 이탈 분석"
audience: "프로덕트 리드"
---

# 결론

온보딩 3단계를 줄이면 4주 안에 이탈률을 4.1%에서 3% 아래로 낮출 수 있다 [S1]. 비용은 디자인 2주다.

:::kpi
현재 이탈률 | 4.1%
목표 | 3.0% 미만
예상 기간 | 4주
:::

## 근거

3단계에서의 이탈이 전체의 절반을 차지한다 [S2].

| 구간 | 진입 | 이탈 | 이탈률 |
|---|---:|---:|---:|
| 1단계 | 12,400 | 1,110 | 9.0% |
| 2단계 | 11,290 | 1,020 | 9.0% |
| 3단계 | 10,270 | 2,050 | 20.0% |

[TOC]

## 다음 단계

3단계를 2단계로 합치는 시안을 2주 안에 만든다 [S3].

## Source list

| Marker | Source | Retrieved |
|---|---|---|
| S1 | 내부 분석 대시보드, 온보딩 퍼널 | 2026-11-13 |
| S2 | 동일 | 2026-11-13 |
| S3 | 디자인 리드 인터뷰 | 2026-11-13 |
```

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| GFM table syntax and the separator row | <https://github.github.com/gfm/#tables-extension-> |
| Fenced code blocks and the info string | <https://github.github.com/gfm/#fenced-code-blocks> |
| Backtick spans taking precedence over other inline rules | <https://github.github.com/gfm/#code-spans-> |
| Underscore emphasis being suppressed here | This package's `assets/runtime/markdown.awk`, verified on 2026-11-13 |