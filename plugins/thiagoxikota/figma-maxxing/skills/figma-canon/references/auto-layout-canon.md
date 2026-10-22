# Auto layout canon

Load before any container write. Auto layout discipline for Figma containers: mandatory on multi-child containers, Hug/Fill/Fixed rules, padding and gap variables, explicit direction, the exceptions list, and two production-tested traps with absolute coordinates and overlays.

## Mandatory rule

Every container with **more than 1 child** uses auto layout. No exceptions without documented justification.

This means: setting `layoutMode = "HORIZONTAL"` or `"VERTICAL"` AND specifying `primaryAxisSizingMode`, `counterAxisSizingMode`, `paddingTop/Right/Bottom/Left`, `itemSpacing`, `primaryAxisAlignItems`, `counterAxisAlignItems`.

## Resizing rules

| Parent | Child | Valid? |
|---|---|---|
| Hug | Hug | yes |
| Hug | Fixed | yes |
| Fill | Fill | yes |
| Fill | Hug | yes |
| Fixed | Fill | yes |
| Fixed | Hug | yes |
| **Hug** | **Fill (on same axis)** | **NO, invalid**: Hug cannot size to something that asks to Fill it |

Pattern to catch before writing: parent `primaryAxisSizingMode = "AUTO"` (Hug) with any child set to FILL on the same (primary) axis: `layoutSizingHorizontal = "FILL"` in a HORIZONTAL parent, `layoutSizingVertical = "FILL"` in a VERTICAL parent.

## Padding & gap: use spacing variables

NEVER hardcode pixel values for padding or gap when spacing variables exist. Pattern:

```javascript
// WRONG: hardcoded literals
frame.paddingTop = 16;
frame.itemSpacing = 12;

// RIGHT: bound to variables
frame.setBoundVariable('paddingTop', spacingMdVarId);
frame.setBoundVariable('itemSpacing', spacingSmVarId);
```

If spacing variables do not exist for the project: flag it to the designer for cleanup before writing.

## Direction: explicit always

- `layoutMode = "HORIZONTAL"` for rows
- `layoutMode = "VERTICAL"` for stacks
- `layoutMode = "NONE"` is the bug: usually it means the agent forgot

## Alignment: explicit

- `primaryAxisAlignItems`: `"MIN"` (start) / `"CENTER"` / `"MAX"` (end) / `"SPACE_BETWEEN"`
- `counterAxisAlignItems`: `"MIN"` / `"CENTER"` / `"MAX"` / `"BASELINE"` (text only)

Default `"MIN"`+`"MIN"` is acceptable for top-left stacks but always SET it (do not rely on the default).

## Exceptions list (auto layout NOT required)

1. **Tooltips / popovers**: absolute-positioned overlays anchored to a reference node
2. **Dropdowns**: same as tooltips
3. **Modal backdrops**: fixed-position covering, usually a single child
4. **Decorative background frames**: single-child wrappers used for backgrounds only
5. **Illustrations / complex SVG groups**: programmatic positioning is correct
6. **Single-child wrappers**: auto layout is still nice but not required if the child fills 100%

When using an exception: name the layer with a `-overlay`, `-decorative` or `-illustration` suffix so future audits can skip it.

## Resize order trap

`resize()` resets sizing modes to `FIXED`. Pattern:

```javascript
// WRONG: sizing modes reset by resize
frame.layoutSizingHorizontal = "FILL";
frame.resize(200, 100);  // resets to FIXED

// RIGHT: resize FIRST, then sizing
frame.resize(200, 100);
frame.layoutSizingHorizontal = "FILL";  // applies after resize
```

## Set sizing AFTER append

```javascript
// WRONG
const child = figma.createFrame();
child.layoutSizingHorizontal = "FILL";  // FILL needs parent context
parent.appendChild(child);  // too late

// RIGHT
const child = figma.createFrame();
parent.appendChild(child);
child.layoutSizingHorizontal = "FILL";  // resolves against parent
```

Pattern to catch: `layoutSizing*=FILL` appears in the code BEFORE `appendChild` for that node. The optional precheck hook (`hooks/figma-canon-precheck.py` at the root of this repository, opt-in, see the repository README) flags every `layoutSizing* = "FILL"` assignment as a reminder. It cannot verify the order, so check it yourself.

## Wrap (`layoutWrap`): for responsive grids

- `layoutWrap = "WRAP"` enables flex-wrap behavior.
- Use for galleries, chip sets, tag groups.
- Always paired with explicit `itemSpacing` and `counterAxisSpacing`.

## Sample correct setup

```javascript
const card = figma.createFrame();
card.name = "card-container";
card.layoutMode = "VERTICAL";
card.primaryAxisSizingMode = "AUTO";       // Hug
card.counterAxisSizingMode = "FIXED";       // Fixed width
card.primaryAxisAlignItems = "MIN";
card.counterAxisAlignItems = "MIN";
card.paddingTop = 16;
card.paddingRight = 16;
card.paddingBottom = 16;
card.paddingLeft = 16;
card.itemSpacing = 12;

page.appendChild(card);
card.layoutSizingHorizontal = "FILL";   // applies against parent

// Children
const title = figma.createText();
title.name = "card-title";
// ... font loading + characters
card.appendChild(title);
title.layoutSizingHorizontal = "FILL";
```

`page` is not defined in this fragment.

## Common bugs

| Symptom | Cause | Fix |
|---|---|---|
| Layout breaks on text edit | `counterAxisSizingMode = FIXED` and content grows | Set to `AUTO` (Hug) |
| Child overflows parent | Parent Hug + child Fill on same axis | Switch parent to Fixed or child to Hug |
| Spacing inconsistent across screens | Hardcoded pixel values | Bind to spacing variables |
| Frame does not resize with content | Missing `layoutMode` | Set HORIZONTAL or VERTICAL |
| FILL silently FIXED | Set sizing before append | Move the sizing assignment AFTER appendChild |
| `resize()` breaks layout | Reset sizing | Resize first, then sizing |
| Lone child floats to CENTER | `SPACE_BETWEEN` with a single child centers it (it does NOT fall back to MIN) | After removing a sibling from a SPACE_BETWEEN container, set `primaryAxisAlignItems='MIN'` explicitly. Hit 3 times in one session (field note, 2026-08): a row lost its pill and the remaining left-aligned group floated to the middle; only the screenshot caught it |

## Audit signals

If an audit (for example the `figma-slop-check` skill) flags any of these, the container needs fixing:

- `layoutMode = "NONE"` on a frame with more than 1 child
- Hardcoded pixel padding when spacing variables exist
- `primaryAxisSizingMode` unset (defaults to FIXED)
- Children manually positioned with `x`/`y` overrides inside an auto layout parent

## Absolute coordinates in an auto layout parent: accepted and ignored

Field note, 2026-08. Setting `x/y` on a child of a frame that has a `layoutMode` **does not throw**: the engine recalculates and stacks. An overlapping composition (glow at the back, illustration in the middle, title on top) became a column of about 2,100 px inside an 844 px frame with `clipsContent`, and only the first child was visible.

- **Telltale symptom:** the read-back LIES compared with what you wrote. `title.y = 336` read back `1716`; `footer.y = 668` read back `1995`. The deltas differ from each other, so it is not a parent offset: it is auto layout taking over.
- **Cheap detector, always use it:** after setting `x/y`, re-read and compare with the value you wrote.
- Before composing by coordinates, read `parent.layoutMode`. A composition with OVERLAP (mask, glow, vignette, badge) requires `layoutMode = 'NONE'`. When the parent has to stay auto layout, the way out is `layoutPositioning = 'ABSOLUTE'` on each overlapping child (next section).
- A screen inherited from another session may use spacer frames (children named `spacer` or similar) as auto layout spacers: their presence in the dump is the clue that the parent is NOT absolute.

## Overlay on a screen that IS auto layout: ABSOLUTE before x/y, or the sibling COLLAPSES

Field note, 2026-08. The section above covers the child that gets stacked and disappears. There is a worse and quieter kind of damage: if the parent distributes space, the new child **steals width from its siblings**. On a 1440 px screen with `layoutMode: 'HORIZONTAL'` and children `sidebar` (240 fixed) + `main` (FILL), appending 3 overlays (halo, spotlight, coach mark) left `main` with **width 1** and pushed the overlays to x=2467. The screenshot of the whole frame only looked like "the overlay disappeared"; the real damage was that the screen itself had evaporated.

- **Rule:** every overlay (spotlight, coach mark, tooltip, backdrop, dialog) gets `node.layoutPositioning = 'ABSOLUTE'` **before** you set `x`/`y`. Without it the node enters the flow. The rule applies when the parent's `layoutMode` is not `'NONE'` (third bullet below).
- **Detector, always use it after appending:** re-read the width of the sibling that was FILL (`main`, `content`, whatever it is). If it came back 1, or any value other than the expected one, this is what happened. Reading only the `x` of the overlay itself does not reveal the case where the overlay landed in the right position and the sibling is the one that shrank.
- **Do not assume from the type of screen.** In the same file, some 1440x1024 screens were `layoutMode: 'NONE'` (a map screen) and others `HORIZONTAL` (list screens such as a feed and an inbox). Check `frame.layoutMode` and only apply ABSOLUTE when it is `!== 'NONE'`.
- **A clone of an overlay that is already ABSOLUTE inherits the ABSOLUTE.** That is why a dialog cloned from another screen worked on the first try and a rectangle created from scratch in the same session did not: do not conclude from that that the parent is absolute.
