---
name: legibility-contrast-and-spacing
description: 'Apply contrast and spacing for legibility — calibrating color contrast between text and background, character tracking, and line leading so a chosen typeface and size actually render legibly. Use when picking text colors, choosing background colors that will carry text, evaluating accessibility against WCAG, fine-tuning typography for production rendering, or auditing why text "looks designed" but is hard to read. Even a perfect typeface at the right size will fail if contrast is too low, tracking too tight, or leading too cramped.'
---

# Legibility — contrast and spacing

A typeface and size are necessary but not sufficient for legibility. The conditions under which type is rendered — contrast against background, spacing between characters, spacing between lines — determine whether the chosen typography actually communicates. Most legibility failures in production are spacing or contrast failures, not typeface failures.

## Color contrast

Color contrast is the difference in luminance between text and its background. WCAG codifies minimum thresholds:

- **4.5:1** for normal text (under 18pt regular or 14pt bold).
- **3:1** for large text (18pt+ regular or 14pt+ bold).
- **3:1** for graphical objects and UI components (icons, button outlines).
- **7:1** for AAA conformance — recommended for users with low vision or in poor viewing conditions.

These are floors, not targets. Best practice is to substantially exceed them where possible.

Common contrast failures:

**Light gray text on white.** Common because designers like the "soft" feel. #999 on white is roughly 2.8:1, well below WCAG AA. #767676 is roughly 4.5:1. Below this, you're failing the standard.

**Brand color on white that doesn't pass.** A brand color in the medium-blue range (e.g., #5BA0E6) on white is often around 3:1 — fine for large display text, fails for body text. Pick text colors with adequate contrast even if the brand color is borderline.

**Text on photos or gradients without protection.** Text overlaid on busy photos or gradients can fail in some places and pass in others. Solutions: a dark scrim over the photo, a solid text background, or moving the text out of the photo area.

**Low-contrast helper or muted text.** Helper text intentionally de-emphasized often drifts into illegibility. Don't go below 4.5:1 (or 3:1 if it's larger text and clearly secondary).

**Color-only state indicators.** A red error message that loses meaning when rendered to a colorblind user, or a green success message that's invisible to others. Always pair color with shape, label, or icon.

Tools for verifying contrast:

- WebAIM contrast checker.
- Browser dev tools' built-in contrast picker.
- axe, Lighthouse, WAVE for automated audits.
- Stark or similar Figma/Sketch plugins for design-time checking.

## Tracking (letter spacing)

Tracking is the space between characters. The right tracking depends on the typeface, the size, and the use.

**Body text:** typefaces are usually designed for body sizes with built-in correct tracking. Don't adjust tracking for body unless you have a specific reason.

**Display sizes (large):** large text often benefits from tighter tracking (-1% to -2%) to prevent characters from feeling too far apart. Many display typefaces are designed expecting some negative tracking at large sizes.

**Small sizes (especially below 12px):** small text may need slightly looser tracking (+0.5% to +1%) to prevent characters from merging into ambiguous shapes.

**All caps:** uppercase text needs significantly looser tracking (+5% to +10%) because capital letters have less visual differentiation in their outlines.

**Bold text:** can sometimes need slightly looser tracking to prevent visual crowding.

Common tracking failures:

**Default tracking on display sizes.** Many typefaces look loose at large sizes; tighten to -1% to -3%.

**Tight tracking on small text.** A common cause of "blurry-looking" small text. Loosen slightly.

**Untracked all-caps.** Uppercase without extra tracking looks crowded and reads slowly.

## Leading (line height)

Leading is the space between lines. The right leading depends on the typeface, the line length, and the use.

**Body text:** 1.4× to 1.6× the font size. So for 16px text, line height of 22–26px. This range is comfortable for sustained reading.

**Display / headline text:** 1.0× to 1.2× the font size. Tighter leading at display sizes prevents headlines from feeling fragmented.

**UI labels and dense text:** 1.2× to 1.4× the font size. Tighter than body but loose enough to keep characters from overlapping.

**Long-form prose:** 1.5× to 1.7× the font size. Slightly more generous than UI body text for sustained reading comfort.

Common leading failures:

**Default browser leading on body text.** Browsers default to about 1.2× line height, which is too tight for body text. Set explicit line-height: 1.5 or higher for prose.

**Leading too tight for the font's x-height.** Fonts with tall x-heights (Verdana, Inter) need slightly more leading than fonts with shorter x-heights (Times, Garamond) at the same size.

**Inconsistent leading across the type system.** Body, headings, captions all should have leading that's calibrated to their use; one-size-fits-all is rarely right.

**Tight leading on multi-line UI elements.** Buttons, table cells, form labels with multiple lines often have insufficient line height, causing the lines to crowd.

## Word spacing and paragraph spacing

Less critical than tracking and leading for most UI but worth checking:

**Word spacing.** Default word spacing in most typefaces is appropriate. Adjust only for specific cases (justified text, very large display).

**Paragraph spacing.** Space between paragraphs should be larger than line spacing. A common ratio: paragraph spacing = 0.75× to 1× the font size, in addition to leading.

**First-line indent vs. block paragraphs.** Most digital UI uses block paragraphs with space between. First-line indents are reserved for editorial / book contexts.

## Worked examples

### A button that fails contrast

A button with white text (#FFFFFF) on a light blue background (#7AB8FF). Contrast ratio: 2.1:1. Below WCAG AA for both normal and large text.

The fix: darken the blue (#1E78D6 gives 4.5:1) or change the text to a darker color. White on the original blue is too low contrast for accessibility.

### Body text with too-tight leading

Default browser styling: 16px body text with default line-height (about 1.2 = 19px). The text feels cramped; users skim faster than they should and miss content.

The fix: set line-height to 1.5 or higher for body text. 24px line height for 16px text is a comfortable baseline for sustained reading.

### A headline with too-loose tracking

A 48px display headline using a typeface with default (positive) tracking. The letters feel separated; the headline doesn't read as a unit.

The fix: tighten tracking to -1% or -2% at this size. The headline now reads as a cohesive title rather than as separate letters.

### All-caps navigation that's hard to read

A navigation bar uses ALL CAPS labels at 13px with default tracking. The text feels crowded and reads slowly because all-caps lacks the ascender/descender silhouette that aids word recognition.

The fix: add positive tracking (+5% to +8%) to give the capitals room to breathe; consider whether all-caps is necessary at all (sentence-case or title-case is usually more readable).

### Helper text that drifts into illegibility

Helper text under form fields is set in #BBBBBB on white. Contrast ratio: 1.6:1. Many users can't read it at all; even those who can, struggle.

The fix: darken to #767676 or similar (gives 4.5:1). The helper text remains clearly secondary but is now legible.

### Code that's hard to scan

Code blocks in a documentation site use a serif typeface at 14px with default tracking and line-height. The text is technically legible but feels dense and hard to scan.

The fix: switch to a monospace typeface (JetBrains Mono or similar), set line-height to 1.6 (a bit more generous than body for visual scanning), and add some background tinting to set code apart from prose.

## Anti-patterns

**Designing on high-contrast displays then shipping to low-contrast contexts.** Mobile devices in sunlight, lower-DPI external monitors, projectors all reduce effective contrast. Test in the worst conditions you'll actually encounter.

**Using opacity for text instead of explicit colors.** A semi-transparent black text on a colored background can produce unpredictable contrast depending on the underlying color. Use explicit colors, computed against the actual background.

**Ignoring user-chosen color schemes.** Dark mode, high-contrast mode, and user-overridden colors all change the effective contrast. Test your typography in all the modes your users will use.

**Tracking adjustments without testing.** Tracking is sensitive to typeface and size. A -2% adjustment that improves a 48px headline may break a 14px body. Calibrate each adjustment to its specific use.

**Set-and-forget design tokens for typography.** Typography tokens that haven't been audited in years often drift away from current best practices. Review your typography system periodically.

**Relying on automated contrast checkers without visual review.** Automated tools catch the most obvious failures but miss situations like text over photos, gradient backgrounds, or color combinations that pass technically but feel low-contrast.

## Heuristic checklist

Before shipping any typography decision, ask: **Does the contrast meet WCAG AA at minimum (4.5:1 normal, 3:1 large)?** Check with a contrast tool. **Does the contrast hold up in dark mode?** Test both modes. **Is the leading appropriate for the use case?** 1.5× for body, 1.2× for display. **Is the tracking appropriate for size and case?** Tighter for display, looser for small or all-caps. **Have you tested in production conditions?** Actual devices, actual browsers, actual viewing conditions.

## Related sub-skills

- `legibility` — parent principle on visual character clarity.
- `legibility-typeface-and-size` — sibling skill on typeface and size choices.
- `color` — color choices that affect contrast.
- `accessibility` — contrast is one critical accessibility dimension.
- `signal-to-noise` — well-spaced, high-contrast type is signal; the opposite is noise.

## See also

- `references/contrast-spacing-recipes.md` — specific recipes for common situations (light mode, dark mode, hero text, code, captions).
