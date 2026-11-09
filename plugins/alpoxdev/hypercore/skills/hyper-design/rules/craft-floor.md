# Craft Floor

Read before building and before judging any finding against a number. This file owns the numeric floor every designed, restyled, or mocked-up screen meets. `MUST` rows are conformance requirements and fail the run. `DEFAULT` rows are the starting value when the project, the brief, or the platform says nothing; a documented project value replaces them.

## 1. Contrast and Color

| Rule | Value | Level |
|---|---|---|
| Body text against its background | at least 4.5:1, computed without rounding (`references/contrast-check.md`); never asserted for a gray pair without computing it | MUST (WCAG 2.2 AA) |
| Large text (about 24px, or about 18.5px bold) | at least 3:1 | MUST |
| Icons, control boundaries, state indicators, chart marks needed to understand content | at least 3:1 against adjacent colors | MUST |
| Text over an image or video | a solid or gradient scrim so the worst-case pixel pair still passes 4.5:1 | MUST |
| Muted and placeholder text | still 4.5:1; hierarchy comes from size and weight, not from gray below the floor | MUST |
| Both color schemes | every pair passes in light and dark when both ship | MUST |
| Accent share | one accent hue; accent fills stay a small share of a screen (KRDS: at most 5%) | DEFAULT |
| Neutral tint | tint neutrals toward the brand hue instead of pure gray when the brand allows | DEFAULT |
| Palette size | two or three core colors plus one accent; neutrals do not count; more only with a documented system | DEFAULT |

WCAG 3 is a Working Draft and APCA is not normative anywhere; keep WCAG 2.2 AA as the contrast baseline.

## 2. Targets and Focus

| Rule | Value | Level |
|---|---|---|
| Pointer target (web) | at least 24×24 CSS px, or the WCAG spacing exception | MUST |
| Touch target | 44×44 CSS px or pt on touch surfaces; Android 48×48 dp | DEFAULT (WCAG AAA, Apple default, Android guidance) |
| Apple control minimum | 28×28 pt is the stated minimum; 44×44 pt is the default to aim for | platform |
| Focus visible | every keyboard-operable control shows a focus indicator; never `outline: none` without a replacement | MUST |
| Focus indicator contrast | at least 3:1 against the adjacent background | MUST |
| Focus not obscured | sticky headers, footers, and non-modal panels never fully cover the focused control (`scroll-padding`) | MUST |
| Focus style | keep the user agent ring or the project's documented ring; a custom ring is at least 2px | DEFAULT |
| Affordance | every enabled control is a native element (`button` for actions, `a href` for navigation), shows `cursor: pointer` from one base rule, has an accessible name, and has distinct hover, active, and disabled states that do not rely on color alone (`references/accessible-interaction.md`) | MUST (name, role, color alone) / DEFAULT (cursor) |
| Zoom | the viewport meta never sets `user-scalable=no` or `maximum-scale=1` | MUST |
| Touch spacing | adjacent touch targets keep a clear gap so a thumb press cannot hit both | DEFAULT |

Browser-drawn surfaces (set each from tokens where the surface exists; never leave the platform default unexamined):

| Rule | Value | Level |
|---|---|---|
| Selection | `::selection` foreground and background from tokens, never the default blue | DEFAULT |
| Caret | `caret-color` matching text color or a token color on editable surfaces | DEFAULT |
| Scrollbars | `scrollbar-color` where scrolling exists, including overflow panels | DEFAULT |
| Focus ring | at least 2px with a visible offset from the control edge | DEFAULT |
| Underline offset | `text-underline-offset` so the underline clears descenders | DEFAULT |
| Figures | `tabular-nums` in tables, prices, and counters (the same rule as section 3) | DEFAULT |

## 3. Type

| Rule | Value | Level |
|---|---|---|
| Web body size | 16px minimum; 16-18px typical (Korean body: §6) | DEFAULT |
| Smallest UI text | 12px; 11pt on iOS, 10pt on macOS are platform minimums, not defaults | DEFAULT |
| Line length | 45-75 characters for running text; never full-width paragraphs on wide screens | DEFAULT |
| Line height, Latin body | 1.4-1.6; headings 1.1-1.3 | DEFAULT |
| Type steps | adjacent sizes differ by at least 1.25x | DEFAULT |
| Display size | display text at most 6rem | DEFAULT |
| Display tracking | display tracking not below -0.04em | DEFAULT |
| Text-spacing tolerance | layout survives user overrides of line height 1.5, paragraph spacing 2em, letter spacing 0.12em, word spacing 0.16em | MUST |
| Resize | text resizes to 200% without loss of content | MUST |
| Families | one family, or two with fixed jobs (display, text); never three | DEFAULT |
| Weights | body 400-500; avoid ultralight and thin for UI text | DEFAULT |
| Heading levels | at most three visible levels in one view; no skipped semantic levels | DEFAULT |
| Headings | sentence case; no all-caps body or headings; tracking only on display sizes (slightly negative) and small labels (slightly positive) | DEFAULT |
| Numbers | tabular figures in tables, prices, and counters | DEFAULT |
| Font supply | every declared face is loaded by the project (`@font-face`, a package, or a system stack); never a face the build does not ship | MUST |

## 4. Space, Layout, Shape, Depth

| Rule | Value | Level |
|---|---|---|
| Space scale | one 4px-based scale (4, 8, 12, 16, 24, 32, 48, 64, 96) or the project's own; no one-off values | DEFAULT |
| Grouping | space inside a group is smaller than space between groups; more space above a heading than below it | DEFAULT |
| Heading space | space above a heading at least 1.5x the space below it | DEFAULT |
| Group space | the gap between groups at least 2x the gap inside a group | DEFAULT |
| Body measure | body text 65-75ch; display text at most 6rem | DEFAULT |
| Reflow | no two-dimensional scrolling at 320 CSS px width, except tables, maps, and editors | MUST |
| Check widths | the project's breakpoints, otherwise 375, 768, and 1280 (Korean public-sector: 360, 768, 1024, 1280) | DEFAULT |
| Content width | a maximum content width (about 1200-1280px) with one consistent gutter | DEFAULT |
| Radius | a scale tied to element size (for example 4 / 8 / 12 / 16 and full); nested radius = outer minus padding | DEFAULT |
| Depth | a few elevation steps; a layered shadow (ambient plus direct) or a border, not both at full strength on every card | DEFAULT |
| Containers | a card only when the content is a separable object; never a card inside a card for decoration | DEFAULT |
| Responsive states | as many layout states as the content needs (usually single column, two columns, full grid), with breakpoints placed where the content breaks, not at device widths; the middle band (about 600-1024px) is designed, not inherited (`references/responsive-reflow.md`) | DEFAULT |
| Full-height sections | size to content; use `dvh` (never `100vh`) only when a section must fill the screen | DEFAULT |
| Fixed chrome | sticky headers and bottom bars stay compact, reserve their height in the page, and respect safe-area insets | DEFAULT |
| Dose caps | glass or backdrop blur on at most one or two elements; glow on at most one or two focus elements; shadows only where an element lifts | DEFAULT |

## 5. Motion

| Rule | Value | Level |
|---|---|---|
| Reduced motion | honor `prefers-reduced-motion: reduce`: replace movement with fades or nothing; no parallax | MUST |
| Interaction feedback | 100-200 ms | DEFAULT |
| State and overlay transitions | 150-300 ms; one authored focal entrance may take up to about 500 ms | DEFAULT |
| Easing | ease-out family for entrances (for example `cubic-bezier(0.2, 0, 0, 1)`); no ease-in on entrances; no bounce or elastic by reflex | DEFAULT |
| Properties | animate `transform` and `opacity`; never `transition: all`; never layout properties | DEFAULT |
| Entrances | never from `scale(0)` (start near 0.95 with opacity); one entrance per container; stagger 30-80 ms with the group under about 300 ms | DEFAULT |
| Frequency | actions repeated many times a session get no animation; keyboard-triggered actions do not animate | DEFAULT |
| Autoplay | moving content longer than 5 seconds has a pause control | MUST |

## 6. Korean Text

| Rule | Value | Level |
|---|---|---|
| Line breaking | `word-break: keep-all` with `overflow-wrap: anywhere` (or `break-word`) for long tokens | DEFAULT |
| Body size | 16px minimum; 17px is the KRDS default with Pretendard GOV | DEFAULT |
| Line height | at least 150% for body; 160-170% is a reasonable choice for long reading | DEFAULT |
| Tracking | 0 on Hangul body and labels; never positive tracking for "style" | DEFAULT |
| Font stack | the project's font, or an OFL Hangul family such as Pretendard (keep the reserved name rules) with `"Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif` fallbacks | DEFAULT |
| Weights | regular and bold are enough; avoid thin Hangul weights in UI | DEFAULT |

## 7. States, Feedback, Forms, Copy

| Rule | Value | Level |
|---|---|---|
| Feedback timing | under 0.1 s feels instant; under 1 s keeps flow; over 10 s needs progress and a way out | DEFAULT |
| Loading | none under about 1 s; skeleton (page) or spinner (module) for 2-10 s; a skeleton mirrors the final layout; progress over 10 s | DEFAULT |
| Empty state | never blank: status, what fills it, and one direct action | DEFAULT |
| Error message | next to the source, plain language, no blame words, a fix, input preserved, more than color alone | MUST (color alone) / DEFAULT |
| Error summary | multi-field forms show a summary that receives focus and links to each field, worded like the inline messages | DEFAULT |
| Forms | one column; visible labels above fields; placeholder is never the label; mark optional fields; no reset button; never asterisk-only required markers | DEFAULT |
| Disabled controls | still legible; the reason is reachable when it is not obvious | DEFAULT |
| Copy | specific verbs and nouns of this product; no slogan filler ("seamless", "supercharge", "next-gen"); no invented numbers | DEFAULT |
| Icons | one set; an icon-only button has an accessible name; emoji are content, never icons | DEFAULT |

## 8. Performance Mechanisms

| Rule | Value | Level |
|---|---|---|
| Media dimensions | every `img`, `video`, and `iframe` has `width` and `height` or an `aspect-ratio`; space for late content (embeds, banners) is reserved | DEFAULT |
| Hero image | the largest above-the-fold image is an `img` in the HTML, never `loading="lazy"`, with `fetchpriority="high"`; lazy-load only below the fold | DEFAULT |
| Third-party scripts | no synchronous third-party script in `<head>`; use `defer`, `async`, or load on interaction | DEFAULT |
| Field metrics | LCP, INP, and CLS are field data at the 75th percentile (good: LCP at most 2.5 s, INP at most 200 ms, CLS at most 0.1); report them only when measured in this run, otherwise write `not measured` | MUST (no unmeasured number) |

## 9. Checklist

Run per changed screen and record each item `pass`, `fail`, `n/a`, or `not run` with the reason:

1. Contrast pairs from the token plan computed for both schemes, and text over images checked at its worst point.
2. Focus visible and not obscured on every interactive element, by keyboard; dialogs close with Escape.
3. Target sizes and spacing at the smallest width.
4. Reflow at 320px, text at 200%, and the middle band of widths.
5. Every value in changed code belongs to the token plan or the project's tokens.
6. Line length, heading levels, and font supply.
7. Reduced-motion path and no `transition: all`.
8. Every listed state rendered or implemented, and each empty, loading, or error state names its cause and next action.
9. Korean rules when the product language is Korean.
10. Affordance: native elements, accessible names, pointer cursor, hover, active, and disabled states; no zoom block.
11. Performance mechanisms in §8.
12. Ratio floors and browser surfaces rendered within the floor values above.

A static run can pass items 5, 6, 10, and 11 and the source half of 7. Item 12 needs rendered computed values and is `static_only` without a rendered capture.

Ratio floors are checkable from rendered `computed` values (font sizes, spacing, line-length) or from source declarations; they are not automatically measured by this package (rendered measurement is a separate concern).

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| 4.5:1, 3:1, non-text 3:1, reflow 320px, text spacing, resize 200%, target 24×24 (AA) and 44×44 (AAA), focus visible and not obscured, animation from interactions | <https://www.w3.org/TR/2024/REC-WCAG22-20241212/> and its Understanding pages |
| WCAG 3 is a Working Draft and its contrast algorithm is undecided; APCA is not normative | <https://www.w3.org/TR/2026/WD-wcag-3.0-20260910/>, <https://readtech.org/ARC/> |
| Apple text and control sizes (44×44 pt default, 28×28 pt minimum), "make motion optional" | <https://developer.apple.com/design/human-interface-guidelines/accessibility> |
| Android touch target 48×48 dp | <https://developer.android.com/guide/topics/ui/accessibility/apps> |
| Material token values (type scale, shape 0/4/8/12/16/28/full, elevation steps, `cubic-bezier(0.2, 0, 0, 1)`) | <https://github.com/material-components/material-web/tree/main/tokens/versions/v0_192> (Apache-2.0) |
| Line length 45-90 characters, line spacing 120-145%, at most three heading levels | <https://practicaltypography.com/line-length.html> |
| Ratio floors (type steps 1.25x, heading space 1.5x, group space 2x, body 65-75ch, display 6rem, tracking -0.04em) and the browser-surface list (`::selection`, caret, scrollbar, focus ring, underline offset, figures) | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored in this package's own words; the source repository has no license and no text or code was copied. The thresholds come from the Apache-2.0 upstream named in that project's frontend attribution (<https://github.com/pbakaus/impeccable>, Apache-2.0) and were re-chosen here as floor defaults: the smallest type step is 1.25x, display text caps at 6rem, and tracking stops at -0.04em |
| Hit targets, `transition: all`, nested radii, autoplay pause | <https://github.com/vercel-labs/web-interface-guidelines/blob/434b7f91364665f2f733b310ec54809bf8f37937/AGENTS.md> (MIT) |
| UI motion under 300 ms, no ease-in, no `scale(0)`, stagger 30-80 ms, frequency rule | <https://github.com/emilkowalski/skills> (commit `c8a7962`) (MIT) |
| Response-time limits, loading indicators, empty states, error messages, form rules | <https://www.nngroup.com/articles/response-times-3-important-limits/>, <https://www.nngroup.com/articles/skeleton-screens/>, <https://www.nngroup.com/articles/empty-state-interface-design/>, <https://www.nngroup.com/articles/error-message-guidelines/>, <https://www.nngroup.com/articles/web-form-design/> |
| Error summary, one question per page, no asterisk-only required markers | <https://design-system.service.gov.uk/components/error-summary/>, <https://design-system.service.gov.uk/patterns/question-pages/> (OGL v3.0) |
| Korean body 17px default with a 16px floor, line height at least 150%, `keep-all`, breakpoints 360/768/1024/1280, accent at most 5% | <https://www.krds.go.kr/html/site/style/style_03.html> and its sibling style pages |
| `word-break: keep-all` behavior | <https://developer.mozilla.org/en-US/docs/Web/CSS/word-break> |
| Pretendard is SIL OFL 1.1 with a reserved font name | <https://github.com/orioncactus/pretendard> |
| Palette cap, affordance rules (native elements, names, pointer cursor, distinct states), zoom never blocked, touch spacing, responsive states beyond two, `dvh` over `100vh`, compact fixed chrome, glass and glow dose caps, media dimensions, hero image priority, deferred third-party scripts, and never reporting an unmeasured metric | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop/SKILL.md` R-03, R-10, R-13, R-29, R-39, R-40; `antislop-layoutmobile/SKILL.md`; MIT) |
| Core Web Vitals thresholds at p75 | <https://web.dev/articles/vitals> |

### Evidence grade

`MUST` rows restate WCAG 2.2 AA and Level A requirements and are as strong as the standard. `DEFAULT` rows pick one value from ranges the sources give; where sources disagree (Apple 28 pt versus 44 pt, Butterick 120-145% versus KRDS 150% for Korean), the table states which applies. The Korean 160-170% range is this package's choice for long reading, not a sourced number. Ratio-floor rows are `DEFAULT`: the numbers above are starting values re-authored from an Apache-2.0 upstream, not WCAG requirements, and a documented project system replaces them.
