# Plugin API: core rules

Load before every write. These rules apply to almost every block of Plugin API JavaScript, whether it runs through `figma_execute` (figma-console MCP, through its Desktop Bridge plugin) or through `use_figma` (official Figma MCP server). Covered here: color floats, fills and strokes clone-mutate-reassign, font loading, async page switch, layout sizing order, atomicity, await discipline, component instancing, the multi-call write pattern, `figma.mixed` in a returned object, a sample template and `setReactionsAsync` in dynamic-page mode.

See `references/plugin-api-data.md` for variables, styles, annotations and plugin data, and `references/plugin-api-anomalies.md` for non-obvious bugs and workarounds.

## Color values

- **Plugin API uses 0-1 floats, NOT 0-255 ints.**
- `{r: 0.5, g: 0.5, b: 0.5}` = mid-gray. `{r: 128, g: 128, b: 128}` = broken.
- Convert: `r/255`, `g/255`, `b/255`.
- Opacity goes at PAINT level (`paint.opacity`), NOT in the color object (`color.a` is invalid for Solid paints).

## Fills / strokes: read-only arrays

- `node.fills` and `node.strokes` are **frozen**: they cannot be mutated in place.
- Pattern: clone, mutate the clone, reassign the array:

```javascript
const fills = JSON.parse(JSON.stringify(node.fills));
fills[0].color = {r: 0.1, g: 0.2, b: 0.3};
node.fills = fills;
```

- Same pattern for `strokes`, `effects`.

## Font loading: required before text ops

- `await figma.loadFontAsync({family: "Inter", style: "Regular"})` BEFORE:
  - Any text node creation
  - Any text property change (`characters`, `fontName`, `fontSize`, `textCase`, etc.)
  - Any `appendChild` of a text node
  - Any `setBoundVariable` on a text-bound variable
  - Any `findAll` callback that reads text
- **Verify font availability** via `figma.listAvailableFontsAsync()`: DO NOT guess style names.
- Common bug: the agent guesses `"Semibold"` when the actual style is `"Semi Bold"` (with a space).
- The optional precheck hook (`hooks/figma-canon-precheck.py` at the root of this repository, opt-in, see the repository README) flags a missing `await` on `figma.loadFontAsync`.

## Page switching: async only

- **WRONG:** `figma.currentPage = page` (sync assignment is silently broken).
- **RIGHT:** `await figma.setCurrentPageAsync(page)`.
- Never assign `figma.currentPage` synchronously. The optional precheck hook flags this pattern.

## Layout sizing: order matters

- **WRONG order:** set `layoutSizingHorizontal = 'FILL'` THEN `parent.appendChild(child)`.
- **RIGHT order:** `parent.appendChild(child)` THEN set `layoutSizing*`.
- Setting FILL before parenting silently leaves the node at FIXED.
- Also: `resize()` resets sizing modes to FIXED. Set sizing AFTER resize.

## Await every async call

- `loadFontAsync`, `setCurrentPageAsync`, `importComponentByKeyAsync`, `combineAsVariants` (some variants), `exportAsync`, `getNodeByIdAsync`, `getVariableByIdAsync`, `getVariableCollectionByIdAsync`, `setFillStyleIdAsync`, `setStrokeStyleIdAsync`, etc.
- Missing await = JS proceeds before the resource is ready = silent broken state.
- The optional precheck hook flags a missing `await` on `loadFontAsync`, `setCurrentPageAsync` and `importComponentByKeyAsync`. Check the others yourself.

## Async getters for Variables: dynamic-page mode

- In `figma_execute` and in `use_figma`, the document loads in dynamic-page mode.
- **Sync getters throw:** `figma.variables.getVariableById(id)` and `getVariableCollectionById(id)` raise "Cannot call with documentAccess: dynamic-page".
- **Use the async variants:**

```javascript
const v = await figma.variables.getVariableByIdAsync(id);
const c = await figma.variables.getVariableCollectionByIdAsync(id);
```

- Same constraint for nodes: prefer `await figma.getNodeByIdAsync(id)` over the sync `getNodeById`.

## Atomicity: depends on the path

- `figma_execute` (figma-console Desktop Bridge, the live write path) is NOT atomic: a script that fails mid-way can leave partial nodes. After any failure, sweep the parent for orphans before retrying (detail in `references/figma-execute-atomicity.md`).
- `use_figma` (official Figma MCP server) used to be described as all-or-nothing. As of 2026-10 its error response carries a `safeToRetryWithoutCanvasRead` flag. When it is `true`, fix the script and retry. When it is `false`, part of the block may have applied: read the canvas, remove what the failed run left, then retry. Never assume a rollback.
- On either path the error message is the diagnostic: read it, fix the JS, then retry. Never retry blind.

## `figma.mixed` is a SYMBOL: it breaks the `return` of figma_execute

Reading a property that may be mixed (`fontSize`, `fontName`, `layoutSizingHorizontal`, `layoutGrow`, `fills`, `strokeWeight`) and handing it back inside the returned object fails with `Error: in postMessage: Cannot unwrap symbol`, without pointing at the field. The script ran to the end and you see nothing.

Wrap every read that may be mixed before returning:

```javascript
const S = (v) => (typeof v === 'symbol' ? 'MIXED' : v);
return { fs: S(txt.fontSize), sizing: S(node.layoutSizingHorizontal) };
```

And `MIXED` in a field is useful information, not noise: that is how you find out, for example, that a price row component styles the period suffix (`/mo`) at a smaller size than the number.

## Return IDs from every call

- Every `figma_execute` block must `return { createdNodeIds: [...], ... }`.
- Subsequent calls reference these IDs as string literals (JavaScript variables do not persist across calls).
- Without IDs returned, multi-call workflows lose composition.

## Top-down with placeholders (write pattern)

- For multi-section frames: create a skeleton with placeholder children, then fill section by section across multiple `figma_execute` calls.
- Each call mutates ONE section and returns updated IDs.
- AVOID: a 50-node tree in a single call. It likely hits the 20 KB output cap (see `references/figma-execute-atomicity.md`) and is harder to debug.

## importComponentByKeyAsync: the canonical instancing pattern

The canon rule "prefer instances, never recreate", implemented. In the first comment below, `get_design_context` is a tool of the official Figma MCP server and `figma_search_components` is a tool of the figma-console MCP server.

```javascript
// 1. Get the component's key from the library
//    (visible in get_design_context output as `componentKey`,
//     or from figma_search_components MCP tool)
const componentKey = "abc123def456...";

// 2. Import the master into the current file's instance cache
const master = await figma.importComponentByKeyAsync(componentKey);

// 3. Spawn an instance: preserves library link, variants, overrides
const instance = master.createInstance();

// 4. Parent BEFORE setting FILL sizing (canon)
parent.appendChild(instance);
instance.layoutSizingHorizontal = "FILL";

// 5. Apply prop overrides via componentProperties (NOT direct text mutation)
//    Property keys have #nodeId suffixes: check instance.componentProperties first
const propKey = Object.keys(instance.componentProperties).find(k => k.startsWith("Label#"));
instance.setProperties({ [propKey]: "Save" });

return { createdNodeIds: [instance.id] };
```

**Anti-pattern:** `figma.createRectangle()` when a matching component exists. Always check `figma_search_components` first. The optional precheck hook flags raw `createRectangle` calls.

## Sample template (correct order)

```javascript
// 1. Load fonts FIRST
await figma.loadFontAsync({family: "Inter", style: "Regular"});

// 2. Switch page asynchronously
const page = figma.root.findChild(p => p.name === "Design");
await figma.setCurrentPageAsync(page);

// 3. Create node
const frame = figma.createFrame();
frame.name = "card-container";
frame.layoutMode = "VERTICAL";

// 4. Position to avoid (0,0)
frame.x = 100;
frame.y = 100;

// 5. Append BEFORE setting FILL sizing
page.appendChild(frame);
frame.layoutSizingHorizontal = "FILL";
frame.layoutSizingVertical = "HUG";

// 6. Clone fills before mutating
const fills = JSON.parse(JSON.stringify(frame.fills));
fills[0].color = {r: 0.95, g: 0.95, b: 0.95};
frame.fills = fills;

// 7. Return IDs
return { createdNodeIds: [frame.id], frameName: frame.name };
```

## Anti-patterns to flag (core)

Each line is something NOT to do, followed by the fix or the reason.

- Wrapping in an `async function() { ... }()` IIFE: the tool auto-wraps.
- Using `figma.closePlugin()`: not supported.
- Mutating `node.fills` in place: clone-mutate-reassign.
- Setting `figma.currentPage = page`: use the async setter.
- Forgetting `await` on async APIs.
- `resize()` then `layoutSizing*=FILL` without re-appending: `resize` resets sizing. Read this line together with Layout sizing: order matters above. The order that holds is `appendChild`, then `resize()`, then `layoutSizing*`; never call `resize()` after setting `layoutSizing*` (see Resize order trap in `references/auto-layout-canon.md`).
- `getVariableById` / `getVariableCollectionById` in `figma_execute`: sync getters throw in dynamic-page mode.

See `references/plugin-api-data.md` for token, style and variable anti-patterns and `references/plugin-api-anomalies.md` for non-obvious traps.

## `node.reactions = [...]` does NOT work in dynamic-page mode

Field note, 2026-08. Same family as `getVariableById`. Direct assignment fails with `Error: in set_reactions: Cannot call with documentAccess: dynamic-page. Use node.setReactionsAsync instead.`

```javascript
// WRONG
node.reactions = [{trigger:{type:'ON_CLICK'}, actions:[...]}];

// RIGHT
await node.setReactionsAsync([{
  trigger: {type:'ON_CLICK'},
  actions: [{type:'NODE', destinationId:'123:456', navigation:'NAVIGATE',
             transition:null, preserveScrollPosition:false, resetVideoPosition:false}]
}]);
```

Remember that the reaction lives in `actions` (an array), never in `action`, and that `NAVIGATE` only accepts a TOP-LEVEL frame (a child of a PAGE or of a SECTION) as destination.
