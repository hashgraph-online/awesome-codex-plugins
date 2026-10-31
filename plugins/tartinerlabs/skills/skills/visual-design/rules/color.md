---
title: Colour
impact: HIGH
tags: palette, accent, neutrals, tokens, dark-mode, category-colours
---

**Rule**: Build the palette from tinted neutrals, an ink colour, and one accent. Spend the accent on what the user should notice first. Keep status and category colours separate from it.

**Evidence**: Pre-attentive processing research (Treisman and Gelade 1980; Healey and Enns 2012) shows a single distinct hue is found almost instantly, and that advantage collapses as more hues compete. WCAG 2.2 SC 1.4.1 and 1.4.3 set the floor for colour-only meaning and contrast.

### When Building

- **Neutrals carry the screen.** Backgrounds, surfaces, text, and dividers make up most of the pixels. Tint them slightly: toward the accent, or toward system content the app shows but cannot restyle (maps, photos, video). Pure `#FFFFFF` on pure grey looks unchosen.
- **Ink, not black.** Use a near-black slightly tinted toward the neutrals for text and dark buttons. Use off-white for text in dark mode.
- **One accent, under about 10% of the screen**: the primary action, the selected state, or the one thing that needs attention now. When everything is accented, nothing is.
- **Category colours are content colours.** Colours that tell items apart (calendar categories, card faces, chart series, tags) appear only on the content: lines, chips, icon tiles at about 12–16% tint, or the item itself. They are never used for chrome, navigation, or selection.
- **Check token collisions.** When the accent is close to a category or status colour, a selected item reads as a category or an error. Use ink for selection and primary actions instead (`rules/actions.md`).
- **Status colours** (success, warning, error) have their own tokens and are used only for status, never as decoration.
- **Design dark mode as its own palette, not an inversion.** Build elevation from lightness steps (base → raised → raised further). Desaturate and lighten the accent slightly so it does not glow, and use off-white text, not pure white.
- **Colour comes from the content.** Artwork, photos, charts, and the user's data bring the colour. The interface around them stays neutral.
- **Name tokens by role** (`surface`, `ink`, `accent`, `category-3`), not by hue (`blue-500`), so the palette can change without renaming every use.

### When Auditing

- Three or more saturated hues competing on one screen
- The accent used on decoration, headers, and icons as well as actions
- A category colour also used for selection or the primary button
- Untinted `#FFF`, `#000`, and default greys throughout
- Dark mode made by inverting light mode (pure black surfaces, pure white text, unadjusted accent)
- Hex values hard-coded in components instead of tokens
- Contrast below WCAG AA (hand off to the `accessibility` skill)

### Incorrect

```css
.badge { background: #ec4899; }
.chip { background: #22c55e; }
.cta { background: #3b82f6; }
.selected { background: #22c55e; } /* also a category colour */
```

### Correct

```css
:root {
  --surface: oklch(97% 0.008 255);
  --ink: oklch(18% 0.02 255);
  --accent: oklch(62% 0.2 40);
  --category-3: oklch(65% 0.15 150);
}
.cta, .selected { background: var(--ink); color: var(--surface); }
.chip { background: color-mix(in oklch, var(--category-3) 14%, var(--surface)); }
```

### Why This Matters

Colour is the loudest tool in visual design and the easiest to overspend. A palette of tinted neutrals with one accent looks deliberate in every direction. When several hues are added without a reason, the primary action stops standing out and the app looks assembled from parts.

### Alternatives

A brand with an established multi-colour identity keeps it, and applies the same budget to each colour. Character-led products can carry two to four soft tints when each tint means something (mood, category, day). Data visualisation needs more hues than this. Use a tested categorical palette for charts, kept inside the chart.
