# Trace the mechanism

Use the branch that answers the user's question. Inspect the real target;
avoid recreating it as a substitute for evidence.

## One visual effect

1. Locate the component and its rendered element. Follow the stylesheet or style
   definition actually attached to it, including imports and token definitions.
2. Inspect the element, `::before`, `::after`, and relevant ancestors. Record
   containing blocks, positioning, bounds, overflow, isolation and stacking
   contexts before asserting paint order. DOM order alone is insufficient.
3. Identify the contributors: backgrounds, image or SVG assets, masks, clipping,
   blend modes, opacity, filters, backdrop filters, shadows and transforms.
   Explain the job of each contributor and how they combine.
4. With an available browser, compare declared and computed values in the
   recorded state. A hit-test omits some non-interactive decorative layers and
   represents pseudo-elements by their host; do not treat it as a complete
   paint-stack inventory.
5. Check only the responsive or interactive conditions relevant to the effect.
   Record breakpoint conditions from source and actual inspected widths
   separately. A declared media query does not prove all narrower widths work.

If a layer comes from SVG, inspect its referenced primitives and asset license.
If it comes from an image or video, distinguish the media content from CSS that
positions it. For canvas or WebGL, report the available source and visible
output; do not invent shader details. Avoid calling context-creation APIs as a
probe: they can change an unused canvas's behavior. Do not execute supplied
drawing code to obtain an explanation.

## Motion and state

Trace the trigger, previous state, next state, animated properties, duration,
delay and easing from available source or an observed animation. Inspect
reduced-motion behavior when motion is part of the question. A still screenshot
cannot supply timing. A page at rest with no active animations does not prove
there is no motion; the reveal may have completed or depend on a state not
visited.

If observing a safe hover, focus or scroll transition, capture its start and
result at matching viewport and state. Do not activate a payment, booking,
deletion, email or lead action to reach an animation. Use a supplied test seam,
source analysis, or report the missing state evidence. An explanation does not
require modifying animation settings or synthesizing production events.

## Whole interface

Trace a representative user task through the relevant components. Then explain
the system that supports it, with examples rather than exhaustive token dumps:

| Concern | Evidence to connect |
|---|---|
| Structure | Route/component ownership, DOM semantics and reusable primitives |
| Layout | Container rules, grid/flex constraints, sizing and actual breakpoints |
| Tokens | Primitive → semantic role → component use, theme and state overrides |
| Type | Declared font stack, loaded font evidence, role sizes and line wrapping |
| Assets | Referenced image/font/SVG source, sizing, delivery and known rights |
| Interaction | Event/state boundary and visible feedback; no production action |

Different values do not by themselves establish inconsistency. A reused value
does not prove a deliberately designed token system. Explain the observed
pattern, qualify the design intent, and route requested quality judgments to
`suede-design`.

## Source or image only

When the runtime is unavailable, use supplied files and repository search to
follow selectors, component props, imports and relevant conditions. State which
source revision was read. Utility-like class names require their actual CSS or
configuration before asserting resolved values. Generated HTML and CSS may omit
runtime styles and inactive component branches.

For an image-only explanation, inspect the original pixels and name the visible
composition. Offer a possible mechanism only as a reconstruction hypothesis.
Report ratios or explicitly stated scale assumptions rather than treating image
pixels as CSS pixels. Sampled colors do not establish the original tokens or
full accessibility contrast; compositing, antialiasing and capture processing
may intervene. Do not identify a font or library from appearance alone.

## Evidence table

Use enough rows to support the mechanism, not every declaration:

| Claim | Source | Tier | Coverage |
|---|---|---|---|
| The decoration uses layered gradients and a blur | `hero.css:18` | Observed source | Declared styles; cascade not rendered |
| Extra bounds may keep blur edges outside the crop | `hero.css:11` and `hero.css:18` | Inferred purpose | Needs rendered bounds to confirm |
| The effect remains behind the heading at this width | Saved capture plus selector and computed styles | Observed runtime | Only the recorded width, theme and state |

Do not upgrade the last row from a source read alone. An observed rendering is
also limited to its capture; it does not certify every viewport or state.
