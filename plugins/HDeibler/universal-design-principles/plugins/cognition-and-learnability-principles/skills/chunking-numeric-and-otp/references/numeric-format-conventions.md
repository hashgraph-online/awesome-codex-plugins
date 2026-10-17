# Numeric format conventions: cross-locale reference

A reference complementing `chunking-numeric-and-otp` with the format conventions across regions and contexts.

## Locale-specific number formatting

| Locale | Thousand sep | Decimal sep | Example |
|---|---|---|---|
| US English | `,` | `.` | 1,234,567.89 |
| UK English | `,` | `.` | 1,234,567.89 |
| German | `.` | `,` | 1.234.567,89 |
| French | space | `,` | 1 234 567,89 |
| Indian | `,` (mixed grouping) | `.` | 12,34,567.89 |
| Swiss | `'` | `.` | 1'234'567.89 |

Use `Intl.NumberFormat` to produce locale-correct formatting:

```js
new Intl.NumberFormat('de-DE').format(1234567.89);
// "1.234.567,89"
```

Hard-coding US format for an international audience is a common bug.

## Phone number conventions

Phone-number formatting varies dramatically by country. Some examples:

- US: `(555) 867-5309` or `555-867-5309`
- UK: `020 7946 0958`
- Germany: `030 12345678`
- Japan: `03-1234-5678`
- France: `01 23 45 67 89`

Rather than hard-coding any one format, use [libphonenumber](https://github.com/google/libphonenumber) (Google's library) for parsing and formatting. It handles country-code prefixes, regional norms, and edge cases.

## Credit card chunking

Most cards: 4-4-4-4 (16 digits). American Express: 4-6-5 (15 digits). Diner's Club: 4-6-4 (14 digits).

Browsers and password managers handle most of this if you use the right `autocomplete` value:

```html
<input autocomplete="cc-number" />
<input autocomplete="cc-exp" />
<input autocomplete="cc-csc" />
```

Don't reinvent; let the platform handle.

## Date format conventions

| Locale | Format | Example |
|---|---|---|
| ISO 8601 | YYYY-MM-DD | 2026-05-02 |
| US | MM/DD/YYYY | 05/02/2026 |
| UK / most of Europe | DD/MM/YYYY | 02/05/2026 |
| Japan / China | YYYY/MM/DD | 2026/05/02 |

The ambiguity between US and European formats is a notorious bug source. For internal data, prefer ISO 8601. For user display, format per locale via `Intl.DateTimeFormat`:

```js
new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium' }).format(new Date());
// "2 May 2026"
```

## Currency display

Always use `Intl.NumberFormat` with `style: 'currency'`:

```js
new Intl.NumberFormat('ja-JP', { style: 'currency', currency: 'JPY' })
  .format(1234567);
// "￥1,234,567"
```

Note: Japanese yen has no decimal places by convention. Other currencies have different fraction digits. The Intl API handles this correctly per currency.

## OTP on mobile: autofill

iOS Messages and Android can autofill OTP codes from SMS into a single input that has `autocomplete="one-time-code"`:

```html
<input type="text" inputmode="numeric" autocomplete="one-time-code" />
```

This works on the *first* such input in the form. Chunked inputs (one per digit) typically only support autofill on the first; the JS must spread the pasted/autofilled value across the other inputs.

For the best UX: detect autofill events and split the value automatically.

## Resources

- **libphonenumber** — Google's phone-number library.
- **Intl** API on MDN — comprehensive locale-aware formatting.
- **CLDR** (Unicode Common Locale Data Repository) — the authoritative source for locale conventions.
- **Apple HIG and Material Design** — both document numeric input patterns.
