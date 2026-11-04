---
title: Typography
impact: HIGH
tags: type-scale, fonts, display, tabular-numbers, leading, casing
---

**Rule**: Use one type scale and only its steps. Give the display role a distinct weight or face, set body text for reading, and give numbers that line up or change tabular figures.

**Evidence**: Bringhurst, *The Elements of Typographic Style*, sets the measure (line length) and leading conventions. Research on reading speed (Dyson 2004) shows comprehension falls with very long or very short lines. Apple's HIG and Material 3 both ship a fixed type scale tied to text scaling.

### When Building

- **A scale, not ad-hoc sizes.** Use the platform's scale (Apple text styles, Material type roles) or a modular scale on the web. Every text element uses one of its steps.
- **Two or three type roles at most**: display (headlines, hero numbers), text (body, labels), and numeric or mono if the product shows timecodes, codes, or prices. A second font is optional.
- **The system font is a valid display face.** A heavier weight (Heavy or Black) or a different width (Expanded, Condensed) gives it character without shipping a font. Add a custom display face only when the direction calls for it (Editorial serif, a brand face).
- **Display sizes get tight leading** (about 1.0–1.15) and slightly tighter tracking where the font does not do this itself. Body text gets about 1.4–1.6 and a line length of 45–75 characters. Leave tracking alone on Apple text styles, which adjust it per size.
- **Tabular figures** for anything in a column or changing over time: prices, balances, countdowns, timecodes, frame numbers. Proportional digits make values jitter and columns misalign.
- **Sentence case** for headlines and buttons. All caps only for short labels or a deliberate expanded-display style, with added tracking.
- **One accented word** in a showcase headline at most. Never colour the whole line.
- **Keep text scalable.** Use the platform's scaling text styles or relative units so Dynamic Type and browser zoom still work.

### When Auditing

- More than six distinct font sizes, or sizes off any scale (13, 15, 17, 19, 21 mixed)
- Three or more font families
- Changing numbers in proportional figures (visible jitter, misaligned columns)
- Display text at body line height, or body text at display line height
- Fixed point sizes that ignore text scaling
- Headlines in Title Case Everywhere, or whole sentences in all caps
- A label-sized style (for example Apple's `.headline` at 17pt) used as a screen title

### Incorrect

```swift
Text("Today").font(.system(size: 22, weight: .semibold))
Text(balance).font(.system(size: 40))
```

### Correct

```swift
Text("Today").font(.largeTitle.bold())
Text(balance).font(.system(.largeTitle, weight: .heavy)).monospacedDigit()
```

### Why This Matters

Type is most of what is on a screen. A consistent scale makes the hierarchy clear without extra colour or boxes. Tabular numbers and tight display leading separate a polished product from a template.

### Alternatives

Editorial and brand-led products may use a custom display face and a separate text face. That is the second font this rule allows. Data-dense tools can use a smaller scale with more steps at the small end. Platform conventions win where they conflict: keep the platform's tracking and scaling.
