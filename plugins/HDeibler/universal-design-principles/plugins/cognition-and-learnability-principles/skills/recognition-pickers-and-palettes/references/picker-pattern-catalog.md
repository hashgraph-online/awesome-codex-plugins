# Picker patterns: catalog reference

A reference complementing `recognition-pickers-and-palettes` with picker-pattern detail.

## Modern command-palette implementations

Command palettes proliferated in the 2010s and 2020s. Notable implementations:

- **Sublime Text** (2008) — among the first widely-adopted; popularized cmd-shift-P.
- **VSCode** — same convention; expanded to "Quick Open" (cmd-P) for files.
- **Linear** — extended to nearly all navigation and actions.
- **Notion, GitHub, Slack, Stripe Dashboard** — all converged on cmd-K or similar.

The pattern is now an expected feature of modern productivity tools.

## Combobox accessibility

The WAI-ARIA Combobox pattern (w3.org/WAI/ARIA/apg) documents the canonical implementation:

- `role="combobox"` on the input.
- `role="listbox"` on the dropdown.
- `aria-expanded`, `aria-controls`, `aria-activedescendant` for state.
- Keyboard: arrow keys navigate, Enter selects, Esc closes.

Reach for `cmdk`, `Downshift`, `Headless UI Combobox`, `Radix Combobox` — accessible, well-tested implementations beat hand-rolled.

## Resources

- WAI-ARIA Authoring Practices: Combobox pattern.
- `cmdk` library — popular React command-palette implementation.
- NN/g articles on autocomplete and search-first interfaces.
