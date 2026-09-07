# UI Theme QA — area rules (SSOT)

Areas split by what they are allowed to do:

| area | acts by | mutates? |
|---|---|---|
| `spacing`, `type-scale`, `color`, `contrast` | setting `theme_override_*` | **yes** — undoable `node set` |
| `containers`, `decoration` | reporting only | **no** — proposals in the report |

**Why the second row never mutates.** Both would have to delete or re-parent
nodes, and neither can be decided mechanically:

- A node that *looks* decorative may carry meaning. The plugin's own dock has a
  1px `ColorRect` that reads as a blob and is actually a divider — an automatic
  deletion would have removed real UI.
- Flattening a wrapper changes node paths, and scripts address nodes by path
  (`$HUD/UI/Layout/Side/ScoreLabel`). The skill cannot see which paths are
  referenced, so a "safe" flatten can break a scene's scripts silently.

So these two surface findings for a human to act on. They are still worth
measuring — the trigger is mechanical even though the fix is not.

Each inspector / enforcer reads **only its own area section** (context isolation
— no single context holds every rule). What counts as a replacement value comes
from [reference-corpus.md](reference-corpus.md); this file is the judgement layer
on top.

Common principle — **an undecided value is a defect; a decided one is not.**
Every tell fires on a single measurement, never on taste, and every replacement
is snapped to the corpus rather than invented.

All measurement uses existing `hera` commands (no custom tooling):
- Enumerate: `hera --ids scene tree` / `hera node find --type <Class>`
- Read tokens: `hera node get <path> --props "<a>,<b>"`
  (**type-aware — see below**)
- Read effective color: `hera eval "get_node('<path>').get_theme_color('font_color')"`
- Read geometry (runtime): `hera game ui tree --fields rect,type,path`
- Enforce (undoable): `hera node set <path> --prop "<token>" --value <v>`
- Verify render: `hera screenshot --runtime --analyze`

Godot theme-token property paths used below:
`theme_override_constants/separation`, `theme_override_constants/margin_left`
(`margin_top|right|bottom`), `theme_override_font_sizes/font_size`,
`theme_override_colors/font_color`.

> **Read tokens by node type — never sweep one token list over the whole tree.**
> A theme-override property only exists on nodes whose class defines that theme
> item, and `node get --props` **fails the entire read** if *any* requested
> property is missing on that node — it does not return the subset that exists.
> Asking a `Label` for `.../separation`, or a `HBoxContainer` for `.../margin_*`,
> is a hard error, so a naive whole-tree sweep breaks on any real mixed UI.
>
> Enumerate per class first, then request only the tokens that class defines:
>
> | token | classes that define it |
> |---|---|
> | `constants/separation` | `BoxContainer` (`HBoxContainer`, `VBoxContainer`), `SplitContainer`, `FlowContainer` |
> | `constants/h_separation`, `constants/v_separation` | `GridContainer`, and `h_separation` on `Button`/`Tree`/`ItemList` |
> | `constants/margin_*` | `MarginContainer` only |
> | `font_sizes/font_size`, `colors/font_color` | text controls — `Label`, `Button`, `LineEdit`, … |
>
> ```bash
> hera node find --type VBoxContainer     # then --props ".../separation"
> hera node find --type GridContainer     # then --props ".../h_separation,.../v_separation"
> ```
>
> A bare `hera node get <path>` (no `--props`) returns every property and is
> failure-proof, but costs ~100 properties per node — use it only to discover
> what a class supports, never for the sweep itself.

> **Enforcement order** (dependency order): `spacing` → `type-scale` → `color`
> → `contrast`. Spacing commits before type-scale, colour converges before
> contrast, and contrast runs last because it depends on the final colours.
> `containers` and `decoration` are inspected in the same pass but enforce
> nothing, so they carry no position in this order.

---

## Area `spacing` (enforcement order 1)

**Statistical default:** spacing constants are magic numbers with no declared
ladder — a spread of near-but-unequal values (`3, 6, 10, 14, 22 …`) instead of
a scale.

**Mechanical trigger:** collect every `separation` and `margin_*` override,
reading **per container class** (see the type table above — `separation` from
`BoxContainer`s, `h/v_separation` from `GridContainer`s, `margin_*` from
`MarginContainer`s only). If the count of **distinct** spacing values exceeds the
count of corpus rungs they map to — i.e. two or more distinct values snap to the
same rung, or values sit off-ladder — the ladder is undisciplined.

**Fix:** snap each spacing value to the nearest corpus rung (ties → smaller).
Do not scale macro whitespace up; snapping is lateral, not inflation.

**Escape (not a defect):** values that are already all on the corpus ladder and
self-consistent. A single off-ladder value that is a deliberate optical tweak on
one focal element is a proposal, not an automatic fix.

**check:** for each changed node, `hera node get <path> --props
"theme_override_constants/separation"` (and `margin_*`) returns a value present
in the corpus spacing ladder. Predicate = *every distinct spacing token ∈
ladder*.

## Area `type-scale` (enforcement order 2)

**Statistical default:** `font_size` overrides are a random spread with no
modular relationship (ratios like `1.42 / 1.18 / 1.60`) and off-rung values
(`17`, odd sizes).

**Mechanical trigger:** collect every `theme_override_font_sizes/font_size`.
If distinct sizes are not all on the corpus type scale, or two hierarchy levels
would collapse to one rung, the scale is undisciplined.

**Fix:** snap each size to the nearest corpus rung, **preserving order** — if two
sizes that express a hierarchy round to the same rung, push the smaller one down
a rung so the hierarchy survives. Hierarchy is size/weight/spacing, never font
swaps.

> **Resolve a collision only between the two levels that collide.** Group the
> nodes before snapping: a *hierarchy chain* is a set of text nodes whose sizes
> rank them against each other (title vs body vs caption in one panel), while a
> *peer group* is a set of controls that intentionally share one size (every
> button in a row, every cell in a grid). Snap each group to the nearest rung;
> when a collision forces one level down, move **only the colliding hierarchy
> level**, never a peer group that merely happened to share that size.
>
> Worked example — sizes `{42 cells, 22 title, 17 score, 15 status, 15 buttons}`:
> `17` and `15` both snap to `16`, so the *status* level drops to `12`. The
> buttons are a peer group, not the level below `score`, so they stay at `16`.
> Dragging them down too would shrink interactive labels for a collision that
> was never theirs.

**Escape:** sizes already all on the scale with a monotonic hierarchy.

**check:** `hera node get <path> --props
"theme_override_font_sizes/font_size"` returns a value in the corpus type scale;
distinct sizes remain strictly ordered by their prior hierarchy.

## Area `color` (enforcement order 3)

**Statistical default:** colours are typed in per node as they are needed, so a
UI ends up with several values that are the same colour to the eye but different
numbers — `Color(0.55,0.57,0.62)` here, `Color(0.54,0.58,0.63)` there — with no
single source any of them came from.

**Mechanical trigger:** collect every `theme_override_colors/*` value. Two
colours are *near-duplicates* when every channel differs by ≤ `0.04` (≈10/255),
which is below the threshold at which a difference reads as intentional. If any
near-duplicate pair exists, the palette is undecided.

**Fix:** collapse each near-duplicate cluster onto its **most-used** member —
the de-facto choice the project already made. Never introduce a colour that is
not already in the UI, and never import an outside palette: the corpus
deliberately vendors none, because the engine defines no ramp to derive one from
and a foreign ramp would overwrite the project's own design.

**Escape (not a defect):** colours sourced from **named constants or a project
`Theme`** with a role bijection — one colour ↔ one semantic role (title / body /
accent / success / error). That is a decided palette even if several values are
close. The trigger is *literal scatter with no single source*, never "uses
overrides". The plugin's own dock is exactly this case: 8 colours, all named
constants (`HERA_ICE`, `HERA_WARM_GOLD`, …), each with one role.

**check:** `hera node get <path> --props "theme_override_colors/font_color"`
returns a value that is either the cluster representative or outside every
near-duplicate cluster. Predicate = *no two distinct override colours are within
0.04 per channel*.

## Area `containers` — report only

**Statistical default:** wrappers accumulate. A container is added for a layout
reason that later moves elsewhere, and the now-inert wrapper stays.

**Mechanical trigger — the ghost wrapper:** a container with **exactly one
child** whose own layout properties cannot affect a single child. `separation`
(BoxContainer/GridContainer/FlowContainer) only applies *between* children, so
with one child it is dead. Worked example from the plugin's dock:

```
panel (MarginContainer)
└── layout (VBoxContainer, separation=14)   <- one child, so separation is inert -> ghost
    └── shell (PanelContainer)
        └── shell_margin (MarginContainer, margins 24/22)  <- one child, but margins DO apply -> not a ghost
            └── content (VBoxContainer, separation=16)
```

**Escape (not a defect):** a single-child container whose properties still act —
`MarginContainer` margins, a `PanelContainer` drawing a `StyleBox`, size flags
that actually change the child's sizing. One child alone is not the tell; the
tell is *one child **and** inert layout properties*.

**No enforcement.** Report the node path, the inert property, and the proposed
flatten. Do not re-parent or delete: node paths are how scripts address nodes,
and the skill cannot see which paths are referenced.

**check:** none — this area asserts nothing about the scene after a run.

## Area `decoration` — report only

**Statistical default:** ornament is added to fill space — a `ColorRect` behind
a panel, a `modulate` glow repeated across surfaces, emoji standing in for icons.

**Mechanical trigger:** a `ColorRect`/`TextureRect` that is not referenced by any
script, carries no text, and no sibling depends on it for layout; or the same
`modulate`/`self_modulate` tint repeated across ≥3 surfaces; or emoji in
`Label`/`Button` text where the rest of the UI uses none.

**Escape (not a defect):**

1. **A functional role** — a divider, a separator rule, a progress fill, a state
   indicator.
2. **Identity** — a logo, app mark, or brand image. It carries no *information*
   and still is not ornament.
3. **`tooltip_text` is set** — a mechanical proxy for the first two. An element
   the author bothered to describe is communicating something.

**Both escapes are load-bearing, not theoretical**, and each was found by
dry-running this rule against the plugin's own dock rather than reasoned up
front:

- its 1px `ColorRect` divider matches the "decorative blob" shape exactly and is
  a real UI element;
- its 86×86 logo `TextureRect` has no text and no layout dependents, so the
  trigger fires on it — escape 2 (and 3, since it sets `tooltip_text = "Hera"`)
  is what keeps a brand mark from being proposed for deletion.

**No enforcement.** Report the candidate and why it looked decorative. Deleting
a node on a shape-match is how a real element gets removed; a human decides.

**check:** none — this area asserts nothing about the scene after a run.

## Area `contrast` (enforcement order 4)

**Statistical default:** text color chosen for looks, contrast against its
surface never checked.

**Mechanical trigger:** for each text Control, read the **effective** font color
and its background surface color, compute WCAG contrast. Fail if below the
corpus threshold for that text's size (body 4.5:1; large ≥24px or ≥18.66px bold
3.0:1).

- Effective font color: `hera eval "get_node('<path>').get_theme_color('font_color')"`
  (the override property alone can be empty while the theme still paints it).
- Background: the nearest ancestor with a painted `StyleBox` — read via
  `hera eval "get_node('<panel>').get_theme_stylebox('panel').bg_color"`, else
  the effective panel/root background.

**Fix:** keep the text colour's hue and saturation and **solve** for the
lightness that meets the threshold — the corpus gives the exact bound
(`L_text >= T*(L_bg+0.05)-0.05` to lighten). Do not guess a colour and do not
recolour the background. Enforce with `node set --value "Color(r, g, b, a)"`
(float 0..1) — the CLI rejects bare `#hex` and `Color("#hex")`.

**Escape:** pair already ≥ threshold. This check is objective — no taste escape.

**check:** recomputed WCAG ratio for the pair ≥ the corpus threshold for that
text size.

---

## Finding schema (all areas)

Each inspector writes `findings-<area>.md`, one entry per finding. The `check`
is a **re-measurable predicate** (a `hera` command + comparison), never a status
word — enforcers and re-inspectors recompute it from the live editor every time.

```
- id: <area>-<slug>            # e.g. spacing-off-ladder
  problem: <one line>
  evidence: <live measurement — node path + value(s) read via hera>
  fix: <mechanical change — which theme_override token, snapped to which rung>
  check: <hera command + predicate that returns true/false from source>
  order: spacing|type-scale|color|contrast
```

Report-only areas (`containers`, `decoration`) use the same entry minus `order`,
and write `proposal:` where an enforcing area writes `fix:`. They carry no
`check`, because they change nothing for a re-inspection to verify — say so
explicitly rather than inventing a predicate that always passes.

**A check is a predicate, not a status.** Never record "done" as text. An
enforcer applies the fix only where `check` is currently false; a fresh
re-inspector recomputes the same `check`. This is what blocks the "trust the
earlier note and silently skip" failure.

## Inviolable

Copy, information architecture, and node order are never changed — only theme
tokens. Snapping spacing/type/colour is not a redesign.

This is why `containers` and `decoration` report instead of enforce: their fixes
are exactly the structural edits this line rules out. If that ever changes it
must be an explicit opt-in with its own flag, not a quiet widening of what a
default run is allowed to do.
