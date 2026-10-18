# Rigor checks

Load when running the Rigor lens of the `figma-slop-check` skill. Eleven checks in five groups, ordered by what a node stores: what it is bound to, which component it comes from, how auto layout sizes it, what it says, and how it renders. Each check names what to read and when it fails.

Scales, glossary and naming rules belong to the project. Read them from the file's variables and styles and from the project map (`figma-map.md`). The numbers below are placeholders that illustrate a rule. Replace them with the project's own before you judge anything.

Every finding gets a severity and an action (swap, snap or ask). Both are defined in `references/punch-list.md`.

## Read once, then judge

Collect the data in one read-only pass per screen, then run every check on that data without calling Figma again. Keep to one screen per `figma_execute` call: a full dump of a dense screen is large, and several screens in one call can hit the timeout (5000 ms by default, up to 30000 ms with `timeout`) or the output cap in [`figma-canon/references/figma-execute-atomicity.md`](../../figma-canon/references/figma-execute-atomicity.md).

Start the session with `figma_search_components`, because node ids from an earlier session may be stale. If the Bridge is down, run the `figma-bridge-doctor` skill and stop.

Return one flat record per node:

| Group | Fields |
| --- | --- |
| Identity | `id`, `name`, `type`, parent id, depth in the tree |
| Box | `width`, `height`, `opacity` |
| Auto layout | `layoutMode`, the four paddings, `itemSpacing`, `counterAxisSpacing`, `primaryAxisSizingMode`, `counterAxisSizingMode`, `layoutSizingHorizontal`, `layoutSizingVertical`, `layoutPositioning` |
| Corners | `cornerRadius`, `topLeftRadius`, `topRightRadius`, `bottomLeftRadius`, `bottomRightRadius` |
| Paint | for each fill and stroke: type, hex, paint opacity, stroke weight, and the id and name of the bound variable if there is one |
| Effects | type, radius, offset, color, spread, visible |
| Text | `characters`, `fontName`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `textStyleId` |
| Components | on INSTANCE nodes: the main component id and key, `componentProperties`, and `isDetachedFromComponent: true` when `getMainComponentAsync()` resolves to nothing. On FRAME nodes: `detachedInfo` when it is set |

Add, once per run, a `_modes` list with each variable collection and its mode names.

Three read rules from the canon:

- Store `figma.mixed` as the string `"mixed"`. A Symbol in the returned object fails the whole call.
- Resolve main components with `getMainComponentAsync()`. The sync getter throws in dynamic-page mode.
- Resolve variable names with `figma.variables.getVariableByIdAsync`, cached per id. It also finds library variables that a local listing misses.

The first two are in [`figma-canon/references/plugin-api-anomalies.md`](../../figma-canon/references/plugin-api-anomalies.md) ("figma.mixed (Symbol)" and "mainComponent is sync-only"). Bring the data back with `return`, never with `console.log` ([`figma-canon/references/plugin-api-data.md`](../../figma-canon/references/plugin-api-data.md)), and pass `timeout: 30000` for a dense screen.

Keep each run as `.figma-slop-check/runs/<YYYY-MM-DD>-<screen-slug>.json` in the project, so the next run can diff against it. Above about 100 nodes, group the records by parent before you reason over them.

Read `_modes` before you report. If it is empty, add the footer `Mode-blind run: no variable modes found (or a library-only design system).` If there are two or more modes, add `Values read in the current mode only; other modes not checked.`

## Bound or loose

### color

Read the fills and strokes, with their bindings, against `figma_get_variables`.

Fails when:

- A paint is a raw hex and a variable with that exact value exists. Name the variable it should bind to.
- A color matches no variable at all (`#FF3A3D` beside a `#FF3B30` token).
- A stroke is unbound while the fills of the same kind of element are bound.
- One concept is bound in one place and raw in another.
- The design refers to a variable or a style that the file does not have. An invented name is a failure, never a pending token.

Leave alone: a raw color on a translucent paint (paint opacity below 1). Binding a variable resets the paint opacity to 1, so a token cannot carry that tint ("setBoundVariableForPaint stomps explicit opacity" in [`figma-canon/references/plugin-api-anomalies.md`](../../figma-canon/references/plugin-api-anomalies.md)). The same goes for a translucent overlay the project keeps raw on purpose.

### text-style

Read the text fields of every TEXT node.

Fails when:

- A text has no `textStyleId` and a style with its values exists.
- One role (a row label, a body paragraph) shows up at two sizes or two weights. Example: `16/400` in one row and `16/500` in the row beside it.
- A font family outside the project's type set appears, or two families split screens of one family.
- Two body texts that should match differ in line height.

### scale

Read paddings, gaps, radii and icon sizes, and compare them with the project's scales.

Fails when:

- A padding, gap or radius is not a step of its scale. With a placeholder spacing scale of `4 8 12 16 24 32`, values such as 7, 14 and 23 fail.
- A value carries a decimal or a near miss: radius `18.5`, or a gap of `25` beside a `24` step.
- One edge is off by one where the others are symmetric: `T16 R24 B17 L24`.
- Siblings disagree: one row of a list at `T12 B12` and the next at `T14 B12`, or one gap of 12 in a list of gaps of 8.
- One class of surface uses two radii across screens (a card at 12 here and 16 there), or a primary button changes radius between screens.
- An icon is not a step of the icon scale, the same icon appears at two sizes in matching places, or an emoji or a text glyph stands in for an icon.

Leave alone: a step that exists for one component only (a gap of 6 inside a compact tag) when the project map records it; a different padding on a different kind of element (a header versus a row); a wider gap that marks a section break.

Report as ask, not as a fix: two card radii when the project has not chosen one yet, and a stroke width that varies between icons when the icon canon names a style but no width. When icons come from two sources (instances and loose vectors), list both so the designer can pick one.

## Components intact

### detached

Read `detachedInfo` on frames and the component fields on instances.

Fails when:

- A FRAME has `detachedInfo` set. It was an instance once. Name the component id or key it points to. High.
- A layer carries a component's name (`Button/Primary`, `Icon/16/Chevron-Right`) but is not an INSTANCE. High.
- An INSTANCE has no main component that resolves (`isDetachedFromComponent: true` in your record). High.
- An instance comes from a scratch or test component instead of the library one.

Report lower: the same element repeated N times with only some of the copies instances. The component exists, so the action follows the swap test in `references/punch-list.md`.

A detached copy looks right the day it is made and drifts the first time its main component changes. That is why this check is high.

### properties

Read `componentProperties` on each instance and the definitions on its main component. The read pass does not collect the definitions, so fetch them in one read-only call:

```js
const node = await figma.getNodeByIdAsync("123:456");
const main = node && node.type === "INSTANCE" ? await node.getMainComponentAsync() : null;
if (!main) return { error: "no instance or no main component" };
const owner = main.parent && main.parent.type === "COMPONENT_SET" ? main.parent : main;
return owner.componentPropertyDefinitions;
```

`figma_get_component_details` returns the same definitions.

Fails when:

- A value is outside the property's options (`State="weird"` where the options are default, hover, pressed and disabled). High.
- The instance carries a property the main component does not define. Medium.
- A property the component needs is unset. Medium.

## Auto layout sized right

### sizing

Read the size, `layoutMode` and sizing modes of each screen and of its main containers.

Fails when:

- Screens of one family have different widths (430 and 393) with no reason given.
- A frame has a fixed height where it should hug its content.
- A screen frame hugs on the counter axis where it should hold the device width, or a child that should stretch to its parent has `layoutSizingHorizontal` set to HUG instead of FILL.
- Sibling frames use different `layoutMode` values for the same job.

### collapse

Walk every FRAME and INSTANCE child of a VERTICAL auto layout parent.

Fails when:

- A child that holds content (not a button or an icon) is narrower than 70% of its parent. It probably shrank to its content instead of stretching. High.
- A node is 1px wide or 0px tall. Critical.
- A root frame is under 100px tall with no reason given. Medium.

The usual cause is the order of operations: a fill sizing set before the child is appended does not take ([`figma-canon/references/auto-layout-canon.md`](../../figma-canon/references/auto-layout-canon.md)). The fix is a write and needs approval: set `layoutSizingHorizontal` to FILL and `layoutSizingVertical` to HUG on the child.

### fill-in-hug

Read the sizing modes of text inside horizontal auto layout frames.

Fails when:

- A TEXT with `layoutSizingHorizontal` set to FILL sits in a HORIZONTAL frame that hugs its content. The frame shrinks to its narrowest sibling, and the text wraps one word per line or runs over whatever sits below it. High. See "Caption FILL-in-HUG overflow" in [`figma-canon/references/plugin-api-anomalies.md`](../../figma-canon/references/plugin-api-anomalies.md).
- A TEXT with `layoutPositioning` set to ABSOLUTE sits inside an auto layout frame. Any change in the height of its siblings breaks the alignment. Medium.
- A frame fixed on both axes holds a text long enough to clip. Medium.

After a fix, capture each fixed element on its own. Node data does not show overlap between separate nodes.

## Words

### wording

Collect the `characters` of every TEXT node, grouped by screen, and the project's glossary if it has one.

Fails when:

- A string breaks the glossary: a locked term swapped for a synonym, or a protected name translated or re-capitalized.
- One concept is written two ways across screens: singular and plural ("Order", "Orders"), case ("Order history", "Order History"), verb and adjective ("Enable", "Enabled"), tense ("Manage team", "Managing team"), a period that comes and goes, or title case on some buttons and sentence case on others.

Output the strings that vary and the form to keep. A typo inside the name of a library token, style or component stays as it is in the binding: list it for the designer and do not fix it on the canvas.

### names

List every layer name recursively and judge it by [`figma-canon/references/naming-canon.md`](../../figma-canon/references/naming-canon.md), unless the project map sets its own convention.

Fails when:

- A layer keeps a Figma default name (`Rectangle 91`, `Frame`, `Group`, `Vector`).
- A component name has no `/` (`Button-Primary` instead of `Button/Primary`), or a layer name uses `/` where it is not a variant.
- A root frame lacks the `NN-name` prefix, or repeats the device (`iPhone 14 - 01-home`).
- PascalCase appears on an internal layer, or visible text is glued into a kebab name (`btn-Add another item`).

## Pixels

### screenshot

Capture 3 to 5 representative frames with `figma_capture_screenshot`: one form, one list, one dashboard, one long multi-section screen, and the dark outlier if there is one. Five captures cost about 200 KB of context.

Fails when:

- A capture shows overlap, a collapsed element, label on label, a bad crop, a broken gradient or visible misalignment. High.
- The work is called ready without this step. Critical. Every other check reads node data, and node data does not show what renders.
