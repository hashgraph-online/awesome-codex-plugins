# UI Theme QA — reference corpus (engine-rooted)

Replacement values are **never invented and never borrowed from another
project's design system**. Every number here is one of:

1. a value Godot's own default theme defines, or
2. a value derived from those by a rule stated on this page, or
3. a constant from a published accessibility standard.

So the corpus is self-contained and reproducible: no vendored third-party data,
no toolchain, nothing to re-download.

## Engine roots

Read from Godot's default theme (`scene/theme/default_theme.cpp` in the engine
source). Verified independently against a live 4.7 editor.

| root | value | where it comes from |
|---|---|---|
| spacing base unit | **4** | `separation` for BoxContainer / VBox / HBox / Grid / Flow |
| large spacing anchor | **12** | `separation` for SplitContainer |
| container margin default | **0** | MarginContainer margins |
| base font size | **16** | `default_font_size` |
| heading anchors | **20 / 24 / 28** | Label variations `HeaderSmall/Medium/Large` (base +4 / +8 / +12) |
| engine's own step ratio | **1.25** | the first heading step, 20 ÷ 16 |

**Verify live** (needs any `Control` in the edited scene):

```bash
hera-godot eval 'get_node("<some Control>").get_theme_constant("separation","BoxContainer")'   # 4
hera-godot eval 'get_node("<some Control>").get_theme_constant("separation","HSplitContainer")' # 12
hera-godot eval 'get_node("<some Control>").get_theme_default_font_size()'                      # 16
```

---

## `spacing` — ladder (px)

Multiples of the engine's **4px base unit**. Below 32 every rung is available
(fine control is useful at UI density); above 32 the ladder thins so that
adjacent rungs stay visibly different.

```
4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64, 80, 96
```

Snap each spacing token (`theme_override_constants/separation`, `.../margin_*`)
to the nearest rung, ties → smaller. Snapping is lateral — it never inflates
macro whitespace.

## `type-scale` — ladder (px)

Rooted at the engine's `default_font_size` of 16 and the heading sizes the
engine itself defines. Above 28 the engine defines nothing, so the ladder
continues at the engine's own **1.25** ratio, rounded to the nearest integer.

```
12, 16, 20, 24, 28, 35, 44, 55, 69, 86
└── engine-defined ──┘ └── ×1.25 ──┘
```

- `16, 20, 24, 28` are the engine's base + heading sizes, used unchanged.
- `12` continues the engine's own +4 heading arithmetic one step below the base.
- `35, 44, 55, 69, 86` = repeatedly ×1.25 from 28, rounded.

**Why the ratio above 28:** a fixed +4 step is a shrinking *relative* change as
sizes grow — 12→16 is +33% and clearly visible, while 96→100 is +4% and looks
identical. Holding a constant ratio keeps every step perceptually equivalent, so
large headings stay distinguishable. Below 28 the engine's own sizes win over
the rule.

Snap each `theme_override_font_sizes/font_size` to the nearest rung, preserving
order — never collapse two hierarchy levels onto one rung.

## `color` — no palette is vendored

There is no reference palette here, deliberately. Godot's default theme defines
individual named colors with no ramp, no perceptual steps and no contrast
guarantees, so there is nothing in the engine to derive a palette *from* — and
importing another project's ramp would overwrite the project's own design with a
foreign one.

Instead:

- **Contrast repair** keeps the project's existing hue and saturation and solves
  for the lightness that satisfies the target ratio (formula below). The colour
  stays the project's; only its lightness moves.
- **Palette convergence** (out of MVP scope) converges to the project's *own*
  most-used colours or its project `Theme` — its declared palette, not an
  external one.

**Applying a colour to a Godot token.** In GDScript / `hera-godot eval`,
`Color("#0090ff")` parses hex directly. The CLI `node set --value` coercion does
**not**: it rejects both `#0090ff` and `Color("#0090ff")` and accepts only float
variant text `Color(r, g, b, a)` (0..1). Convert before enforcing — each channel
`= int(hh, 16) / 255`.

## `contrast` — WCAG thresholds and the repair formula

WCAG 2.1 SC 1.4.3 — a human-vision accessibility standard, independent of any UI
toolkit.

| target | min ratio |
|---|---|
| body text | 4.5 : 1 |
| large text (≥ 24px, or ≥ 18.66px bold) | 3.0 : 1 |
| UI component / graphical object | 3.0 : 1 |

**Relative luminance.** For each sRGB channel `c` in 0..1:

```
lin(c) = c/12.92                    if c <= 0.03928
         ((c+0.055)/1.055) ^ 2.4    otherwise
L = 0.2126*lin(R) + 0.7152*lin(G) + 0.0722*lin(B)
```

**Contrast ratio** = `(L_lighter + 0.05) / (L_darker + 0.05)`.

**Repair — solve, don't guess.** Given the background luminance `L_bg` and a
target ratio `T`, the text luminance needed is exact:

```
lighten text:  L_text  >=  T * (L_bg + 0.05) - 0.05
darken  text:  L_text  <=  (L_bg + 0.05) / T - 0.05
```

Move the text colour's lightness (hue and saturation unchanged) until its
computed `L` reaches that bound, then convert to `Color(r, g, b, a)` floats.
Never recolour the background.

**One direction is often impossible — check before choosing.** Luminance is
bounded to `0..1`, so a bound outside that range means that direction cannot
reach the target. Against a dark surface (`L_bg ≈ 0.07`) the darken bound at
4.5:1 comes out negative, i.e. no colour is dark enough; the text must be
lightened. Compute both bounds, discard any that fall outside `0..1`, and take
the feasible one. If neither is feasible the surface itself is the problem —
report it rather than emitting an unreachable colour.
