---
name: readability
description: 'Apply the principle of Readability — the ease with which sustained prose can be read, determined by line length, line height, paragraph rhythm, font choice for prose, and visual breathing room. Use when designing long-form content (articles, documentation, books, transcripts), writing email or report layouts, evaluating whether users can comfortably read paragraphs of text. Distinct from legibility (per-character clarity); readability is about the experience of reading sustained prose without fatigue. The two principles compose: readability requires legibility and adds prose-specific constraints.'
---

# Readability

> **Definition.** Readability is the ease with which sustained text can be read — paragraphs, articles, documentation, long-form content. It depends on the legibility of individual characters (necessary precondition) plus a set of prose-specific factors: line length, line height, paragraph spacing, typeface suited for sustained reading, and visual breathing room. A readable design lets the reader move smoothly through the text without fatigue or visual jumping.

Readability is distinct from *legibility*. Legibility is per-character clarity — can the user identify each letter at a glance. Readability is sustained-reading ease — can the user read paragraphs of prose comfortably without tiring.

A typeface can be highly legible (every character distinguishable) but poorly readable (uncomfortable for long-form reading) — many display typefaces are this way. A typeface can be highly readable (comfortable for sustained reading) but only moderately legible (some characters look similar) — many traditional book typefaces have minor character-distinction issues that don't matter for prose.

## Why readability matters

Most UI text is short — labels, buttons, helper text. Legibility usually dominates these contexts. But many products also serve long-form text: documentation, articles, emails, transcripts, reports, books, news, dashboards with substantial commentary. For these, readability matters as much as or more than legibility.

Poor readability costs the user real effort: they tire faster, lose their place more often, miss content, and abandon longer pieces. The cost is not in any single moment but in the cumulative fatigue of reading.

## The five inputs to readability

Readability is determined by:

**Line length (measure).** The number of characters per line. The classic recommendation is 45–75 characters per line for body prose, with ~66 as the sweet spot. Lines that are too long cause the eye to lose track between the end of one line and the start of the next; lines that are too short force frequent line breaks that interrupt reading flow.

**Line height (leading).** The vertical space between lines. Generous leading aids reading by giving the eye clear separation between adjacent lines. Tight leading causes ascenders and descenders to overlap, slowing reading.

**Paragraph spacing.** The space between paragraphs. Adequate spacing creates clear paragraph breaks that aid scanning and chunking. Tight paragraph spacing turns prose into a wall of text.

**Typeface choice for prose.** Some typefaces are designed for sustained reading (humanist serifs, transitional serifs, humanist sans-serifs); others are designed for short use (display, signage). Sustained reading typefaces have proportions and details that reduce eye fatigue.

**Visual breathing room.** Margins around text, vertical space between sections, page-level rhythm. Cramped layouts cost reading comfort even when individual elements are well-designed.

## Diagnosing readability problems

Symptoms of readability issues:

**Users skim or abandon long content.** They open an article, scan the first paragraph, and leave. Often the problem is not the content but the readability of the layout.

**Users complain about "tiring" or "hard-to-read" pages.** Difficult to articulate, but a reliable signal of readability issues.

**Reading-time analytics drop sharply over content length.** Time-on-page falls faster than content length predicts; users are tiring faster than the content warrants.

**Reflow on different screen sizes produces dramatically different layouts.** A page that's readable at desktop width may be unreadable at a different width if the text doesn't reflow well.

**Users zoom in or use reader mode.** When users invoke browser reader mode or zoom in, your readability has failed; the browser is doing what your design should have done.

## Sub-skills in this cluster

- **readability-line-length** — Setting line length (measure) and how it interacts with screen width, font size, and reading context. The most fundamental readability decision.
- **readability-rhythm-and-prose** — Paragraph rhythm, leading, vertical spacing, and the prose-level readability that goes beyond line-by-line.

## Worked examples

### A readable article layout

A long-form article on a content site: 18px serif body type at 1.6 line height, line length capped at 70 characters, paragraph spacing of about 0.8em above each paragraph, generous margins on the article, no other elements competing in the central column. Subheadings break up sections every 3–5 paragraphs.

The reader can move smoothly through the article without conscious effort. The line length is short enough that the eye easily finds the next line, the leading is comfortable, and the paragraph rhythm provides natural rest points.

### A documentation page

Documentation often combines prose and code. The prose follows similar readability principles (15–17px body text, 1.6 line height, 60–70 character line length) and code blocks are differentiated visually (monospace, slightly tinted background, generous leading).

The combination requires careful design: code blocks shouldn't disrupt prose flow; prose shouldn't blur into code. Vertical rhythm between paragraphs and code blocks should be consistent.

### A wall of text that fails

A FAQ page with no structural breaks: 16px text running 120 characters per line, 1.2 line height, single paragraphs of 10–15 sentences each, no subheadings. Users open it, see the wall, and leave without reading.

The fix: shorter paragraphs, subheadings every few paragraphs, line length capped at 70 characters, line height bumped to 1.5+, more vertical space between paragraphs. The content is the same; the readability transforms.

### A dashboard with too-long lines

A dashboard widget shows a paragraph of explanatory text that runs the full width of the dashboard column — about 130 characters per line. Users read the first few lines and skip the rest because the long lines tire the eye.

The fix: cap the explanation's max-width at 70 characters. The dashboard column can be wider, but the text within it shouldn't run the full width.

### Email that's hard to read on mobile

An email designed at desktop width (600px column with 12pt text) is read on a mobile phone. The text reflows to the narrower screen width but the font size doesn't scale up; lines are now very short (15–20 characters) and the user pinches to zoom or switches to a different reader.

The fix: design email for mobile-first, with larger base font sizes (16–18px) and narrower max-widths that still read well at desktop width.

## Anti-patterns

**Lines that run the full container width.** Default web behavior is to fill the available width with text, which often produces lines too long for comfortable reading. Cap your max-width.

**Tight leading on body prose.** Browser default leading (about 1.2) is too tight for sustained reading. Bump to 1.5 or higher for body content.

**No paragraph breaks.** Long paragraphs that don't break up are visually intimidating and cognitively dense. Most prose benefits from 3–5 sentence paragraphs.

**No subheadings in long content.** A 2000-word article without subheadings is a wall. Subheadings every 3–5 paragraphs provide visual rest and structural navigation.

**Dense layouts that compete with the prose.** Sidebars, ads, callouts, and pop-ups that surround the prose all reduce reading focus. Long-form content benefits from cleared layouts that prioritize the reading experience.

**Display typefaces in body prose.** A typeface chosen for headlines used at body sizes for prose. Reading fatigue accelerates rapidly.

**Justified text without proper hyphenation.** Justified text (left and right edges aligned) without good hyphenation produces uneven word spacing — "rivers" of white space running through the prose. Most digital contexts should use left-aligned (ragged-right) text instead.

**Text overlaid on busy backgrounds.** Text on a photo or pattern fights for attention with the background. Use a solid background for body text.

## Heuristic checklist

Before shipping any long-form content, ask: **Is the line length capped at 45–75 characters?** Wider needs justification. **Is the leading at least 1.5× the font size?** Tighter is uncomfortable. **Is there adequate paragraph spacing?** Visible breaks between paragraphs. **Are there subheadings every 3–5 paragraphs?** Long content needs structural navigation. **Is the typeface designed for sustained reading?** Display type doesn't survive at body sizes. **Have I tested at all the screen sizes my users will use?** Especially mobile.

## Related principles

- **Legibility** — the per-character clarity that readability builds on.
- **Hierarchy** — readability is supported by clear structural hierarchy.
- **Chunking** — paragraphs and subheadings chunk prose into readable pieces.
- **Signal-to-Noise Ratio** — readable layouts maximize signal (the prose) and minimize noise (everything else).
- **Form Follows Function** — long-form reading layouts should be different from UI layouts because their function is different.
- **Accessibility** — readable typography helps users with reading differences.

## See also

- `references/lineage.md` — origins in book typography, web typography, and reading research.
- `readability-line-length/` — sub-skill on line length (measure).
- `readability-rhythm-and-prose/` — sub-skill on paragraph rhythm and breathing room.
