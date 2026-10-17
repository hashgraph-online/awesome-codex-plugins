---
name: readability-line-length
description: 'Set line length (measure) for prose — capping the maximum width of body text so lines stay in the 45–75 character range that supports comfortable sustained reading. Use when designing article layouts, documentation, email templates, dashboard copy, or any container that holds paragraphs of prose. Line length is the most fundamental readability decision because it directly affects the reader''s eye movement; lines that are too long or too short both cost reading comfort.'
---

# Readability — line length (measure)

Line length, also called *measure* in typography, is the number of characters per line. It's the most fundamental readability decision because it directly affects the reader's eye movement: at the end of each line, the eye must jump back and find the start of the next line, and the difficulty of that jump scales with line length.

The recommended range, established by centuries of book typography research and confirmed by modern reading studies: **45 to 75 characters per line for body prose**, with 60–66 as the sweet spot for most use cases.

## Why line length matters

Two failure modes bracket the comfortable range.

**Too long (>75 characters per line).** The eye must travel a long distance between line ends. The reader can lose their place — find the wrong line on the way back, or read the same line twice. Reading slows. Fatigue accumulates faster.

**Too short (<45 characters per line).** The eye has to jump too frequently. Each line break interrupts the cognitive thread. Words at the line ends are often hyphenated awkwardly. Reading feels stuttering rather than flowing.

The 45–75 range is wide enough to accommodate different design contexts; specific products can land at different points based on their typeface, audience, and content.

## How line length is set

Line length is determined by:

**Container width.** A text container (`<article>`, `<main>`, a content column) has a width in pixels.

**Font size.** The number of characters per line depends on how many character-widths fit in the container.

**Typeface character width.** Different typefaces have different average character widths at the same point size. A condensed typeface fits more characters per line than a wide one.

**Letter spacing.** Looser letter spacing means fewer characters per line.

In practice: pick a target line length in characters (say, 65), and calculate the container width that produces that line length at your body size. For 16px Inter, this is roughly 600–700px container width. For 18px Georgia, it's about 650–750px. The exact number depends on the typeface.

The CSS approach: use `max-width` on text containers, with a value calibrated to your target line length. Or use `ch` units (which are based on character width): `max-width: 65ch;` produces approximately 65 characters per line in most typefaces.

## Line length on responsive layouts

The biggest line-length challenge is responsive layouts that need to work across screen widths.

**At wide desktop:** without `max-width`, body text fills the entire viewport width, often producing 130+ character lines that fail readability.

**At narrow mobile:** the same text reflows to the narrow width, producing 30–40 character lines. With smaller font sizes, this can be acceptable, but the text feels cramped.

The fix: cap `max-width` on text containers (so lines don't get too long at wide widths), and consider scaling font size down on narrow widths (so lines don't get too short).

A practical pattern:

```css
.prose {
  max-width: 65ch;
  font-size: 16px;
}

@media (min-width: 1024px) {
  .prose {
    font-size: 18px;
  }
}
```

This gives ~65 characters per line at all widths, with slightly larger text on larger screens.

## Worked examples

### A blog post layout

A blog post container with `max-width: 65ch` and 16px body text. On any screen wider than ~700px, the article reads at a comfortable line length. On screens narrower than ~400px (mobile portrait), the text reflows to fill the available width, producing 30–50 character lines depending on typeface.

The mobile case is suboptimal but acceptable. Consider bumping the body size to 18px on mobile to get back into the 45–55 character range.

### A dashboard with embedded prose

A dashboard widget shows a paragraph of explanatory text inside a card. The card is 800px wide. Without intervention, the text fills the card and runs ~140 characters per line. Users skip the explanation because the long lines are visually intimidating.

The fix: cap the explanatory text's max-width at 65ch (about 600px at the dashboard's body size). The text now reads at a comfortable line length, even though the card is wider.

### Email layout

An email template designed at 600px column width with 14px body text produces roughly 75–80 characters per line — at the upper edge of the comfortable range. On mobile (read in narrow portrait), the email may reflow to 320px, producing 40 character lines (just below the comfortable minimum, but acceptable).

The compromise of email design: you can't perfectly satisfy all clients and screen sizes. Pick a target (often 600px column at 14–16px text) and accept that some clients will render slightly wider or narrower.

### A wide-screen documentation site

A documentation site renders on a large monitor. Without max-width, body prose fills 1500px+ at 16px — well over 200 characters per line. Users zoom out, lean closer, or invoke reader mode.

The fix: cap content max-width at 65ch (~600px at this body size). The wide screen has plenty of room for sidebar navigation, table of contents, and other supporting elements alongside the centered prose.

### A code-and-prose documentation page

A documentation page with prose explaining concepts and code blocks demonstrating them. The prose follows readability rules (max-width: 65ch). Code blocks can extend wider — code lines often need 80–120 characters before wrapping, and wrapping code mid-line can break syntax highlighting and indentation.

The pattern: prose blocks at 65ch max-width; code blocks at a wider max-width (90–120ch) or full width within the article column. Use horizontal scroll if code lines exceed the available width rather than wrapping.

## Anti-patterns

**Letting body text fill the container width.** The default behavior on most layouts. Long lines are uncomfortable, and the longer the screen, the worse it gets.

**Setting `max-width` in pixels and forgetting to test on different displays.** A 700px max-width designed for a 14px font may produce different line lengths if a user has zoomed the page or if the system font is different.

**Two-column layouts with too-narrow columns.** Splitting a content area into two columns can produce columns of 30–40 characters each — too narrow. Either widen the columns or use a single column.

**Prose-and-image layouts where the prose is squeezed.** When a sidebar image takes 40% of the width and prose takes the remaining 60%, the prose may end up at narrower-than-comfortable line length. Either reflow on narrower screens or reconsider the layout.

**Justified text at narrow widths.** Justified text (left and right edges aligned) needs sufficient line length to distribute spacing without producing rivers of white space. At narrow widths, justified text becomes spotty. Use left-aligned (ragged-right) instead.

**Forgetting subheadings and other interruptions.** A 65ch column of pure prose for thousands of words is a wall, even at the right line length. Combine line-length capping with paragraph and section structure.

## Heuristic checklist

Before shipping a long-form layout, ask: **What's the line length of body text at the rendering widths my users will see?** Measure, don't estimate. **Is it in the 45–75 character range?** If wider, add max-width; if narrower, consider larger font or wider container. **Does the line length hold up across mobile, tablet, and wide desktop?** Test all breakpoints. **Are code blocks and other special content handled separately?** They often need different rules.

## Related sub-skills

- `readability` — parent principle on sustained-reading ease.
- `readability-rhythm-and-prose` — sibling skill on paragraph spacing and rhythm.
- `legibility-typeface-and-size` — typeface and size choices that interact with line length.
- `chunking` — paragraph breaks chunk prose into readable units, complementing line-length control.

## See also

- `references/measure-by-context.md` — line-length recommendations for specific contexts (book, web, email, documentation).
