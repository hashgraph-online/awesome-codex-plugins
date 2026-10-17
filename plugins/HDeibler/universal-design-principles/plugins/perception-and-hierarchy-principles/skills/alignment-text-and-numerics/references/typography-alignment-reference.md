# Text and numeric alignment: practical reference

A reference complementing `alignment-text-and-numerics` with deeper detail on text and numeric alignment in production design.

## Reading-speed research on text alignment

Studies on reading rates (Tinker, Paterson, and many others; modern syntheses by Bringhurst and Larson) consistently show:

- **Left-aligned (ragged-right)** is fastest for body text in LTR scripts.
- **Justified (with hyphenation)** is comparable to left-aligned for narrow columns; degrades without hyphenation.
- **Justified (without hyphenation)** is slowest; "rivers" of white space disrupt reading.
- **Centered** is significantly slower for paragraphs (~30% slower); usable for short single-line content.
- **Right-aligned** is impractical for body in LTR; usable for narrow contexts.

For most product UI: left-aligned body, full stop. Centered body is a near-universal mistake when designers reach for it for "elegance."

## Tabular numerals: how and why

Most fonts ship with **proportional** numerals — each digit has slightly different width (`1` is narrow, `8` is wide, etc.). This is correct for body text where numbers appear inline. For numeric columns, it means digit positions don't quite stack.

**Tabular numerals** (also called monospaced figures) make every digit the same width. CSS:

```css
.numeric-column {
  font-variant-numeric: tabular-nums;
}
```

Most modern fonts ship with both proportional and tabular variants; the CSS property toggles which the browser uses.

For older fonts that don't support `tabular-nums`, fall back to a monospace font for numeric columns:

```css
.numeric-column {
  font-family: 'JetBrains Mono', monospace;
  font-variant-numeric: tabular-nums;
}
```

## Decimal alignment patterns

Three approaches:

### 1. Force consistent decimal precision

The simplest. Display all currency with two decimals, all percentages with one decimal:

```js
amount.toFixed(2);  // "1234.50"
percentage.toFixed(1);  // "12.5"
```

Right-align with tabular numerals; decimals naturally align.

### 2. Decimal-aligned tables (CSS)

Possible with CSS but awkward. Wrap each number in a span with the integer and decimal parts:

```html
<td class="decimal-aligned">
  <span class="integer">1,234</span><span class="decimal">.50</span>
</td>

<style>
.decimal-aligned {
  display: inline-flex;
  font-variant-numeric: tabular-nums;
}
.integer { width: 4ch; text-align: right; }
.decimal { width: 3ch; text-align: left; }
</style>
```

Works but fragile; only worth it for tables where decimal alignment really matters.

### 3. Modern CSS: `text-align: "."`

Some browsers support `text-align` on a character (like `text-align: "."`), which aligns numbers on the decimal point. Browser support is incomplete; check before relying.

## Currency display by locale

Use `Intl.NumberFormat` with `style: 'currency'`:

```js
new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
  .format(1234.5);  // "$1,234.50"

new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' })
  .format(1234.5);  // "1.234,50 €"

new Intl.NumberFormat('ja-JP', { style: 'currency', currency: 'JPY' })
  .format(1234567);  // "￥1,234,567"
```

Note: yen has no decimal places by convention. The Intl API handles per-currency conventions.

## Date alignment

Dates in tables typically left-align if formatted as text ("May 2") or right-align if numeric/ISO ("2026-05-02"). For sortable date columns, ISO format right-aligned is the safer choice — the column sorts correctly as text and aligns visually.

## Resources

- **Bringhurst, R.** *The Elements of Typographic Style* — comprehensive typographic alignment.
- **MDN: `font-variant-numeric`** — tabular-nums details and browser support.
- **Intl API on MDN** — locale-aware formatting.
- **NN/g** — articles on text alignment and reading speed.
