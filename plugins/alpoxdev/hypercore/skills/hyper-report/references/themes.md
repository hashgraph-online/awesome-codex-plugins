# Themes

A theme is a token file. It changes colour, type, and margin; it never changes structure, and it never changes which blocks exist.

## 1. Choosing

| Theme | Look | Use for |
|---|---|---|
| `civic` (default) | Sans-serif, cool grey, blue accent, 17mm margins, 10.2pt | Business, public sector, status reports, anything that will be forwarded |
| `editorial` | Serif body, warm neutral, oxblood accent, 19mm margins, 10.4pt | Research notes, quarterly reviews, anything meant to be read at length |

Two themes is the right number. A third theme is a request to justify.

## 2. Setting it

In the source frontmatter:

```yaml
theme: "editorial"
```

Or at render time, which wins over the frontmatter:

```bash
--theme editorial
```

`--list-themes` prints what is installed.

## 3. The token set

Every theme defines these, and a new theme must define all of them or the base stylesheet's fallbacks take over.

| Token | Meaning |
|---|---|
| `--paper` | Page background |
| `--ink` | Body text |
| `--muted` | Captions, footer, secondary labels |
| `--muted-strong` | Emphasised secondary text, blockquote body |
| `--rule` | Hairlines: table rows, footer rule, heading rules |
| `--rule-strong` | Table header underline and table bottom edge |
| `--accent` | The single accent: rules, citation markers, links, callout edge |
| `--surface` | Callout and blockquote background |
| `--code-bg` | Inline code and code block background |
| `--font-body`, `--font-heading`, `--font-mono` | Font stacks |
| `--font-size`, `--line-height` | Body scale |
| `--page-margin-x`, `--page-margin-top` | Margins |

## 4. Rules a theme may not break

- **One accent colour.** A second accent turns emphasis into decoration, and then nothing is emphasised.
- **Contrast.** Body text on paper is near-black on near-white, not grey on cream. The accent is for rules and markers, not for body text at small sizes.
- **Print-safe sizes.** Body between 10pt and 11pt. A theme that needs 9pt to fit is a theme for a denser document, not a smaller one.
- **Korean font first.** Every font stack lists a Korean family before the Latin fallback, or Korean text silently renders in a fallback with different metrics and the pagination shifts.
- **No background images, no gradients, no shadows in print.** They cost ink and gain nothing on a page.

## 5. Making a new theme

Copy the closest existing theme, change the tokens, and check three pages: a dense table page, a figure page, and the cover. If the table's header rule and the footer rule are indistinguishable, the rule tokens are too close.

Then add it to `--list-themes` output by dropping the file in `assets/runtime/themes/`; the list is read from the directory.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| CSS custom properties as the theme mechanism | <https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties> |
| Korean font stacks needing a Korean family first to avoid metric shift | This package's measurement on macOS 26.2, 2026-11-13 |
| One accent colour and contrast discipline | <https://www.nngroup.com/articles/choosing-chart-types/> for the emphasis principle, applied here to document colour |