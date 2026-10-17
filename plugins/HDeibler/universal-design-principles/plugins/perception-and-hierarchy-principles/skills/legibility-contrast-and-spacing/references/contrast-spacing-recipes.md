# Contrast and spacing — recipes for common situations

Specific defaults and starting points for typography in different contexts. Use as a baseline; adjust based on your typeface and audience.

## Light mode body text

**Color:** dark text on white background. #1A1A1A on #FFFFFF gives ~17:1 contrast, very comfortable. Pure black (#000) on white is sometimes seen as too harsh; #1A1A1A or #222222 reads more comfortably while still passing AAA.

**Size:** 16px is a comfortable baseline for sustained reading. 14px is acceptable for denser UI; below 14 starts to require careful design.

**Leading:** 1.5× to 1.6× the font size. So 24–26px line height for 16px text.

**Tracking:** default for the typeface (don't adjust unless the typeface is known to need it).

## Dark mode body text

**Color:** light text on dark background. #E6E6E6 on #1A1A1A gives ~14:1 contrast. Don't use pure white (#FFFFFF) on pure black (#000000) — that's harsh and can produce eye strain. Reduce contrast slightly for dark mode by using a softer white and a not-quite-black background.

**Size:** same as light mode, possibly 1px larger if the typeface gets thinner-looking in dark mode (which some typefaces do).

**Leading:** same as light mode.

**Tracking:** consider +0.5% to +1% in dark mode; light text on dark backgrounds can feel slightly tighter optically.

## UI labels and helper text

**Body label color:** #1A1A1A or similar dark on light backgrounds.

**Helper / muted text color:** #6C6C6C or #767676 on white. Stays above 4.5:1 contrast. Don't go lighter for "softer" feel — it crosses into illegibility.

**Size:** 14–15px for primary labels; 12–13px for helper text or captions. Don't go below 12px for text users need to read.

**Leading:** 1.4× for label text, 1.5× for helper text.

## Display headlines

**Color:** same as body, or use a muted color (#444 or similar) for secondary headings.

**Size:** scaled by your typographic ratio. Common scale: 24px (h3), 32px (h2), 48px (h1), 64–96px (hero).

**Leading:** 1.0× to 1.2× the font size at display sizes. Tighter than body to keep headlines feeling unified.

**Tracking:** -1% to -3% at display sizes. Most display typefaces look loose at default tracking when scaled up.

## Hero text on photos

**Color:** white text on a dark scrim (a semi-transparent black overlay over the photo). The scrim should be dark enough to bring contrast above 4.5:1.

**Alternative:** text on a solid background area beside or below the photo, rather than overlaid.

**Tracking:** small negative tracking (-1% to -2%) for visual cohesion at large sizes.

**Leading:** tight (1.0× to 1.1×).

## Buttons

**Primary button:** white text on a brand color background. The brand color should give at least 4.5:1 contrast against white. Most "modern" tech blues (#3B82F6, #2563EB) do; lighter blues often don't.

**Secondary button:** dark text on a light background, or brand-color text on white with a brand-color border. Whatever combination, verify contrast.

**Disabled button:** muted text on muted background. Disabled buttons are exempt from WCAG contrast requirements but should still be visually distinguishable.

**Size:** 14–16px text. 16px gives more visual weight and is preferred for primary actions.

**Padding:** vertical padding should be at least equal to the font size. So 16px text in a button needs at least 16px vertical padding (top + bottom = 32px), giving the button a comfortable 48px+ height (good for touch targets).

## Forms

**Field label:** 14–16px, weight 500 or 600 (slightly emphasized). High contrast against background.

**Field value (user's input):** 16px regular weight (resist going smaller — input text is critical and should be very legible).

**Placeholder text:** muted color (#999 on white is on the edge — go with #767676 to stay accessible). Don't use placeholder as a substitute for label.

**Helper text:** 12–14px, muted color, below the field.

**Error text:** 12–14px, error color (red), high contrast. Reinforce with an icon (don't rely on color alone).

## Tables and data

**Header text:** 14px, weight 500 or 600, slightly emphasized.

**Body text:** 14–15px regular weight, high contrast.

**Numeric values:** consider tabular figures if the typeface offers them. They give consistent column widths. If not, use a monospace typeface for tables of numbers.

**Leading:** 1.3× to 1.5×. Tables benefit from slightly tighter leading than prose for scannability.

**Color:** standard body colors. Avoid alternating row backgrounds at low contrast (they can hurt scannability rather than help).

## Code blocks

**Typeface:** monospace (JetBrains Mono, Fira Code, Source Code Pro, etc.).

**Size:** 14–16px. Slightly larger than UI body text because code is denser and benefits from the extra breathing room.

**Leading:** 1.5× to 1.7×. Code benefits from generous leading for visual scanning.

**Background:** subtle tint (light gray on light mode, slightly darker than the surface in dark mode) to set code apart from prose.

**Syntax highlighting colors:** verify each color against the background for contrast. Many syntax themes have one or two colors (often the comment color) that fall below 4.5:1. Adjust those colors.

## Captions and footnotes

**Size:** 12–14px.

**Color:** muted (#767676 or similar) — clearly de-emphasized but still legible.

**Leading:** 1.4× to 1.5×.

**Use sparingly:** captions and footnotes drift into illegibility quickly because designers want them to "feel small." Resist setting them below 12px.

## Marketing / hero copy

**Size:** larger than UI text. 18–20px for body marketing copy; 24–32px for sub-headlines; 48–96px for hero.

**Leading:** 1.4× to 1.6× for body marketing copy.

**Line length:** aim for 50–75 characters per line. Marketing text is often read more carefully than UI text and benefits from comfortable measure.

**Spacing between sections:** generous. Don't pack marketing sections tight; let them breathe.

## Anti-patterns to avoid

**Using opacity for text colors.** `color: rgba(0,0,0,0.6)` is unpredictable on colored backgrounds. Use explicit colors computed against the actual background.

**Forgetting that font weight affects perceived contrast.** Light weights at small sizes look low-contrast even when the color contrast technically passes. Use medium weights for small text.

**Designing for one mode and not the other.** Light-mode designs that haven't been verified in dark mode often fail in subtle ways: helper text becomes invisible, brand colors clash, contrast inverts incorrectly.

**Setting line-height in pixels instead of unitless multipliers.** `line-height: 24px` doesn't scale with the font size. `line-height: 1.5` does. Use unitless values for body text.

**Tracking applied uniformly across all sizes.** Tracking should vary by size — tighter at large, looser at small or all-caps.

## Cross-reference

For typeface selection, see `legibility-typeface-and-size`. For the parent principle, see `legibility`.
