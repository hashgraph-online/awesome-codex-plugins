---
name: constraint-psychological
description: 'Use this skill when designing constraints that work through perception, expectation, and learned convention — symbols, conventions, mappings. Trigger when designing iconography, picking control conventions, or designing for behavioral predictability. Sub-aspect of `constraint`; read that first.'
---

# Psychological constraints

Psychological constraints don't physically prevent action; they make wrong actions feel obviously wrong by leveraging perception, learned convention, or perceived control-effect relationships. Weaker than physical constraints, but available where physical constraints aren't.

## The three subtypes (from the book)

### Symbols

Communicate meaning through language and imagery. Examples:

- A skull-and-crossbones on a poison bottle.
- A "WET FLOOR" sign.
- A red traffic light.
- A trash icon on a delete button.

In software UI: any icon or label that signals what an element does or what state it's in. The user reads the symbol and adjusts behavior accordingly.

### Conventions

Learned practices that the user expects systems to honor. Examples:

- "Red means stop, green means go."
- "Click the X to close."
- "Cmd-S saves; Cmd-Z undoes."
- "The hamburger icon opens a menu."

Conventions are powerful because they're transferable — a user who learned cmd-K opens the command palette in one app expects it in others. Honor conventions; deviate only with strong reason.

### Mappings

Perceived relationships between controls and their effects. Examples:

- Stovetop knobs arranged to match burner positions.
- Volume dial that turns clockwise to increase.
- Light switches near the lights they control.

In software UI: a row of action buttons whose layout matches the order of objects they affect; a slider whose direction matches the direction of value change.

```html
<!-- Mapping: + on the right increases, - on the left decreases -->
<div class="counter">
  <button>−</button>
  <span>5</span>
  <button>+</button>
</div>
```

Good mapping makes the right action feel obvious; the wrong action feels wrong.

## Symbols in software UI

### Iconography

Icons that follow established conventions:

- Trash → delete.
- Pencil → edit.
- Magnifier → search.
- Gear → settings.
- Bell → notifications.

Reusing conventional icons is psychological constraint via convention. Inventing new icons forces users to learn new symbols; only do so when no convention fits.

### Status badges

A red "ERROR" badge psychologically constrains the user from treating the item as normal. The symbol pre-empts the wrong action.

### Warning labels

Inline warnings ("This action cannot be undone") constrain the user from proceeding without consideration.

## Conventions in software UI

### Keyboard conventions

- `Cmd-S` / `Ctrl-S` saves.
- `Cmd-Z` / `Ctrl-Z` undoes.
- `Esc` closes overlays.
- `/` focuses search.
- `Cmd-K` / `Ctrl-K` opens command palette.

Honoring these conventions constrains the user to expected behavior. Violating them creates surprise.

### Mouse conventions

- Click triggers actions.
- Right-click opens context menus.
- Drag moves elements.
- Hover reveals supplementary information.

### Layout conventions

- Logo top-left links to home.
- Account menu top-right.
- Primary action bottom-right of dialogs.
- "Cancel" left of "Confirm" in dialog footers.

## Mappings in software UI

### Spatial mappings

- A list of items in vertical order; the action buttons for each row appear next to each row.
- A toolbar of formatting buttons; the buttons appear above the text they affect.

### Direction mappings

- Up arrow scrolls up.
- "Increase" controls increase what they control.
- A slider moves rightward to increase.

### Color mappings

- Brand color = primary action.
- Red = destructive.
- Green = success.

(Color mapping intersects with semantic color systems; see `color-semantic-systems`.)

## When psychological constraints fail

- **First-time users** lacking the convention. They don't know cmd-K opens the palette; the constraint doesn't apply.
- **Cross-cultural transfer** — symbols and conventions vary by region. Red means luck in some cultures, not danger.
- **Convention drift** — old conventions (the floppy-disk save icon) become opaque to younger users.
- **Override by stronger signal** — a brand redesign that breaks convention may overpower it.

When psychological constraints fail, fall back to physical constraints (block the wrong action structurally) or explicit information (explain the rules).

## Anti-patterns

- **Custom icons that violate conventions** — the user's prior knowledge becomes wrong.
- **Convention-breaking shortcuts** — Cmd-S that triggers something other than save.
- **Arbitrary mappings** — buttons that don't correspond spatially to what they affect.
- **Cultural-blind symbols** — a hand gesture icon that means OK in one culture and offense in another.

## Heuristics

1. **The convention audit.** For each interactive element, name the convention you're following or breaking. Breaking should be deliberate.
2. **The "what does this symbol mean?" check.** Show your icons to users unfamiliar with your product. If they can't tell, the symbol isn't carrying its psychological constraint.
3. **The mapping check.** For each control, do its position and direction match the effect? If not, mapping is failing.

## Related sub-skills

- **`constraint`** (parent).
- **`constraint-physical`** — the structural complement.
- **`mapping`** (cognition) — the broader principle.
- **`mimicry`** — psychological constraints often borrow from familiar systems.
- **`expectation-effect`** — convention-honoring designs match user expectations.
