# Plugin API: anomalies and workarounds

Non-obvious Plugin API traps, MCP tool bugs and operational anomalies that do not fit the core or
data references. Each entry was paid for in a real file and gives the symptom, the cause when it is
known, the workaround and, where one exists, a detector you can run. Load this file when a write
hits an edge case, or when a result reads back correctly but renders wrong. It pairs with
`references/plugin-api-core.md` (always-on write rules) and `references/plugin-api-data.md`
(tokens, annotations, images). "Field note, <date>" marks an observation from production work; it
is not a pointer to `references/field-notes.md`.

**Index.** Find the symptom, then jump to the section.

**Sections and canvas placement**

- [(0,0) collisions: the find-free-space algorithm](#00-collisions-the-find-free-space-algorithm): new top-level nodes land on top of existing content.
- [clone() of a SECTION child lands at page level, not in the section](#clone-of-a-section-child-lands-at-page-level-not-in-the-section): clones sit loose on the page and look like lost frames.
- [SECTION.appendChild: reflow](#sectionappendchild-reflow): every child of the section shifts after an append.
- [A SECTION created or resized over existing content adopts it, and remove() destroys it](#a-section-created-or-resized-over-existing-content-adopts-it-and-remove-destroys-it): nodes vanish from `page.children`, then die with the section.
- [SECTION children use section-relative coordinates](#section-children-use-section-relative-coordinates): a node lands far from the x/y you set.

**Instances and components**

- [Replacement overlay on a kit instance: check the original accessory underneath](#replacement-overlay-on-a-kit-instance-check-the-original-accessory-underneath): duplicated or clipped radio, chevron or check.
- [Replacing a node inside a master wipes the override on every instance](#replacing-a-node-inside-a-master-wipes-the-override-on-every-instance): hidden slots all show at once, no error.
- [instance.resize() does not scale the children: use rescale()](#instanceresize-does-not-scale-the-children-use-rescale): icon renders as a giant blob or disappears.
- [addComponentProperty INSTANCE_SWAP wants the node id, not the key](#addcomponentproperty-instance_swap-wants-the-node-id-not-the-key): `Property value is incompatible with component property type`.
- [createComponentFromNode invalidates the source frame](#createcomponentfromnode-invalidates-the-source-frame): `The node with id "X" does not exist` when reading the old frame.
- [combineAsVariants requires COMPONENT, not FRAME](#combineasvariants-requires-component-not-frame): `A COMPONENT_SET node cannot have children of type other than COMPONENT`.
- [combineAsVariants: stale references](#combineasvariants-stale-references): the original node array is dead after combining.
- [combineAsVariants: variants keep original positions and the set does not auto-shrink](#combineasvariants-variants-keep-original-positions-and-the-set-does-not-auto-shrink): huge set, overlapping siblings, wrong default variant.
- [Instance manipulation: three gotchas](#instance-manipulation-three-gotchas): `Could not find a published component with the key X`, text lost after `resetOverrides()`.
- [mainComponent is sync-only: throws in dynamic-page](#maincomponent-is-sync-only-throws-in-dynamic-page): `Cannot call with documentAccess: dynamic-page`.
- [Instance sublayers: width and constraints also belong to the master](#instance-sublayers-width-and-constraints-also-belong-to-the-master): `resize` silently does nothing, `constraints` throws.

**Auto layout and sizing**

- [frame.resize() applies child constraints: a centered child slides](#frameresize-applies-child-constraints-a-centered-child-slides): a sheet sits a few px off axis after a widen.
- [Auto-layout frame stuck FIXED after resize()](#auto-layout-frame-stuck-fixed-after-resize): the frame does not hug and `height` reads stale.
- [Overlays on any auto-layout container flow into the layout](#overlays-on-any-auto-layout-container-flow-into-the-layout): a dim or sheet lands below the content instead of on top.
- [Caption FILL-in-HUG overflow](#caption-fill-in-hug-overflow): text wraps one word per line or overlaps the body.
- [layoutPositioning ABSOLUTE requires an auto-layout parent](#layoutpositioning-absolute-requires-an-auto-layout-parent): `Can only set layoutPositioning = ABSOLUTE if the parent node has layoutMode !== NONE`.
- [Changing layoutMode on a frame that already has auto layout freezes the dimension](#changing-layoutmode-on-a-frame-that-already-has-auto-layout-freezes-the-dimension): height stays locked, content clipped.

**Variables and paints**

- [createNodeFromSvg carries raw hex and stray wrapper fills](#createnodefromsvg-carries-raw-hex-and-stray-wrapper-fills): imported icons fail a no-raw-hex audit, unwanted box behind the icon.
- [setBoundVariableForPaint stomps explicit opacity](#setboundvariableforpaint-stomps-explicit-opacity): translucent tints come out solid.
- [Force-rebind strokes after master rebuild](#force-rebind-strokes-after-master-rebuild): strokes look right but the variable binding is gone.
- [Black translucent overlay paint can fail to composite](#black-translucent-overlay-paint-can-fail-to-composite): a scrim renders as if absent.
- [BOOLEAN_OPERATION: constraints is not assignable, and a paint binding in a later call does not resolve](#boolean_operation-constraints-is-not-assignable-and-a-paint-binding-in-a-later-call-does-not-resolve): `object is not extensible`, mark renders black.
- [Deriving the dark version of a screen: setExplicitVariableModeForCollection and the raw hex detector](#deriving-the-dark-version-of-a-screen-setexplicitvariablemodeforcollection-and-the-raw-hex-detector): what does not flip was hardcoded.

**Images, SVG, shapes and export**

- [createNodeFromSvg rejects the whole file on a duplicate attribute](#createnodefromsvg-rejects-the-whole-file-on-a-duplicate-attribute): `Failed to convert SVG file`, `Failed to fetch` from a local server.
- [createPolygon is inscribed in the ellipse of the box: no regular triangle or hexagon from the width](#createpolygon-is-inscribed-in-the-ellipse-of-the-box-no-regular-triangle-or-hexagon-from-the-width): spec looks right, shape is irregular.
- [Distorted photos: math detector and bulk fix](#distorted-photos-math-detector-and-bulk-fix): squashed or stretched image fills.
- [figma_set_image_fill: MCP tool bug](#figma_set_image_fill-mcp-tool-bug): "applied to 0 node(s)".
- [REST screenshot 403 vs plugin capture](#rest-screenshot-403-vs-plugin-capture): `403 Invalid token` on a screenshot.
- [REST /v1/images renders stale cloud state after plugin edits](#rest-v1images-renders-stale-cloud-state-after-plugin-edits): the exported PNG still shows the bug you fixed.
- [Plugin export as REST 429 bypass](#plugin-export-as-rest-429-bypass): screenshots locked out by rate limits, export to disk.

**Prototype and flows**

- [createConnector: FigJam-only](#createconnector-figjam-only): `TypeError: not a function` in a Design file, arrows for a flow graph.
- [Prototype reads: reactions live on nested nodes, flows on the page](#prototype-reads-reactions-live-on-nested-nodes-flows-on-the-page): false "no prototype" verdict, reaction left on the inner node after a wrap.

**Tooling, traversal and execution**

- [figma.mixed (Symbol): "Cannot unwrap symbol" on return](#figmamixed-symbol-cannot-unwrap-symbol-on-return): the whole `figma_execute` call fails on return.
- [findAll and findOne on a clone root match the backdrop too](#findall-and-findone-on-a-clone-root-match-the-backdrop-too): the wrong node gets mutated.
- [figma_execute timeout on bulk clone and font loads](#figma_execute-timeout-on-bulk-clone-and-font-loads): partial applies, silent duplicates, late execution.
- [getNodeByIdAsync hangs (does not throw) in large multi-page files](#getnodebyidasync-hangs-does-not-throw-in-large-multi-page-files): the call dies at the MCP timeout, `currentPage` drifts.
- [appendChild returns null: never chain on it](#appendchild-returns-null-never-chain-on-it): `cannot set property 'layoutAlign' of null`.
- [INSTANTIATE_COMPONENT: intermittent WebSocket timeout](#instantiate_component-intermittent-websocket-timeout): `timed out after 15000ms`, slot stays empty.
- [findAllWithCriteria runs on figma.currentPage: another session can switch it](#findallwithcriteria-runs-on-figmacurrentpage-another-session-can-switch-it): an audit returns zero or foreign results.
- [findAll plus remove loop dies on orphaned nodes](#findall-plus-remove-loop-dies-on-orphaned-nodes): `The node with id "X" does not exist` mid-loop.
- [Research vs empirical evidence: log contradictions](#research-vs-empirical-evidence-log-contradictions): a source claims a behavior the canvas contradicts.
- [Anti-patterns to flag (anomalies)](#anti-patterns-to-flag-anomalies): the short list to check a script against.

## (0,0) collisions: the find-free-space algorithm

- New top-level nodes default to position (0,0).
- If existing content is at (0,0), new nodes overlap silently.
- ALWAYS scan `figma.currentPage.children` for occupied positions before placing top-level nodes.
- Reposition with `node.x = X; node.y = Y;` after creation.

**Concrete scan (port of `document.find_free_space` from ai-happy-design, the project behind the `ahd-figma` server listed in `references/security-canon.md`):**

```javascript
// Find non-colliding (x,y) for a new W×H node, scanning right-then-down
// from a starting anchor with a configurable gutter.
function findFreeSpace(width, height, {anchorX = 0, anchorY = 0, gutter = 80} = {}) {
  const occupied = figma.currentPage.children.map(n => ({
    x: n.x, y: n.y, w: n.width, h: n.height,
  }));
  const collides = (x, y) => occupied.some(o =>
    x < o.x + o.w + gutter && x + width + gutter > o.x &&
    y < o.y + o.h + gutter && y + height + gutter > o.y
  );
  // Try same row as the rightmost existing node first
  const rightEdge = occupied.length
    ? Math.max(...occupied.map(o => o.x + o.w)) + gutter
    : anchorX;
  if (!collides(rightEdge, anchorY)) return {x: rightEdge, y: anchorY};
  // Otherwise drop below everything
  const bottomEdge = occupied.length
    ? Math.max(...occupied.map(o => o.y + o.h)) + gutter
    : anchorY;
  return {x: anchorX, y: bottomEdge};
}
```

Use before every `appendChild` of a top-level frame. Eliminates the "all my new frames land on top of each other" failure mode.

See also: the function reads `figma.currentPage`, which follows the user's live navigation ("getNodeByIdAsync hangs (does not throw) in large multi-page files" below).

## createConnector: FigJam-only

- `figma.createConnector` is **`undefined`** in Figma Design files (the `createConnector` property does not exist on the `figma` global). Verified 2026-05-09 and re-verified 2026-05-12: calling it gives `TypeError: not a function`.
- It works only in FigJam files.
- **Workaround for Design files:** `figma.createNodeFromSvg('<svg ...>...</svg>')` for arrow and line shapes.
- The `figma-click-flow` skill encodes this workaround.
- Never call `figma.createConnector` in a Design file. The optional precheck hook flags this pattern.
- **Better for a many-arrow flow graph (field note, 2026-06):** ONE `VECTOR` holding all edges via `setVectorNetworkAsync`, with per-vertex `strokeCap` for DIRECTION. A global `vec.strokeCap = 'ARROW_LINES'` puts an arrowhead on BOTH ends of every open path (reads as bidirectional, wrong). Instead give each segment two vertices: origin `strokeCap:'NONE'`, destination `strokeCap:'ARROW_LINES'`.
  ```javascript
  const verts=[], segs=[];
  edges.forEach(([x1,y1,x2,y2],i)=>{ verts.push({x:x1-minX,y:y1-minY,strokeCap:'NONE'}); verts.push({x:x2-minX,y:y2-minY,strokeCap:'ARROW_LINES'}); segs.push({start:2*i,end:2*i+1}); });
  const vec=figma.createVector(); vec.strokes=[paint]; vec.strokeWeight=1.5;
  await vec.setVectorNetworkAsync({vertices:verts, segments:segs, regions:[]});
  vec.x=minX; vec.y=minY;  // path coords are LOCAL: offset by bbox min, then position the node
  page.insertChild(0, vec);  // behind the boxes
  ```

## createNodeFromSvg rejects the whole file on a duplicate attribute

Field note, 2026-08.

- **Symptom:** `Failed to convert SVG file` with no further detail at all.
- **Cause:** a `fill` repeated on the same `<g>`. potrace (a bitmap-to-vector tracer) already emits `<g transform="..." fill="#000000" stroke="none">`, and concatenating a custom color without removing the existing one produced `fill="#000000" stroke="none" fill="#E5484D"`. XML does not accept a duplicate attribute, so the parse dies and nothing is imported. Figma's error does not say which attribute or which line.
- **Cheap diagnosis, run it BEFORE blaming Figma:**
  `python3 -c "import xml.etree.ElementTree as ET; ET.parse('a.svg')"`. It returns
  `duplicate attribute: line N, column M` for free.
- **Fix at the source:** `re.sub(r'\s+fill="[^"]*"', "", potrace_tag)` before appending your own.
- **Corollary for a large SVG:** do not transcribe the path by hand into `figma_execute` (it gets corrupted; the same happened with a base64 payload, field note 2026-07). Start a local server and `fetch` from inside the plugin. Requirements:
  - the CORS header `Access-Control-Allow-Origin: *` (Figma documents that plugin iframes have a `null` origin, so no specific origin can be listed);
  - AND an IPv6 socket (`socketserver` with `address_family = AF_INET6`), because the Desktop Bridge plugin manifest allows `localhost` and `localhost` resolved to `::1`. A server bound only to `127.0.0.1` returned "Failed to fetch". The field run bound `::`, which listens on every interface: bind `::1`, the IPv6 loopback, instead. If `localhost` resolves only to `127.0.0.1` on your machine, bind `127.0.0.1`. Never bind `::` or `0.0.0.0`. The server code is in `references/plugin-api-data.md`.
- See also, for the port: the manifest's `allowedDomains` lists `http://localhost:9223-9232` ("Plugin export as REST 429 bypass" below), and the bridge WebSocket itself listens inside that range, so use a port in it that nothing else is listening on.

## createNodeFromSvg carries raw hex and stray wrapper fills

Field note, 2026-06-16.

`createNodeFromSvg` returns a FRAME wrapper whose vector children keep the SVG's literal colors (`#FFFFFF`, `#E5484D`, etc): **raw hex, fails a no-raw-hex design system audit**. The wrapper FRAME can also get a stray solid fill (renders an unwanted box behind the icon).

- **Fix:** after creating, recolor every shape descendant to a bound token AND strip the wrapper fill:
  ```javascript
  if (Array.isArray(frame.fills) && frame.fills.length) frame.fills = [];  // kill stray wrapper box
  for (const d of frame.findAll(x => ['VECTOR','ELLIPSE','RECTANGLE','LINE','POLYGON','STAR','BOOLEAN_OPERATION'].includes(x.type))) {
    if (d.strokes?.length) d.strokes = [boundPaint];
    if (d.fills?.length)   d.fills   = [boundPaint];
  }
  ```
- Also: SVG vectors arrive named `Vector`/`Ellipse` (default names): rename them (`references/naming-canon.md` flags bare default names in delivered components).

## clone() of a SECTION child lands at page level, not in the section

- `node.clone()` on a frame whose parent is a SECTION places the copy as a **sibling of the section (page child)**, not inside it. Setting `.x/.y` after that positions it in page coordinates, which can visually overlap other sections while looking "placed" in your own math.
- Verified the hard way on 2026-07-17 on one project: 12 frames built via clone() all sat loose at page level for a whole session; captures looked right because bounds were checked in absolute coordinates. The designer later found a cluster of "lost frames" (and deleted 3 thinking they were junk).
- **Rule:** after ANY clone of a section child, immediately `section.appendChild(clone)` and only then set section-relative x/y. Verify with `clone.parent.name`, never with a screenshot.

## frame.resize() applies child constraints: a centered child slides

- `frame.resize(w, h)` (unlike `resizeWithoutConstraints`) recomputes the constraints of the CHILDREN. When widening a wrapper from 360 to 375, a child with a horizontal CENTER constraint slides +7.5px; the inner content you aligned by hand stays correct RELATIVE to the child, but the whole child leaves the axis. Verified 4 times in the same session (field note, 2026-07: four different bottom sheets, all at absX 8 after the widen).
- **Fix:** after resizing a wrapper, re-measure the absX of the direct children and zero it (`child.x -= absX`), or use `resizeWithoutConstraints` when a constraint-driven reflow is not wanted.
- **Signature detector** (sweep the whole file, not only the reported screen): a non-TEXT node with `width` between 350 and 376 and absX between 3 and 14 = a shifted sheet.

## Replacement overlay on a kit instance: check the original accessory underneath

- **Pattern:** a replacement overlay, meaning new controls drawn ON TOP of rows from an iOS kit (for example Android radios over iOS grouped rows). The kit row has its own radio/chevron/check as a sublayer. Repositioning the overlay without hiding the original accessory leaves the two partially overlapping = a duplicated or clipped circle in the render (field note, 2026-07: the original ellipse of the iOS grouped row at 343..361 under the Android radio at 335..355).
- **Fix:** before moving the overlay, `findAll` the VECTOR/ELLIPSE nodes with a stroke in the trailing zone of the row and set `visible=false` on the originals (a sublayer override works). Only then position the overlay with the correct margin.

## Replacing a node inside a master wipes the override on every instance

Field note, 2026-08.

- An instance override (`visible`, `characters`, `fills`) is tied to the **node id** of the child in the master. `remove()` + `insertChild()` at the same position, with the same name, creates a NEW node: every override that pointed at the old id disappears, with no error and no warning.
- Verified on a component whose instances toggle child icons with `visible`. After the ad hoc icons were swapped for library instances inside the master, **every instance showed all of its icons at once**. The master read `hidden: 0` in every variant.
- **Before replacing a node inside a master:** capture the override state of every instance (a map `node name -> visible/characters/fills`) and re-apply it afterwards. Copy `visible` from the old node to the new one along with `constraints` and paint.
- **If it is already wiped:** version history via REST solves it, but **only with a live personal access token** (`FIGMA_ACCESS_TOKEN`; in the field case it had expired, see the `figma-bridge-doctor` skill). The figma-console-mcp version tools are `figma_get_file_versions` and `figma_get_file_at_version`. Without a live token, what remains is rebuilding by a deterministic rule derived from the content (for example: the label of each instance decides which icon stays visible).
- **Closing detector:** sweep for "parent with more than one visible icon" = 0. Counting swaps proves nothing about visibility.

## SECTION.appendChild: reflow

- `section.appendChild(node)` triggers a section-wide RE-PACK:
  - Out-of-bounds children get pulled in.
  - All children shift down to make space.
- After appending to a SECTION, RE-QUERY positions on all children before continuing.
- This bites when building multi-frame sections programmatically.

## A SECTION created or resized over existing content adopts it, and remove() destroys it

Field note, 2026-08.

- A `SECTION` created (or `resize`d) over an area that already holds page nodes **absorbs those nodes as children**, silently. There is no warning, and `page.children` simply stops listing them.
- `section.remove()` after that **deletes everything that was absorbed along with it**. Verified on one production file: a scratch section created at (2150, 760) and later widened to 2380x1400 swallowed a neighboring section and 18 text boxes (headers and captions); the `remove()` of the scratch section took the 18 with it. The absorbed COMPONENTS survived as **orphans** (they resolve through `getNodeByIdAsync`, `removed === false`, `parent === null`) and could be re-adopted; the TEXT/FRAME nodes no longer resolved by id: total loss.
- The same episode left **duplicated frames** on the page (3 copies of one screen, 2 of another), apparently from atomic calls that failed but whose `clone()` stayed. After any section work, **dedupe by name** before continuing.
- **Rule:** before `createSection` or any section `resize`, scan `page.children` and pick coordinates that are provably empty (bounding-box check against every sibling). Never place a section "in a corner that looks free".
- **Before `section.remove()`**, list `section.children` and re-parent to the page whatever is not yours. Prefer emptying first and only then removing.
- Disposable scratch area: use a FRAME, not a SECTION. A frame does not adopt its neighbors.

## figma.mixed (Symbol): "Cannot unwrap symbol" on return

- `cornerRadius` (per-corner radii), `fontSize`, `fontName`, `textStyleId`, `fills` etc. return `figma.mixed` (a **Symbol**) when the node has mixed values.
- Returning a Symbol from `figma_execute` throws `Error: in postMessage: Cannot unwrap symbol`: the whole call fails, not just that field.
- **Workaround:** type-guard before returning. `typeof n.cornerRadius === 'number' ? n.cornerRadius : 'mixed['+n.topLeftRadius+',...]'`. Same for `fontSize` (`typeof === 'number'`), `fontName`/`fills` (compare `=== figma.mixed`), `textStyleId` (`typeof === 'string'`). Verified 2026-05-29 on a sheet with `topLeftRadius:28` + others 0.

## Auto-layout frame stuck FIXED after resize()

- Building a frame with `layoutMode='VERTICAL'` + `primaryAxisSizingMode='AUTO'`, then calling `resize(w, h)` to give it an initial width leaves `primaryAxisSizingMode` effectively **FIXED at the resize height**: the frame does NOT hug its children, and `.height` reads back the stale resize value (e.g. 120) right after building.
- **Workaround:** after appending ALL children, set `frame.primaryAxisSizingMode='AUTO'` **again**, THEN read `frame.height` and reposition. Re-asserting AUTO post-append forces the hug recompute. Hit 4 times in one session (filter sheets): always re-assert AUTO before reading height.

## Overlays on any auto-layout container flow into the layout

- `appendChild`/`insertChild` of a dim rect, wash, or bottom-sheet into ANY auto-layout frame (cloned screen, map container, dialog) stacks it **into the layout flow** (squeezing siblings or landing below the last child, often off-frame), NOT on top. This is not specific to clones: it bit again on a plain map container wash (field note, 2026-07).
- **Workaround:** set `overlay.layoutPositioning='ABSOLUTE'` then `overlay.x/y` + `constraints`. Absolute children float over the layout and ignore flow. Z-order = child index, so append the dim before the sheet. Verified 2026-05-29 (the dim landed at y=497, the sheet at y=1429 until set ABSOLUTE).

## findAll and findOne on a clone root match the backdrop too

- When a screen clone holds both a backdrop (the cloned UI) and a new overlay (a sheet), `cloneRoot.findAll(n => n.name === 'card')` returns cards from **both**: easy to grab `[1]` and mutate the wrong one (corrupted a backdrop card while trying to edit the sheet's card).
- **Workaround:** scope queries to the overlay subtree (`sheet.findAll(...)`, where `sheet` is the overlay frame node, resolved from its id), or filter by ancestor. Never run a name-based `findAll` on the clone root and index blindly. Verified 2026-05-29.

## REST screenshot 403 vs plugin capture

- `figma_take_screenshot` uses the REST API (`FIGMA_ACCESS_TOKEN`); a bad or expired token returns `403 Invalid token` and the screenshot fails.
- `figma_capture_screenshot` uses the plugin's `exportAsync` over the bridge: it works regardless of the REST token, and reflects the current plugin-runtime state (better for validating just-made edits).
- **Rule:** for in-session visual validation, prefer `figma_capture_screenshot`; fall back to REST only if plugin export is unavailable.
- As of figma-console-mcp v1.40.8, `figma_take_screenshot` uses the Desktop Bridge plugin when connected and falls back to the REST API, and `figma_capture_screenshot` always uses the plugin runtime and needs the bridge. The 403 in this note was observed on the REST path.

## REST /v1/images renders stale cloud state after plugin edits

Verified 3 times, 2026-07-16.

- Exports via REST (`/v1/images`, `figma_take_screenshot`) render the CLOUD-synced document, which can lag `figma_execute` edits by several minutes. The canvas (and `figma_capture_screenshot`) shows the fix; the exported PNG still has the bug. A "fixed" zip shipped with stale renders twice in one session (field note, 2026-07).
- As of figma-console-mcp v1.40.8, `figma_take_screenshot` uses the Desktop Bridge plugin when connected and falls back to the REST API. The stale renders in this note were observed on the REST path.
- **Rule:** after edit + export, validate the EXPORTED FILE (read the PNG, check pixels), not just the canvas. If stale: wait ~20s and re-export; do NOT re-edit the already-correct canvas.
- **Cheap QA gate:** compare the exported PNG dimensions vs the frame size. A 360x800 frame exporting 360x812 / 392x808 = `clipsContent=false` with a child or shadow bleeding (caught 2 frames a canvas audit missed).
- **No-op detector:** two `figma_capture_screenshot` calls returning identical `byteLength` = your edit changed nothing (e.g., hiding already-hidden nodes, moving a child that auto layout reflows back). More reliable than eyeballing compressed PNGs.
  - **False positive:** invisible-by-design edits (wrapping a text action in a transparent frame that only enlarges its clickable area, moving reactions between nodes) legitimately keep the bytes identical: verify by querying the node, not by declaring the edit failed (field note, 2026-07).
  - **Second false-positive mode:** the plugin export CACHE can return byte-identical PNGs across a REAL paint change (field note, 2026-07): bust it with a capture at a different `scale`.

## figma_execute timeout on bulk clone and font loads

- Cloning ~4 frames + ~12 `loadFontAsync` calls in a single `figma_execute` can exceed the timeout (the field note recorded 25s as the default).
- As of figma-console-mcp v1.40.8, `figma_execute` has a default timeout of 5000 ms and a maximum of 30000 ms. Trust these two numbers over the 25s in the note.
- A timed-out execute may have **partially completed** (e.g. 3 of 4 clones created but none retitled): always re-query state after a timeout instead of assuming nothing happened.
- **Workaround:** batch at most 2 to 3 clones per call, raise `timeout` to 30000 for heavier builds, and load each font family once per call (not per node).
- **Partial TEXT-batch apply (field note, 2026-07):** a timed-out call that clones a card and rewrites N text nodes can land the clone plus only the FIRST texts, leaving the rest stale from the source (hit twice in a row on a batch of cards). Protocol: after ANY timeout, re-read the target's texts and complete pointwise; for clone-and-edit jobs, split clone/position into one call and the text rewrites into 1-2 follow-up calls.
- **Dup risk (2026-05-29):** a timed-out clone-batch can create a node and leave it un-retitled (stale label), then a follow-up "make the missing one" call creates a SECOND at the same position, a silent duplicate (caught one with a stale `25` badge overlapping the correct `34`). Re-querying a `count` right after the timeout races the commit and under-reports. After any timed-out build, dedupe by **name + position** (group section children by `(x,y)`, flag same-name overlaps with negative gap) before continuing.
- **Late full execution clobbers your recovery work (field note, 2026-07):** a call that timed out at 32s (the wait the field note records; compare the 30000 ms maximum above) and verified as "nothing applied" ran to completion MINUTES later, while the agent was rebuilding incrementally. Because the script opened with an idempotence guard (`find previous section -> remove -> create`), the late run DELETED the section that had just been rebuilt by hand and recreated its own, with fresh node ids that invalidated every id the agent was holding. Protocol after a timeout: (1) do NOT immediately rebuild, (2) wait and re-inspect the parent by NAME, not by cached id, (3) if the late write landed, reconcile with it instead of racing it. Corollary: an idempotence guard that deletes-then-creates is a landmine in any script that can execute late. Prefer "find existing and update in place", or scope the delete to nodes you can prove are yours.

## getNodeByIdAsync hangs (does not throw) in large multi-page files

- Verified 2026-07-28 on an 18-page Figma file: `await figma.getNodeByIdAsync('123:456')` never resolved and the call died at the MCP timeout, while `return {ok:1}` in the same session answered in ms. A health probe of the bridge connection reported healthy (~290ms). It is a hang, not an error, so there is nothing to catch.
- **Cause:** page loading. Resolving an id whose page is not loaded forces document-wide work in `documentAccess: dynamic-page`.
- **Workaround:** resolve the page explicitly and traverse from it.
  ```js
  const page = figma.root.children.find(p => p.name === 'My Page');
  await page.loadAsync();
  const sec = page.children.find(c => c.id === '123:789');   // then walk down by id/name
  ```
- Related trap in the same family: **`figma.currentPage` follows the user's live navigation.** Mid-session the designer switched pages and every `figma.currentPage.children` lookup started returning another page's nodes (calls failed with `cannot read property 'children' of undefined`). Never anchor a multi-call build on `currentPage`; anchor on the page found by name.

## appendChild returns null: never chain on it

- `parent.appendChild(node)` returns `undefined`/`null` in the Plugin API, NOT the appended node.
- `parent.appendChild(makeThing()).layoutAlign = 'STRETCH'` throws `TypeError: cannot set property 'layoutAlign' of null` and aborts the whole `figma_execute` mid-build (leaving a half-built sheet). Verified 2026-05-29.
- **Workaround:** assign first, then append, then set: `const n = makeThing(); parent.appendChild(n); n.layoutAlign = 'STRETCH';`

## setBoundVariableForPaint stomps explicit opacity

- Binding a color variable to a paint via `figma.variables.setBoundVariableForPaint({type:'SOLID',color,opacity:0.18},'color',v)` **resets opacity to 1**: translucent tinted fills (e.g. button pills at 18%, icon badges) come out SOLID.
- Seen 2026-05-16 and again 2026-05-29 (confirm-sheet buttons rendered solid blue/red instead of at 18%).
- **Workaround:** for any translucent surface, use a RAW rgba fill (`[{type:'SOLID',color,opacity:0.18}]`) and skip the variable binding. Bind only opaque fills. (A no-raw-hex audit should tolerate raw values on these specific translucent tints: a token cannot carry the opacity. The token check in the `figma-slop-check` skill names only translucent black overlays as its exception, so it may flag these tints: mark them as raw on purpose, the way that check asks.)

## INSTANTIATE_COMPONENT: intermittent WebSocket timeout

- `figma_instantiate_component` sometimes fails with `WebSocket command INSTANTIATE_COMPONENT timed out after 15000ms`, and the slot stays empty (not a partial create). Hit twice in a row 2026-05-29 on a Toggle.
- **Workaround:** retry once; if it still times out, build the component's visual manually via `figma_execute` (e.g. draw the Toggle Off: a 50x30 track with radius 15 in the design system's track color at 0.5 opacity, plus a 26px white knob with a shadow at offset 0/1, blur 2, alpha 0.15) and note in the handoff that it stands in for the design system instance.

## instance.resize() does not scale the children: use rescale()

Field note, 2026-08.

- **Symptom:** `instance.resize(w,h)` on a library icon resizes the BOX of the instance but leaves the inner geometry at the original size. An icon from a 400x400 master "reduced" to 20x20 keeps its glyph at ~372px, which leaks as a giant black blob around it (or becomes invisible, if the parent clips). The node reads correctly (`width:20`) and only the render is wrong: `findAll` showed the icon child with `w:372` inside an instance of `w:20`.
- **Cause:** it depends on the constraints of the master. Components whose children have a SCALE constraint survive the resize, the others do not. That is why the bug shows up in SOME icons and not in others, which is misleading.
- **Fix:** `instance.rescale(target / instance.width)`. It scales the geometry too. For a non-square master (e.g. a share icon at 285x251), `rescale` preserves the proportion: `resize(16,16)` would distort it.
- **Cheap detector:** after instantiating, compare the `absoluteBoundingBox` of a descendant with that of the instance. A child larger than the parent = resize without rescale.

## addComponentProperty INSTANCE_SWAP wants the node id, not the key

Field note, 2026-08.

- The docs say to pass the component **key** as the `defaultValue` of an `INSTANCE_SWAP` property. Passing the key (40 chars, valid, read from `comp.key`) returns
  `in addComponentProperty: Property value is incompatible with component property type`
  and **aborts the whole call** (atomicity), taking with it the properties that had already been added.
- What works: `set.addComponentProperty('Brand','INSTANCE_SWAP', comp.id)`, with the **node id** (`'123:456'`). Verified by bisection: key fails, empty string fails, id passes.
- `preferredValues`, on the other hand, really does want `{type:'COMPONENT', key: comp.key}` and accepts it through `editComponentProperty`. In other words, the two ends of the SAME property use different identifiers. Do not assume symmetry.
- `instance.setProperties({[propId]: value})` also preferred the **node id** of the target variant; the key failed. Safe pattern: try the key, fall back to the id in the catch.
- **Diagnostic recipe:** when a call dies in `addComponentProperty`, do NOT re-run it unchanged. Wrap each `addComponentProperty` in a try/catch that accumulates the message in an array, and return the array. `figma_execute` is atomic only on a throw: with the errors caught, what succeeded persists and you find the culprit argument in ONE call instead of five.

## createComponentFromNode invalidates the source frame

Field note, 2026-08.

- `figma.createComponentFromNode(frame)` consumes the frame. Any later read on it (including `frame.name`) throws `in get_name: The node with id "X" does not exist` and takes down the whole call.
- It breaks the natural idiom `const c = createComponentFromNode(f); c.name = f.name;` because `f.name` is read AFTER the conversion.
- **Fix:** capture the names as strings BEFORE the conversion loop and name from the string. `const names = frames.map(f=>f.name)` first, then convert.

## combineAsVariants requires COMPONENT, not FRAME

- `figma.combineAsVariants([frames], parent)` fails with
  `Cannot move node. A COMPONENT_SET node cannot have children of type other than COMPONENT`.
- Correct flow: create each variant as a FRAME, call `figma.createComponentFromNode(frame)` on each one, and only then `combineAsVariants` with the COMPONENTs. Name each one `Prop=Value` BEFORE combining.

## combineAsVariants: stale references

- After calling `figma.combineAsVariants([nodes])`, the original `nodes` array references are STALE.
- The returned component set is the new authoritative reference.
- Re-query children via `componentSet.children` for subsequent operations.

## combineAsVariants: variants keep original positions and the set does not auto-shrink

- `combineAsVariants` does NOT re-grid the variants: each COMPONENT keeps its ORIGINAL x/y, so a set built from scattered imported frames spans their whole bounding box (huge, overlapping siblings). Verified 2026-06-16 (a 3-icon set came out 2711px wide for ~1300px of content).
- Moving the variant children inward does NOT shrink the COMPONENT_SET frame. After laying children in a grid you MUST resize explicitly: `set.resizeWithoutConstraints(contentW + 2*pad, contentH + 2*pad)`.
- Reading `set.width` in the SAME `figma_execute` right after moving children returns the STALE pre-move size. Re-read in a fresh call, or trust your computed size.
- Default variant = `set.children[0]`, but `combineAsVariants` re-sorts children alphabetically by variant value: the default can become an unwanted value (e.g. an invisible white variant whose name happens to sort first). To control it: `set.insertChild(0, desiredChild)` before arranging.

## SECTION children use section-relative coordinates

- A node parented into a `SECTION` (incl. a set placed via `combineAsVariants(nodes, section)`) has `.x/.y` RELATIVE to the section origin, not absolute. Setting `set.x = -12263` when the section sits at abs x -12363 lands the node at abs -24626 (section.x + your value). Verified 2026-06-16. Use small relative coords (e.g. 100,100) to place inside.
- Sections do NOT auto-grow to contain children placed outside their bounds; a child can sit visually outside while still being a child. Size the section manually to enclose content.

## findAllWithCriteria runs on figma.currentPage: another session can switch it

- `figma.currentPage.findAllWithCriteria(...)` audits whatever page is active. When several Claude Code sessions work on the same file, another window (or the designer) can switch the active page mid-work, so your audit silently runs on the WRONG page and returns foreign or zero results. Verified 2026-06-16 (an audit returned 0 component sets + a stray "Overlay" from another page while the real work was intact and reachable by id).
- Before any page-scoped read or audit, re-assert the page from a KNOWN node: `let p = await figma.getNodeByIdAsync(KNOWN_ID); while (p && p.type!=='PAGE') p = p.parent; await figma.setCurrentPageAsync(p);`. For writes, operate by explicit node id (page-independent).
- See also: in a large multi-page file, `getNodeByIdAsync` itself can hang ("getNodeByIdAsync hangs (does not throw) in large multi-page files" above). There, anchor on the page found by name instead.

## Distorted photos: math detector and bulk fix

Field note, 2026-08: 84 nodes.

- **Cause:** aspect-ratio distortion lives in `scaleMode: 'CROP'` with a non-uniform scale in `imageTransform`. FILL and FIT never distort.
- **Detector** (axis-aligned crops only, meaning the off-diagonal terms of the transform are zero: `T[0][1] === 0 && T[1][0] === 0`):
  `k = (node.width / node.height) / ((T[0][0] * imgW) / (T[1][1] * imgH))` with
  `T = paint.imageTransform` and
  `{width:imgW, height:imgH} = await figma.getImageByHash(paint.imageHash).getSizeAsync()`
  (cache per hash). `k` outside ~0.89-1.12 = a visibly squashed or stretched photo.
- **Bulk fix:** clone-mutate-reassign the fills, switching the paint to `scaleMode:'FILL'` and deleting `imageTransform` (center-crop preserves the proportion). 84 nodes across 3 pages, zero left on re-measurement. Caveat: FILL re-centers the crop; for a photo with critical framing, check the render afterwards.

## figma_set_image_fill: MCP tool bug

- The `figma_set_image_fill` MCP tool returns a valid `imageHash` but reports "applied to 0 node(s)" and does NOT write the fill.
- **Workaround:** take the returned hash, then apply it via `figma_execute`:

```javascript
const node = await figma.getNodeByIdAsync('NODE_ID');
const fills = JSON.parse(JSON.stringify(node.fills));
fills[0] = {type: "IMAGE", scaleMode: "FILL", imageHash: "HASH_FROM_MCP_TOOL"};
node.fills = fills;
```

## Force-rebind strokes after master rebuild

- After rebuilding a master component, instance overrides on STROKES often survive variable bindings.
- Reading `node.strokes` looks correct but the bound variable was dropped.
- After a master rebuild: recursive force-rebind, re-apply the variable binding to every node's strokes.

## Caption FILL-in-HUG overflow

- TEXT nodes with `layoutSizingHorizontal = 'FILL'` inside a HUG horizontal frame cap at badge width.
- The title wraps; absolute-positioned body content overlaps.
- **Fix:** badge + title in a HUG frame (compact). Body + triggers in a separate AUTO+FILL vertical frame.
- **Chat-bubble variant (field note, 2026-07):** TEXT with `layoutSizingHorizontal='FILL'` inside a HUG bubble collapses to one word per line (minimum width). Fix: `textAutoResize='HEIGHT'` + `resize(fixedWidth, h)` per text; never FILL a text inside a HUG container.

## Plugin export as REST 429 bypass

- When the REST API hits 429 (after ~6 batched `get_screenshot` calls, a tool of the official Figma MCP server; ~30+ min lockout), plugin export still works.
- **Pattern:** use `figma_execute` with `node.exportAsync({format: "PNG"})` returning a Uint8Array.
- **Export-to-disk pipeline (also bypasses a dead REST token):** run a tiny local HTTP server on port 9232 (the top of the bridge's port range; the bridge WebSocket can fall back to any port from 9223 to 9232, so pick another port in the range if something already listens on 9232) and `fetch('http://localhost:9232/?name=x.png', {method:'POST', body: bytes})` from inside `figma_execute`. The plugin manifest's `allowedDomains` lists `http://localhost:9223-9232`; **`127.0.0.1` fails with "Failed to fetch"**, always use `localhost` (field note, 2026-07).
  - The receiving server is not shipped in this repo. It has to handle this POST and meet the two requirements in the corollary of "createNodeFromSvg rejects the whole file on a duplicate attribute" above: the `Access-Control-Allow-Origin: *` header and a loopback bind (`::1`, or `127.0.0.1` where `localhost` resolves only there). Use the "Export-to-disk server (POST)" in `references/plugin-api-data.md`: it binds `::1`, keeps only the basename of `name`, accepts only `.png` names and PNG bytes, and writes into one folder. Stop it when the export is done.
- See `references/rate-limit-recovery.md` for the 429 lockout and the plugin export bypass. It does not cover the disk step above.
- The same path works under the Starter-plan tool-call cap of the official Figma MCP server (caps depend on seat and plan): `figma_execute` and Plugin API calls go through the bridge, not the metered remote MCP surface.

## Instance manipulation: three gotchas

Empirically discovered on one project (2026-05-25) while building a clone of a confirmation screen:

**1. `importComponentByKeyAsync` fails silently on LOCAL-only components.** The Plugin API docs show `importComponentByKeyAsync(key)` as the canonical instancing pattern, but the key parameter requires a **published library component**. For a local-only component in the current file, the call throws `"Could not find a published component with the key X"` even when the key string is correct. Fallback for local components: fetch the master via `figma.getNodeByIdAsync(masterNodeId)` and call `instance.swapComponent(master)`. Both APIs accept the same `master` object: `swapComponent` works whether the master came from a library import OR a local node lookup. (See also the instancing pattern in `references/plugin-api-core.md`, which creates a fresh instance with `master.createInstance()`.)

**2. `instance.resetOverrides()` clears ALL overrides: text included.** Easy trap: you reset to clear an unwanted fill override (e.g., a red to blue revert), then notice the text reverted to the master default. After `resetOverrides()`, **re-apply any text or prop overrides you want to keep** in the same `figma_execute` call. The reset is total: text, fills, strokes, variant choices, instance-swap targets, anything overridden returns to master defaults.

**3. Atomic block ordering: put risky calls LAST.** `figma_execute` is one transaction. If ANY call throws, the entire block reverts. So if you have 5 safe ops + 1 risky op (e.g., an `importComponentByKeyAsync` that might fail), put the risky op LAST: safe ops still run first and accumulate state. If the risky op fails, you keep the 5 ops; without that ordering, you lose everything. (Better: split risky ops into separate `figma_execute` calls. But within a single call, order matters.)

See also: `references/figma-execute-atomicity.md` records that this atomicity is best-effort (work applied before a throw can persist), and gives the cleanup step before a retry.

## Prototype reads: reactions live on nested nodes, flows on the page

- Auditing "does this file have a clickable prototype?" by reading the screen frame root gives a **false negative**: `frame.reactions` is usually empty because reactions live on nested children (buttons, cards), and flow starting points are a PAGE property (`page.flowStartingPoints`), not a node property.
- Verified 2026-06-10 on one project: a reviewing agent declared zero flows and no interactions on the home frame, while `page.flowStartingPoints` had the flow and `frame.findAll(n => n.reactions?.length)` returned 14 hotspots.
- **Correct read:** `page.flowStartingPoints` + `screen.findAll(n => n.reactions && n.reactions.length > 0)`. Never conclude from the frame root.
- Related: cloning a screen that carries a flow starting point DUPLICATES the flow entry: re-set `page.flowStartingPoints` after cloning presentation copies.
- **Wrapping a node does not move its reaction (field note, 2026-08).** When you wrap a node that already had a reaction (to give it a larger tap area), the reaction stays on the INNER node, it does not migrate to the wrapper, so the work you did before the wrap drops out of sight. Move it with `setReactionsAsync([])` on the old one + `setReactionsAsync([...])` on the new one, and re-audit targets smaller than 28 px after any hierarchy refactor.

## Black translucent overlay paint can fail to composite

Field note, 2026-07.

- **Symptom:** a scrim rect created WITH a black semi-transparent paint (`{type:'SOLID',color:{r:0,g:0,b:0},opacity:0.45}` at paint level) can render as if ABSENT, while a paint-identical sibling on another frame renders fine. Node data reads correct (fills, index, visible, opacity all right); only the composite is wrong.
- **Diagnose:** swap the fill to opaque red. If red renders, z-order is fine and the translucent paint itself is the broken one.
- **Fix:** assign a FRESH opaque paint (`fills=[{type:'SOLID',color:{r:0,g:0,b:0}}]`) and put the transparency at NODE level (`node.opacity=0.45`). Renders correctly.

## layoutPositioning ABSOLUTE requires an auto-layout parent

- Setting `layoutPositioning='ABSOLUTE'` on a child whose parent has `layoutMode==='NONE'` throws (`Can only set layoutPositioning = ABSOLUTE if the parent node has layoutMode !== NONE`) and aborts the call, leaving partials.
- **Fix:** give the parent a layoutMode (VERTICAL is fine even for image-fill covers) BEFORE appending absolute badges or overlays.

## mainComponent is sync-only: throws in dynamic-page

- `instance.mainComponent` raises `Cannot call with documentAccess: dynamic-page` in `figma_execute`, killing the whole call.
- **Fix:** use `await instance.getMainComponentAsync()`. Same family as the getVariableById/getNodeById sync traps in `references/plugin-api-core.md`.

## findAll plus remove loop dies on orphaned nodes

- Iterating a `findAll` result and removing nodes (or their parents) invalidates later entries: touching a dead node throws `The node with id "X" does not exist` mid-loop, aborting the rest. Removing a wrapper also orphans its children that are in your list.
- **Fix:** loop with `findOne` per pass (re-query, remove, repeat until no match, cap passes). Never batch-remove from a stale findAll list.

## BOOLEAN_OPERATION: constraints is not assignable, and a paint binding in a later call does not resolve

Two distinct defects on the same node type (items 1 and 2), both paid for in the same session while building brand marks with `figma.subtract` / `figma.exclude` (field note, 2026-08). Item 3 is a related auto layout exception.

**1. `node.constraints = {...}` throws `TypeError: object is not extensible`.** This applies to the `BooleanOperationNode` returned by `subtract`/`exclude`/`union`/`intersect`; ordinary nodes (ELLIPSE, RECTANGLE, VECTOR) accept it normally. The error names neither the node type nor the property, so it looks like a frozen-object error in your own code. Because atomicity is best-effort, the call dies AFTER it has already created the component and the boolean: a partial artifact is left behind.

- **Fix:** do not set `constraints` on a boolean. To scale artwork (brand mark, icon, illustration), use `instance.rescale(factor)` instead of `resize()` + SCALE constraints. `rescale` scales geometry AND stroke weight proportionally, which is the right behavior for a logo, and removes the need for constraints on every child.

**2. `setBoundVariableForPaint` on an ALREADY EXISTING boolean leaves the literal color.** Binding in a call later than the one that created the node returns `boundVariables.color` present and `bound: true` on read, but `color` stays `{r:0,g:0,b:0}` and the mark RENDERS BLACK. When the paint is created in the SAME call that creates the boolean, the color resolves correctly. The read lies: only the screenshot catches it.

```javascript
// TRAP: bound:true, but it renders black
b.fills = [figma.variables.setBoundVariableForPaint({type:'SOLID', color:{r:0,g:0,b:0}}, 'color', v)];

// Universal FIX: build the paint with the resolved value OF THE VARIABLE ITSELF, then bind
const mode = Object.keys(v.valuesByMode)[0];
const c = v.valuesByMode[mode];
let p = { type:'SOLID', color: { r: c.r, g: c.g, b: c.b } };
p = figma.variables.setBoundVariableForPaint(p, 'color', v);   // right color + binding
node.fills = [p];
```

This is not a hardcode: the color comes from the variable, not from a typed hex. The same fix applies to the OPERAND nodes of the boolean (for example `base` and `cutout`), which still exist underneath with Figma's default `#D9D9D9` and fail a no-raw-hex audit even though they are invisible.

**3. Brand artwork is a legitimate auto layout exception.** A logo component with several hand-positioned children falls under item 5 of the exception list in `references/auto-layout-canon.md` (illustrations and complex SVG groups). Document it in `component.description` instead of forcing auto layout, otherwise the next audit reopens the discussion. That exception list also asks for the `-illustration` suffix on the layer name.

## Changing layoutMode on a frame that already has auto layout freezes the dimension

Field note, 2026-08.

`primaryAxisSizingMode` and `counterAxisSizingMode` keep their value, but **the axes they name swap** when you change `layoutMode`. A HORIZONTAL header with primary=FIXED (fill on the width) and counter=AUTO (hug on the height) becomes VERTICAL and starts reading primary=FIXED as a **locked height**: the frame keeps the old height, the new content is clipped or stacked underneath, and no error appears. Measured: a 116px header that should have become 215px stayed at 116, and the next read confirmed 116, so you cannot catch it through `height`.

**Rule:** after ANY `node.layoutMode = ...` on a frame that already was auto layout, re-declare the sizing through the absolute-axis setters, which do not depend on which axis is the primary one:

```javascript
frame.layoutMode = 'VERTICAL';
frame.layoutSizingHorizontal = 'FILL';   // always these two,
frame.layoutSizingVertical   = 'HUG';    // never primary/counterAxisSizingMode after switching the mode
```

Sibling symptom: reordering children with `insertChild` in a VERTICAL frame can bring two adjacent spacers together and produce a double gap in one place and none in the other. Check `children.map(n=>n.name)` after reordering, not only the total height.

## Deriving the dark version of a screen: setExplicitVariableModeForCollection and the raw hex detector

If the fills of the screen are bound to variables of a collection with Light/Dark modes, the dark version is not painted by hand:

```javascript
const col = (await figma.variables.getLocalVariableCollectionsAsync()).find(c => c.name === '<collection name>');
frame.setExplicitVariableModeForCollection(col, col.modes.find(m => m.name === 'Dark').modeId);
```

What does NOT flip by itself is exactly what was hardcoded, and that becomes a **free audit**: sweep the frame for SOLID fills **without** `boundVariables.color` and with high luminance. That is how the edit badge of an avatar turned out to carry a raw `#FFFFFF`: in dark mode the badge stays white and the pencil (which is bound to `text-primary`) turns white on top of white and disappears.

Two details that cost a round trip:

- **A monoline icon usually paints on `strokes`, not on `fills`.** A recolor loop that only touches `node.fills` reports success (`0 changed`) and fixes nothing. Check both.
- **An icon instance with a variant property is the right path for recoloring**, not a fill override: `inst.setProperties({ Color: 'White' })` on the tab bar icons solved all four at once. Read `componentPropertyDefinitions` of the component set to learn the valid values before guessing.

## Instance sublayers: width and constraints also belong to the master

Field note, 2026-08.

The POSITION of an instance sublayer is not an override (`set_x: relative-transform`, see "Mandatory guards in batch writes" in `references/figma-execute-atomicity.md`). Width and constraints belong to the same family, and they fail in two different ways:

- `sublayer.constraints = {...}` **throws**: `This property cannot be overridden in an instance: vertical-constraint`.
- `sublayer.resize(w, h)` **does not throw and does not apply**. It reads back the old value. That is how a card resized from 153 to 200 ended up with its `bg` (RECTANGLE, MIN constraint) stuck at 153 inside a 200 card: 47 px of empty space beside the photo, without a single error in the console.

**Practical consequence:** widening a card that came from a shared component only works if ALL children have a STRETCH/SCALE constraint in the master. If one child is MIN, the only way out is to change the master (which changes every surface) or to create a variant. Do not insist on an override.

**Mandatory detector:** after `resize` on any instance sublayer, read the width back and compare it with the one you wrote. Same as the `x/y` detector in auto layout (`references/auto-layout-canon.md`, "Absolute coordinates in an auto layout parent: accepted and ignored"): the read-back is the only proof.

**Related, after a hierarchy refactor:** wrapping a node does not move its reaction to the wrapper. The rule and the fix are in "Prototype reads: reactions live on nested nodes, flows on the page" above.

## createPolygon is inscribed in the ellipse of the box: no regular triangle or hexagon from the width

Field note, 2026-09.

`figma.createPolygon()` with `pointCount` 3 or 6 and `resize(w, h)` puts the vertices on the ellipse inscribed in `w x h`, with one vertex at the top. A "triangle" from `resize(290, 251)` comes out with base 251 and height 188 (not equilateral), and a "hexagon" from `resize(251, 290)` comes out irregular. Reading `width/height` returns the BOX, not the shape, so the spec looks right and the render does not.

- **Exact shape:** `createNodeFromSvg` with the computed points (equilateral triangle with base W: `145,0 290,251.14 0,251.14`; regular hexagon with radius R: `R*0.866,0 2R*0.866,R/2 ... `), then bind the fill on the child VECTOR and set `fills = []` on the wrapper (the wrapper arrives with the SVG's fill).
- If you insist on the native polygon, the box of an equilateral triangle with base W is a CIRCLE of diameter `2W/sqrt(3)` and the base sits at `0.75` of the box height; the bounding box overshoots the shape.
- **Cheap signal (field case):** a review comment on the shape, asking whether it could be a hexagon, is what exposed that the "triangle" was not even equilateral (290x255). When a piece needs exact geometry, the native polygon does not deliver it: take the SVG route above.

## Research vs empirical evidence: log contradictions

When a research source (e.g., a research aggregator, a blog post) claims a Plugin API behavior that contradicts the empirical canon in this file, **the empirical evidence wins**. Current log:

- **`figma.createConnector` in Design files**: some sources claim it works via plugin injection. Empirically re-verified broken on 2026-05-12 in one production Design file (editorType `"figma"`): `typeof figma.createConnector === "undefined"` and `"createConnector" in figma === false`: the property is not even present on the `figma` global, it is not just throwing on call. Never call it in a Design file (the optional precheck hook flags this pattern). Workaround: `createNodeFromSvg` for arrow geometry.
- **Variables override styleId**: a secondary research summary claimed that the Variable "wins" when both are set. Empirically the two are **mutually exclusive on the same property**: setting one auto-clears the other, last-write-wins (verified 2026-05-12, both directions). See `references/plugin-api-data.md`, section "Variables and styleId: mutually exclusive on the same property", for the matrix.
- **Write ops on Desktop Bridge (`127.0.0.1:3845`)**: official Figma docs say write ops require the remote server. figma-console-mcp (a separate server from the official Figma MCP server) writes successfully via the Desktop Bridge plugin: different transport, different constraints. The "no writes on local" warning applies to the official MCP server, not to figma-console-mcp.
  As of figma-console-mcp v1.40.8, its Desktop Bridge is a WebSocket on localhost port 9223 (falling back through 9224 to 9232), not port 3845, which `references/security-canon.md` lists as the read-only official Figma desktop MCP server. The official remote server also writes through its `use_figma` tool, so figma-console-mcp is not the only write path.
- **`upload_assets` MCP tool exists**: secondary research reports omit it and falsely claim images are not writable. The tool exists on the official Figma MCP server as a separate tool, not part of `use_figma` (which is documented as having no image assets); in Claude Code, a ToolSearch for `upload_assets` returns its schema. Plugin-side `figma.createImage(bytes)` is the simpler path inside `figma_execute`.

Re-test contradictions periodically (Figma ships often). Update this section with the verification date when a re-test confirms or flips a claim.

## Anti-patterns to flag (anomalies)

- Calling `figma.createConnector` in Design files: use `createNodeFromSvg`.
- Reusing references after `combineAsVariants`: re-query from the returned component set.
- Trusting `figma_set_image_fill` to write the fill: apply the hash via `figma_execute`.
- Dropping new top-level frames at (0,0): run `findFreeSpace` first.
- Assuming stroke variable bindings survive a master rebuild: force-rebind recursively.
- Setting `constraints` on a BOOLEAN_OPERATION. Use `instance.rescale()` for artwork scaling.
- Binding a paint variable to an already-created boolean in a later call. Build the paint from `valuesByMode` first.
- Letting screenshots loop until a 429 lockout: switch to plugin `exportAsync` after the first batch fails.
