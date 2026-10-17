---
name: alignment-text-and-numerics
description: 'Use this skill when designing text-alignment and numeric-alignment decisions — choosing between left, right, center, and justified text; right-aligning numeric columns in tables; aligning labels relative to inputs; handling decimal alignment for currency. Trigger when laying out body content, designing tables with mixed types, or fixing alignment issues in dense data displays. Sub-aspect of `alignment`; read that first.'
---

# Text and numeric alignment

Text and numbers behave differently. Text wants to flow naturally, with predictable left edges so the eye can return to a known column. Numbers want to align by digit position so the user can compare magnitudes. Mixing them in a table requires deliberate alignment per column.

## Text alignment

### Left-aligned (the default for body)

In LTR scripts, body text should almost always be left-aligned. The reasons:

- **Predictable left edge** — the eye returns to a known x-position on each line.
- **Ragged-right edge** — variations in line length signal where each line ends.
- **No "rivers" of white space** that justified text creates.

Best for: paragraphs, descriptions, body copy, lists, captions.

### Right-aligned

Used in narrow contexts:

- **Numeric columns in tables** so digit positions stack.
- **Labels in two-column forms** (label-flush-right, input-flush-left) so the gap between label and input is consistent regardless of label length.
- **Some footer text** in mixed-direction layouts.
- **Content in RTL scripts** (Arabic, Hebrew) — the equivalent of left-aligned in LTR.

Avoid for body content in LTR scripts.

### Center-aligned

Use *sparingly* and only for short content:

- **Hero headlines** (one line, focal point).
- **Page titles** above content.
- **Button labels** (centered within the button).
- **Single-line CTAs** ("Sign up below" → button).
- **Quotations or epigraphs**.

Avoid for paragraphs of body text. Center-aligned body is significantly slower to read because each line starts at a different x-position.

### Justified (both edges flush)

Used in print where typesetting can hyphenate and adjust spacing precisely. On screens:

- **Without hyphenation**: don't. The "rivers" of white space between widely-spaced words are distracting.
- **With CSS `hyphens: auto`**: acceptable for long-form prose, particularly in narrow columns.

Most modern web design uses ragged-right (left-aligned) by default.

## Numeric alignment

### Right-align all numeric columns

Numbers should right-align so that digit positions stack:

```
        1.00
       12.50
      135.00
    9,876.50
```

The eye scans the right edge to compare magnitudes. Left-aligned, the same numbers don't compare:

```
1.00
12.50
135.00
9,876.50
```

Now the user has to read each number to compare; the columnar advantage is lost.

### Use tabular numerals (`font-variant-numeric: tabular-nums`)

Most fonts ship with proportional numerals (each digit has slightly different width — `1` is narrower than `8`). For columns of numbers, this means digit positions don't quite stack even when right-aligned. Use tabular numerals instead:

```css
.numeric-column {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
```

Now every digit occupies the same width; columns align perfectly.

### Decimal alignment

When numbers have varying decimal places, you sometimes want to align *on the decimal point* rather than the right edge. CSS doesn't make this easy; the workarounds:

- **Force consistent decimal places** ("$2.50" not "$2.5") so right-alignment serves as decimal alignment.
- **Use a span around the integer part** and another around the decimal, with explicit width on the integer part. Fragile; reserve for cases where it matters.

For most products, forcing consistent decimal places is the simpler answer.

### Currency

Display currency with locale-appropriate symbol position and separators:

```js
new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(1234.5);
// "$1,234.50"

new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(1234.5);
// "1.234,50 €"
```

Right-align currency columns; use tabular numerals.

## Label-input alignment

Three common patterns:

### Top-aligned labels (most common in vertical forms)

Label sits above input. No alignment between label and input axis (they're stacked vertically).

```html
<label for="email">Email</label>
<input id="email" type="email" />
```

Pros: simplest; works at any width; labels can be long without affecting layout.

### Right-aligned labels (label-input pairs in two columns)

Label flush-right against input flush-left. The gap between is consistent regardless of label length.

```html
<style>
  .field-row { display: grid; grid-template-columns: 8rem 1fr; gap: 12px 16px; }
  .field-row label { text-align: right; padding-top: 0.5rem; }
</style>

<div class="field-row">
  <label for="email">Email</label>
  <input id="email" />
</div>
```

Pros: scannable for dense settings; predictable column widths.
Cons: label width must accommodate the longest label; long labels look awkward right-aligned.

### Left-aligned labels (label-input pairs)

Both label and input left-aligned in their columns. The gap between label and input varies with label length, creating a slight visual ragged edge.

Pros: more relaxed; easier to read longer labels.
Cons: less scannable; the variable gap reads as messier.

For most app settings: top-aligned labels. For compact dense forms: right-aligned. Left-aligned columnar is a third choice that some prefer aesthetically.

## Anti-patterns

- **Centered body text.** Reading speed drops 30%+ for centered paragraphs.
- **Left-aligned numeric columns.** Magnitudes can't be compared.
- **Mixed proportional + tabular numerals across a single column.** Drift accumulates.
- **Inconsistent decimal places.** "$2", "$2.5", "$2.50" in the same column. Right-alignment doesn't save it.
- **Justified body text without hyphenation.** Rivers of white space.
- **Centering headers but not body** without a clear reason. The reading rhythm jumps.
- **Mixing label alignment within a form.** Some labels left, some right, some top. Each switch is a re-orientation.

## Heuristics

1. **The numeric-comparison test.** Look down a numeric column. Can you spot the largest value at a glance? If not, alignment is wrong.
2. **The reading-speed test.** Read centered body text vs. left-aligned. Notice the cognitive cost. (Then never use centered body again.)
3. **The label-alignment audit.** Across the form, are all labels aligned the same way? If not, fix.
4. **The currency precision test.** All currency in a column has the same decimal places. If "$2.5" sits next to "$1,234.00", fix the precision.

## Related sub-skills

- **`alignment`** (parent).
- **`alignment-grid-systems`** — the structural grid that text and numbers align within.
- **`legibility`** and **`readability`** — typography decisions interact with alignment.
- **`proximity-data-tables`** — table-specific alignment patterns.

## Resources

- **Bringhurst, R.** *The Elements of Typographic Style* — comprehensive reference on text alignment in typography.
- **Tufte, E.** *The Visual Display of Quantitative Information* — alignment in tabular data.
- **Material Design / Apple HIG** — both document text and numeric alignment conventions.
