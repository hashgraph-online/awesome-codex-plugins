---
name: recognition-pickers-and-palettes
description: 'Use this skill when designing pickers, dropdowns, comboboxes, autocompletes, command palettes, or any UI that lets the user select from a known set. Trigger when picking between a free-text field and a select; when designing a command palette; when reviewing why users keep typing wrong values into autocomplete inputs. Sub-aspect of `recognition-over-recall`; read that first.'
---

# Pickers, palettes, and recognition-based selection

Selection UI is the most direct application of recognition-over-recall. Showing the user a list of valid options — visually scannable or filterable — beats requiring them to type from memory.

## The picker ladder by set size

Different selection patterns suit different option counts:

| Option count | Pattern | Notes |
|---|---|---|
| 2 | Toggle / switch | Visual either-or |
| 3–5 | Radio group / segmented | All options visible |
| 5–8 | Select dropdown | Visible on click |
| 8–20 | Grouped select | Categorical chunking helps |
| 20+ | Combobox / typeahead | Filter-as-you-type |
| 100+ | Search-first picker | Search-driven; recents augment |

Going lighter than the count permits forces unnecessary recall. Going heavier adds complexity without benefit.

## Patterns

### Combobox / typeahead

```html
<combobox label="Country">
  <input placeholder="Search countries..." />
  <listbox>
    <option>United States</option>
    <option>United Kingdom</option>
    <!-- filtered as user types -->
  </listbox>
</combobox>
```

The user types partial recall; the system filters; the user recognizes the right option. Tolerates typos with fuzzy matching.

### Command palette (cmd-K)

A palette that lists actions, navigation destinations, and search:

```
[ ⌘K opens palette ]

Search:
> Recents
  Create invoice
  Open settings
> Actions
  Search projects
  Invite teammate
> Navigation
  Go to Dashboard
  Go to Projects
```

Categorical groups + search + recents = recognition for nearly any command.

### Recents at the top of pickers

```html
<combobox label="Assignee">
  <listbox>
    <group label="Recent">
      <option>Maria Mendoza</option>
      <option>Lin Chen</option>
    </group>
    <group label="All members">
      <!-- alphabetical -->
    </group>
  </listbox>
</combobox>
```

Repeat-task speed via recents.

### Suggestions and predictions

For inputs where the system can predict likely values:

```html
<input
  name="email"
  type="email"
  autocomplete="email"
  list="email-suggestions"
/>
<datalist id="email-suggestions">
  <option value="user@example.com" />
  <option value="user@gmail.com" />
</datalist>
```

The browser surfaces matching options; the user recognizes and selects.

### Visual pickers for inherently-visual content

For colors, dates, locations, etc., visual pickers are more recognition-friendly than coded inputs:

- Color picker (visual swatch grid) beats hex code input.
- Date picker (calendar) beats text date input.
- Map picker (visual location) beats lat/long input.

## Combobox accessibility

The WAI-ARIA Combobox pattern documents the keyboard interaction:

- `Tab` enters the input.
- Arrow keys navigate the listbox.
- Enter selects the highlighted option.
- Esc closes the listbox without selection.

Reach for an accessible combobox library (Radix, React Aria, Headless UI) rather than rolling your own — focus management and ARIA are easy to get wrong.

## Anti-patterns

- **Free-text where a picker would do.** Asking users to type "United States" exactly when a dropdown could show options.
- **Empty pickers** that require typing to see anything (vs. showing options on focus).
- **Picker without filter** for sets larger than ~10 items. Scrolling 200 items is slow.
- **No recents.** Users repeatedly retype the same destinations.
- **Picker labels that don't match user vocabulary.** Showing internal names instead of friendly names.

## Heuristics

1. **The "what's available?" test.** For each input, ask: how does the user know what valid options are? If they don't, you're requiring recall.
2. **The set-size match.** Match the picker pattern to the option count.
3. **The recents-presence audit.** For pickers used repeatedly, are recents surfaced? If not, every selection is a fresh recognition task.

## Related sub-skills

- **`recognition-over-recall`** (parent).
- **`recognition-recents-and-suggestions`** — accelerating repeat tasks.
- **`hicks-law-menus`** — picker design under decision-time constraints.
- **`accessibility-operable`** — comboboxes are notorious accessibility-test surfaces.
