# Research: Deck Design

Why this package lays a slide out the way it does, and what was measured before choosing. This file records the sources, the patterns that survived contact with real decks, and the ones that were rejected.

## 1. What Was Read

Twenty-five public deck skills and generators were inspected on 2026-11-14. Star counts and last-commit dates are from the GitHub API on that day; licence is from the repository.

| Repository | Stars | Last commit | Licence | What it contributes |
|---|---|---|---|---|
| `anthropics/skills` | 22817 | 2026-11-06 | none | Thumbnail grid review, "unpack and edit the XML" discipline |
| `hugohe3/ppt-master` | 5979 | 2026-11-13 | MIT | Image composition and crop geometry vocabulary |
| `zarazhangrui/frontend-slides` | 2465 | 2026-06-23 | MIT | Type scale and spacing taken from web design |
| `op7418/guizang-ppt-skill` | 2046 | 2026-10-30 | AGPL-3.0 | Editorial layout and section openers |
| `gitbrent/PptxGenJS` | 976 | 2025-11-28 | MIT | Chart and shape XML that PowerPoint accepts |
| `chuspeeism/dashi-ppt-skill` | 907 | 2026-11-06 | AGPL-3.0 | Theme token set and editable output |
| `scanny/python-pptx` | 745 | 2024-08-07 | MIT | Package part structure, what a reader expects |
| `ningzimu/codex-ppt-skill` | 370 | 2026-10-13 | MIT | Outline-to-deck pipeline |
| `GordenSun/GordenPPTSkill` | 393 | 2026-06-22 | NOASSERTION | Non-destructive text editing |
| `iOfficeAI/OfficeCLI` | 2272 | 2026-11-12 | Apache-2.0 | Rendering and verification round trip |
| `crazyykhllc-bit/CyberPPT` | 189 | 2026-07-20 | MIT | Consulting narrative and quality gates |
| `microsoft/Resource2Skill` | 62 | 2026-11-05 | MIT | Accessibility and alt text in generated decks |
| `likaku/Mck-ppt-design-skill` | 43 | 2026-11-03 | Apache-2.0 | A 72-entry layout catalogue |
| `siril9/presentation-skill` | 26 | 2026-10-08 | MIT | Slide-kind vocabulary |
| `EveryInc/hands-on-deck` | 17 | 2026-08-04 | MIT | Inspect / edit / verify loop |
| `mpuig/agent-slides` | 3 | 2026-03-15 | MIT | Card, badge, KPI row patterns with rationale |
| `tmustier/clean-slides` | 3 | 2026-05-07 | MIT | Subtraction rules |
| `Hasasasa/html-to-editable-pptx` | 10 | 2026-07-07 | MIT | HTML geometry to editable shapes |
| `artifact-kit/html-to-pptx-skill` | 1 | 2026-04-29 | none | The same, with a smaller surface |
| `eddyzzl/imagegen-pptx-pipeline` | 1 | 2026-09-14 | MIT | Image placement pipeline |
| `liustack/pptwise` | 1 | 2026-10-23 | MIT | Deck review checklist |
| `withevergrow/withicons` | 1 | 2026-11-06 | MIT | Icon use in slides |
| `geekfujiwara/powerpoint-agent-skills` | 0 | 2026-11-10 | MIT | Runtime notes for agent-driven decks |
| `CxyZyr/PPTX-Template-Skills` | 4 | 2026-06-12 | MIT | Template extraction |
| `ferdinandobons/brand-docs` | — | — | none | Brand token extraction |

## 2. Patterns Adopted

### Cards for peers, numbers for sequence

A card says "these items have equal weight". A numbered badge says "step 2 follows step 1". Mixing them on one slide makes the reader look for a sequence that is not there. This package keeps those as separate kinds: `columns` draws cards, `timeline` draws dated steps on one rule.

### One number per card, with its comparison

Every KPI needs a comparison frame, because a number with no base is not a claim. `kpi` and `stats` both enforce a `note` or `delta` slot under the value, and the layout reserves its height whether or not the field is filled, so a filled version and an empty version of the same slide do not shift.

### Action titles

The title states what the data proves, not what the slide contains. "결제 실패율은 3주 만에 12% 줄었습니다" beats "결제 실패율 추이". This belongs to the narrative rule file, but the layout enforces one line of it at 30 points, which is about twenty Korean characters, so an action title that does not fit is a title that is trying to be two slides.

### Grey first, accent for one thing

Start every chart in grey and colour only the series the argument is about. This package assigns the accent to the first series and falls back to muted, line, and surface for the rest. A chart where every series is accent-coloured has no emphasis at all.

### Alignment to one left edge

Cards, tables, captions, and the title share one margin. A centred column that does not match the title's left edge reads as a mistake even when it is deliberate. The one exception is a picture that fills the column, and hero/quote, where the block is centred as a whole.

## 3. Patterns Rejected

- **Fixed card height as a share of the body.** Dashi and several others fix a card to a percentage of the slide. With three short bullets this leaves a large empty panel, and with a long one it overflows. This package measures the text first and sizes the card to it.
- **Automatic right/left image alternation.** `ppt-master` deliberately refuses to choose; the author names the side. This package does the same with `image.side`, defaulting to `right`.
- **Slide-level colour changes.** A deck with one slide in green and one in orange reads as two decks. The palette is a deck field; a slide may override only for a single, deliberate exception.
- **Generating images.** Every repository that generates pictures for slides also produces decks that look generated. This skill places pictures and says so when there is none.

## 4. What This Changed

| Decision in this package | Source of the decision |
|---|---|
| Fifteen kinds, each with one argument shape | Mck catalogue's 72 entries condensed to the ones a real deck uses |
| Cards measured, not fixed | Failure of the fixed-height card across the test decks |
| KPI card height from a stack of value, label, and note | Card pattern plus the "always carry a comparison" rule |
| Timeline capped at five milestones | Readability at projection size; the sixth label collides |
| Compare centres the pair, capped at a third of the body | A block dropped to the exact middle detaches from the title |
| One accent per deck | Grey-first rule from the chart research |

## Sources

> Checked 2026-11-14.

| Claim | Source |
|---|---|
| Card, badge, and KPI row patterns with their rationale | <https://github.com/mpuig/agent-slides> |
| A 72-entry consulting layout catalogue | <https://github.com/likaku/Mck-ppt-design-skill> |
| Thumbnail-based review before delivery | <https://github.com/anthropics/skills> |
| Consulting narrative structure and quality gates | <https://github.com/crazyykhllc-bit/CyberPPT> |
| Image placement refusal to auto-choose a side | <https://github.com/hugohe3/ppt-master> |
| Theme tokens and editable output requirement | <https://github.com/chuspeeism/dashi-ppt-skill> |

### Evidence grade

`LOCAL` — the adopt/reject decisions are this package's, taken after rendering and reading the test decks on 2026-11-14. Star counts and dates were read from the GitHub API on the same day. No repository listed here was benchmarked against the same deck, so the comparison is of pattern descriptions, not measured output quality.
