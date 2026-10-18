# Web

Semantic HTML first; ARIA only to fill gaps. The first rule of ARIA use (W3C, *Using ARIA*): if a native HTML element or attribute already has the semantics and behaviour you need, use it instead of repurposing another element with ARIA.

## Semantics

| Need | Use | Not |
|---|---|---|
| Action | `<button type="button">` | `<div onClick>` |
| Navigation | `<a href>` | `<span onClick>` / `<button>` that changes the URL |
| Page structure | `header`, `nav`, `main`, `footer`, `<h1>`–`<h6>` in order | styled `div`s |
| Form field | `<label for>` + `<input>`; `fieldset`/`legend` for groups | placeholder as label |
| Toggle | `<button aria-pressed>` or `<input type="checkbox" role="switch">` | a `div` with a class |
| Disclosure | `<details>`/`<summary>`, or `<button aria-expanded aria-controls>` | click-to-show without state |
| Dialog | `<dialog>` with `showModal()` (focus trapped, Escape closes) | a positioned `div` |

Custom widgets (combobox, tabs, menu, tree, grid) follow the WAI-ARIA Authoring Practices Guide pattern exactly — roles, states, and keyboard model: https://www.w3.org/WAI/ARIA/apg/patterns/

## Names

- Visible text is the best name; `aria-label` only for icon-only controls; `aria-labelledby` to reuse visible text
- The accessible name of a control should contain its visible label, so speech-input users can say what they see (WCAG 2.5.3)
- Decorative icons and images: `aria-hidden="true"` / `alt=""`

## Focus

- `:focus-visible` styles with at least 3:1 contrast against the background
- `scroll-padding-top` equal to any sticky header height, so focused elements are not hidden (WCAG 2.4.11)
- Single-page apps: after a route change, move focus to the new page's `<h1>` (with `tabindex="-1"`) or `main`, and update `document.title`
- `inert` on content behind a non-native modal

## Live Regions

- `role="status"` (polite) for results, saves, and progress; `role="alert"` only for urgent errors
- The region must exist in the DOM before its text changes
- `aria-busy="true"` on a region while it loads

## Motion and Contrast Preferences

- `@media (prefers-reduced-motion: reduce)` — replace large movement with fades or no animation; also check it in JavaScript animation libraries (`window.matchMedia('(prefers-reduced-motion: reduce)')`)
- `@media (prefers-contrast: more)` — strengthen borders and text where the design uses subtle contrast
- `forced-colors` mode (Windows High Contrast) — don't convey state with background colour alone; use borders and `outline`

## Testing

1. **Lint while writing** — Biome's `a11y` rule group, or `eslint-plugin-jsx-a11y`
2. **Automated checks in tests** — `@axe-core/playwright`:

   ```ts
   import AxeBuilder from "@axe-core/playwright";
   const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
   expect(results.violations).toEqual([]);
   ```

3. **Lighthouse** accessibility audit (axe-based) for a quick page score
4. **Manually** — keyboard-only through every primary flow; a screen reader (VoiceOver on macOS, NVDA on Windows); 200% zoom and 320 px width; Windows High Contrast

Automated tools catch only part of the problem. Deque's 2021 study of about 2,000 audits found automated axe testing identified about 57% of issues by volume — the rest, including most problems with meaning, names, and order, need a person.
