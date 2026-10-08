# Field notes

Recent notes from production work that have not yet been folded into the themed reference files
(`references/plugin-api-core.md`, `references/plugin-api-data.md`,
`references/plugin-api-anomalies.md`, `references/figma-execute-atomicity.md`). Read the themed
files first. Each note here gives the symptom, the cause, the fix and the month it was recorded.

Tool names are figma-console MCP tools unless a note says the tool belongs to the official Figma
MCP server. A few notes record behavior that differs from a themed file. They say so, and both
observations stand.

**Index.** Find the symptom, then jump to the note.

**Sandbox and timeouts**

- [Sequential `await loadFontAsync` in a loop hangs the sandbox](#sequential-await-loadfontasync-in-a-loop-hangs-the-sandbox): the script hangs after 5 to 7 font loads.
- [`setTimeout` did not fire through the figma-console bridge](#settimeout-did-not-fire-through-the-figma-console-bridge): a `Promise.race` timeout guard protected nothing. Figma's typings declare `setTimeout`; cause not established.
- [`createAutoLayout`, `node.query` and `node.set` are not Plugin API](#createautolayout-nodequery-and-nodeset-are-not-plugin-api): `TypeError: not a function`.
- [`getRangeAllFontNames` in a loop hangs the sandbox](#getrangeallfontnames-in-a-loop-hangs-the-sandbox): a text script dies on the third node.
- [A script that runs past the execute ceiling freezes the sandbox for every session](#a-script-that-runs-past-the-execute-ceiling-freezes-the-sandbox-for-every-session): the bridge stops answering for everyone.
- [`figma_execute` with `fileKey` on a background file is throttled](#figma_execute-with-filekey-on-a-background-file-is-throttled): "Unable to establish connection" at 10 s.
- [An instance sublayer id fails with a fake network error](#an-instance-sublayer-id-fails-with-a-fake-network-error): "check your internet connection" with a normal network.
- [End deep reads with `return JSON.stringify(out)`](#end-deep-reads-with-return-jsonstringifyout): `Cannot unwrap symbol` on return.

**Instances and components**

- [An instance cannot receive children, and a cross-page clone stays on the source page](#an-instance-cannot-receive-children-and-a-cross-page-clone-stays-on-the-source-page): "New parent is an instance", a stray duplicate on another page.
- [Configure a nested instance only after inserting it into the slot](#configure-a-nested-instance-only-after-inserting-it-into-the-slot): `findAll callback crashed: ... does not exist`.
- [A TEXT component property has one default value per component set](#a-text-component-property-has-one-default-value-per-component-set): editing one variant's text changes every variant.
- [Switching a variant resets the icon to the new variant's default](#switching-a-variant-resets-the-icon-to-the-new-variants-default): wrong icon after a `Selected` switch.

**Vectors**

- [Mirrored vectors flip when cloned and repositioned](#mirrored-vectors-flip-when-cloned-and-repositioned): an icon upside down while every measurement passes.
- [`vectorPaths` rejects the arc command](#vectorpaths-rejects-the-arc-command): "Invalid command at A", orphan VECTOR on the page.

**Sections and layout**

- [Page coordinates written to a SECTION child land far away and can move the section](#page-coordinates-written-to-a-section-child-land-far-away-and-can-move-the-section): screens thousands of px away, no error.
- [A section created through the API did not adopt the nodes underneath](#a-section-created-through-the-api-did-not-adopt-the-nodes-underneath): `children` empty after `createSection`.
- [`maxHeight` inherited from a clone blocks hug](#maxheight-inherited-from-a-clone-blocks-hug): the height does not change under HUG.
- [A hug sweep shrinks cards that should fill a horizontal row](#a-hug-sweep-shrinks-cards-that-should-fill-a-horizontal-row): one card shorter than its row.
- [Rebuilding content inside an existing auto layout frame stacks the new children](#rebuilding-content-inside-an-existing-auto-layout-frame-stacks-the-new-children): children land below the photo.
- [Auto layout height read in the same call is stale](#auto-layout-height-read-in-the-same-call-is-stale): a sibling lands across the body text.
- [Lists with interleaved separators: move or clone the separator with the item](#lists-with-interleaved-separators-move-or-clone-the-separator-with-the-item): double or missing hairlines.

**Prototype**

- [NAVIGATE needs a top-level frame on the same page](#navigate-needs-a-top-level-frame-on-the-same-page): "destinations must be a different top-level frame on the same page".
- [Re-pointing a reaction: write `actions`, not `action`](#re-pointing-a-reaction-write-actions-not-action): `success: true` and the old destination.

**Variables and paints**

- [A SECTION fill bound to a variable renders the base color you passed](#a-section-fill-bound-to-a-variable-renders-the-base-color-you-passed): new sections render black.
- [`setBoundVariableForPaint` drops paint opacity: bind first, set opacity after](#setboundvariableforpaint-drops-paint-opacity-bind-first-set-opacity-after): a tinted chip turns solid.
- [Writes under a locked ancestor did not take through the figma-console bridge](#writes-under-a-locked-ancestor-did-not-take-through-the-figma-console-bridge): a few binds out of thousands did not take. Figma's typings say `locked` does not block plugin writes; cause not established.
- [Contrast per mode: resolve both colors through their bindings](#contrast-per-mode-resolve-both-colors-through-their-bindings): a pair passes in light mode and fails in dark mode.

**Images**

- [An uploaded image that no layer uses is discarded](#an-uploaded-image-that-no-layer-uses-is-discarded): `getImageByHash` returns `null` hours later.
- [Image bytes must not pass through the model](#image-bytes-must-not-pass-through-the-model): `Invalid base64 string`, a subagent stuck emitting base64.
- [`upload_assets` writes the fill in the cloud, and Figma Desktop stays stale until the file is reopened](#upload_assets-writes-the-fill-in-the-cloud-and-figma-desktop-stays-stale-until-the-file-is-reopened): Desktop shows the old fill.
- [App Store icons are square: add the corner radius on the node](#app-store-icons-are-square-add-the-corner-radius-on-the-node): one icon with square corners.

**Screenshots and QA**

- [Plugin screenshots cap the output size](#plugin-screenshots-cap-the-output-size): unreadable capture of a large section, no real 2x.
- [`figma_capture_screenshot` captures the active file only](#figma_capture_screenshot-captures-the-active-file-only): `Node not found` for another file.
- [A reduced-scale screenshot cannot approve alignment](#a-reduced-scale-screenshot-cannot-approve-alignment): "QA complete" and bugs found in minutes.

**REST and plan limits**

- [Never fall back to REST when the bridge drops](#never-fall-back-to-rest-when-the-bridge-drops): a 429 with a `Retry-After` of days.
- [The official Figma MCP server has a hard tool-call cap on a Starter plan](#the-official-figma-mcp-server-has-a-hard-tool-call-cap-on-a-starter-plan): "You've reached the Figma MCP tool call limit".

**Several agents on one file**

- [A deleted section that carried comment pins: restore the version, do not rebuild](#a-deleted-section-that-carried-comment-pins-restore-the-version-do-not-rebuild): comment pins float over nothing.
- [Restarting a shared bridge server releases another session's pin](#restarting-a-shared-bridge-server-releases-another-sessions-pin): writes land in another session's file.
- [Lock held by another live session while your writes are on a different page](#lock-held-by-another-live-session-while-your-writes-are-on-a-different-page): the lock blocks disjoint work.
- [Parallel builder agents on one bridge server work with a strict brief](#parallel-builder-agents-on-one-bridge-server-work-with-a-strict-brief): what kept 48 agents free of hangs.
- [An example in a multi-agent brief becomes data](#an-example-in-a-multi-agent-brief-becomes-data): a wrong example date copied into deliverables.

**Bridge setup**

- [figma-console tools missing from the session: talk to the server over stdio](#figma-console-tools-missing-from-the-session-talk-to-the-server-over-stdio): `No such tool available` while the server is connected.
- [Scope figma-console to design projects](#scope-figma-console-to-design-projects): about 130 tools in every session.

**Fonts**

- [Font keys in code are not Figma family names](#font-keys-in-code-are-not-figma-family-names): `loadFontAsync` fails on a code font key.
- [Installing fonts for Figma Desktop on macOS](#installing-fonts-for-figma-desktop-on-macos): fonts declared registered without proof.

## Sequential `await loadFontAsync` in a loop hangs the sandbox

- **Symptom:** a loop that awaits `figma.loadFontAsync(...)` one font at a time hangs after about
  5 to 7 loads, even when the fonts are already loaded.
- **Cause:** not established. Seen through `figma_execute` while building 24 screens. Finding it
  cost about 20 minutes of bisecting.
- **Fix:** preload every font in one `Promise.all` at the top of the script
  (`await Promise.all(fonts.map(f => figma.loadFontAsync(f)))`). A `Promise.all` of 10 fonts
  resolved in 55 ms.

(field note, 2026-09)

## `setTimeout` did not fire through the figma-console bridge

- **Symptom:** a timeout guard built with `Promise.race` plus `setTimeout` protected nothing in a
  `figma_execute` script.
- **Where:** the figma-console bridge (`figma_execute`) only. Not tried on `use_figma` or in a
  regular plugin.
- **Figma's docs say otherwise:** `@figma/plugin-typings` 1.140.0 declares `setTimeout` as a
  global (`index.d.ts`), uses it in the `saveVersionHistoryAsync` example, and says
  `figma.closePlugin()` cancels pending `setTimeout` timers. Both observations stand.
- **Cause:** not established.
- **Fix:** do not count on `setTimeout` as a timeout guard in `figma_execute`. Keep each script
  short instead: one or two screens per call.

(field note, 2026-09)

## `createAutoLayout`, `node.query` and `node.set` are not Plugin API

- **Symptom:** `TypeError: not a function` when a `figma_execute` script calls
  `figma.createAutoLayout`, `node.query` or `node.set`.
- **Cause:** those helpers belong to `use_figma` (the official Figma MCP server), not to the
  Plugin API. They do not exist in the figma-console bridge.
- **Fix:** `figma.createFrame()` and then set `layoutMode`.

(field note, 2026-09)

## `getRangeAllFontNames` in a loop hangs the sandbox

- **Symptom:** a text-editing script died on the third text node and the bridge stopped
  answering.
- **Cause:** calling `getRangeAllFontNames` on every text node in a loop.
- **Fix:** load the font styles the file uses once, at the top of the script (the session that
  hit this loaded Inter Regular, Medium, Semi Bold and Bold in a `preload()` helper). Call
  `getRangeAllFontNames` only when `fontName === figma.mixed`.

(field note, 2026-09)

## A script that runs past the execute ceiling freezes the sandbox for every session

- **Symptom:** after one script overruns, the plugin sandbox stays stuck for EVERY session on
  that bridge. The `GET_FILE_INFO` probe (a command of the Desktop Bridge plugin's WebSocket
  connection) starts failing.
- **Cause:** a hard ceiling of 32 s per `figma_execute` was measured. A `timeout` argument above
  that is ignored. The overrunning script leaves the sandbox blocked.
- **Fix:** the bridge only came back after re-triggering the plugin from the Figma menu
  (Plugins > Development > Figma Desktop Bridge, Step T of the `figma-bridge-doctor` skill)
  followed by `figma_reconnect`.
  As of figma-console-mcp v1.40.8, the maximum `timeout` of `figma_execute` is 30000 ms and
  `figma_reconnect` is informational: it does not repair a dead connection. `figma_get_status` is
  the proof that the bridge is back.
- **Prevention:** a chunk of about 12 text edits per script runs in 1 s. A `findAll` over a whole
  page, or `listAvailableFontsAsync` in the same script as another sweep, goes past the ceiling.

(field note, 2026-09)

## `figma_execute` with `fileKey` on a background file is throttled

- **Symptom:** a call aimed at a connected file that is not the focused one fails with "Unable to
  establish connection" at the 10 s timeout when it has 5 or 6 sequential `await`s. The same call
  with 1 or 2 awaits passes.
- **Cause:** `figma_execute` with `fileKey` does work on a background file, but Figma throttles
  that file.
- **Fix:** on an inactive file, slice the work: one `getNodeByIdAsync` per call and everything
  else synchronous.

(field note, 2026-08)

## An instance sublayer id fails with a fake network error

- **Symptom:** `figma.getNodeByIdAsync('I123:456;78:90')` (a text node inside an instance)
  returned three times in a row "Error: Unable to establish connection to Figma after 10 seconds.
  Please check your internet connection". Ping was normal and `getNodeByIdAsync('123:456')` on a
  frame answered at once. The same instance id had worked minutes earlier.
- **Cause:** the message looks like a network failure and is not. The failing id was an
  instance-internal id (`I...;...`) kept from an earlier read.
- **Fix:** reach nodes inside an instance from the frame, never through a stored `I...;...` id.
  Rewriting the script to start from the frame
  (`F.findAll(x => x.type==='INSTANCE' && x.name==='<component name>')`, then filter by
  `variantProperties`) applied the 16 fills in 1 s.
- **Detector:** when a short script reports "Unable to establish connection", test
  `getNodeByIdAsync` on a FRAME before blaming the network. Two scripts (frame by id, instance
  node by id) settle it. Skipping that cost 15 minutes and three blind retries.

(field note, 2026-09)

## End deep reads with `return JSON.stringify(out)`

- **Symptom:** `Cannot unwrap symbol` on the return of a deep read. It failed twice in a row
  before this fix.
- **Cause:** `figma.mixed` is a Symbol. One Symbol anywhere in the returned object breaks the
  whole return (see `references/plugin-api-core.md`).
- **Fix:** keep the `typeof` guards (`typeof n.fontSize === 'number'`,
  `typeof n.cornerRadius === 'number'`) and end the script with `return JSON.stringify(out)`.
  `JSON.stringify` ignores properties whose value is a Symbol, so it shields the boundary.

(field note, 2026-06)

## An instance cannot receive children, and a cross-page clone stays on the source page

- **Symptom:** `box.appendChild(logo)` where `box` lives inside an INSTANCE throws "Cannot move
  node. New parent is an instance". Worse: `source.clone()` of a node from ANOTHER page creates
  the clone next to the source, on the source page, and the failed `appendChild` leaves that
  duplicate there.
- **Cause:** an instance does not accept new children, and `clone()` places the copy beside the
  original, not on the page you are working on.
- **Fix:**
  - Remove the duplicate by name on the source page.
  - Get the visual through an override the instance allows: hide the icon vectors of the sublayer
    with `visible = false` and replace its `fills` with an IMAGE paint copied from the logo.
  - Or use an overlay with `layoutPositioning = 'ABSOLUTE'` in a sibling frame.
  - Before composing inside an instance, choose between sublayer override and absolute overlay.
    Never `clone()` across pages without a guaranteed `appendChild` in the same call.

(field note, 2026-09)

## Configure a nested instance only after inserting it into the slot

- **Symptom:** an instance was created with `createInstance`, configured (`findOne` on a child,
  `setProperties({...})`, rename) and only then placed with `slot.insertChild` into a slot inside
  another instance. The render was correct, but the instance kept 3 ghost sublayers. Any
  `findAll` with a predicate on `name` or `characters`, over the section or the whole page, failed
  with `findAll callback crashed: ... does not exist`.
- **Cause:** on entering an instance slot, the new instance gets compound ids
  (`I<parent>;<child>`). The proxies visited before the insert keep pointing at ids that Figma no
  longer recognizes, and the `findAll` predicate breaks when it reads `name` or `characters` from
  them.
- **Fix:** in a slot, or in any child of an instance, the order is `createInstance`, then
  `insertChild` or `appendChild`, and only then `findOne`, `setProperties`, rename, `rescale`.
  If the error shows up on an instance that already exists, recreate the instance in that order.
  Doing so restored `findAll`, with a PNG identical by sha256. Reloading the plugin could not be
  tested as an alternative fix.
- **Detector:** at the end of a batch, run `section.findAll(n => n.name === 'x')` WITHOUT
  try/catch as a health proof of the page. If it throws `findAll callback crashed`, the page has
  ghost sublayers.

(field note, 2026-09)

## A TEXT component property has one default value per component set

- **Symptom:** writing `characters` on a layer in the variants of one type only, to give them a
  different example text, changed all 5 variants and the 11 instances that inherited the default.
  The write had to be reverted.
- **Cause:** the layer was bound to a TEXT component property (`Label#12:34`). Figma stores one
  default value per set. The Plugin API has no default text per variant when the layer is bound to
  a TEXT property: the property value is the text.
- **Fix:** for a different example per variant, create a separate property with
  `addComponentProperty` and re-link only the layers of those variants
  (`componentPropertyReferences = {characters: key}`). Then re-point the overrides of the existing
  instances (`getInstancesAsync` plus `setProperties` with the old value).
- **Detector:** before writing `characters` on a layer of a component, read
  `componentPropertyReferences`.

(field note, 2026-09)

## Switching a variant resets the icon to the new variant's default

- **Symptom:** a tab bar was cloned from one screen to another and only `Selected: False -> True`
  was changed on one tab. The tab came out with the wrong icon (a filled home icon on a Messages
  tab).
- **Cause:** the `Selected=True` variant has a DIFFERENT icon slot node from the `Selected=False`
  variant, and the per-screen override lives in the slot of the source variant. After the switch,
  the new slot falls back to the component default. The override does not travel.
- **Detector:** after switching any variant that involves an icon, call `getMainComponentAsync()`
  on the INSTANCE child of the tab. A wrong component name means this bug. A full-screen
  screenshot at 1x does not show it: the icon is 20 px and disappears in the tab bar.
- **Fix:** `icon.swapComponent(await figma.getNodeByIdAsync('<id of the right icon>'))`. When
  cloning chrome (tab bar, nav bar) between screens, check the main component of EVERY icon after
  touching a variant, never only the label.

(field note, 2026-08)

## Mirrored vectors flip when cloned and repositioned

- **Symptom:** an icon vector restored from a saved copy with `clone()` and then `.x` / `.y`
  showed upside down in the tab bar. Stroke thickness (1.19 / 1.54 / 1.75 / 1.54 / 1.54),
  width, height and absolute position were identical to the original, so four green measurements
  approved an inverted icon.
- **Cause:** the vectors of those icon sets are stored mirrored on the Y axis:

  ```
  original:        relativeTransform = [[1, 0, 50.37], [0, -1, 341.15]]   <- scaleY = -1
  after the clone: [[1, 0, 50.47], [0,  1,  30.84]]                       <- mirror lost
  ```

  Setting `.x` / `.y` on the clone makes Figma normalize the transform: it recomputes the
  translation to keep the box in place and discards `scaleY = -1`. Same geometry, inverted figure.
  None of the measured quantities changes when the figure flips.
- **Fix:**
  1. Before touching an icon vector, read `relativeTransform`, not only x/y/width/height. If
     `t[0][0] < 0` or `t[1][1] < 0` the node is mirrored and any clone-and-reposition loses that.
  2. A faithful restore writes the whole `relativeTransform` from the saved copy. It does not set
     `.x` and `.y`.
  3. The verification must include the sign: `relativeTransform[1][1] < 0`. One comparison.
     Without it no dimension reveals the inversion.
  4. Closing proof: sweep the file for the instances of that family and count the non-mirrored
     ones. That sweep covered 79 instances and found zero inverted.
- **Related signal:** in the untouched siblings the vector sits at `y=327` inside a frame 372
  tall. That is the mirror offset, not a bug. A coordinate anomaly you cannot explain is a sign of
  a transform.

(field note, 2026-09)

## `vectorPaths` rejects the arc command

- **Symptom:** "Failed to convert path. Invalid command at A".
- **Cause:** `vectorPaths` does not accept `A` (arc).
- **Fix:** convert arcs to cubic curves. A 270 degree arc becomes three cubics with
  k = 0.5523 times the radius.
- **Related orphan:** `figma.createVector()` is born on the page. If the `appendChild` that
  follows fails, an orphan VECTOR stays at page level. Sweep `page.children` for VECTOR before
  repeating the call.

(field note, 2026-09)

## Page coordinates written to a SECTION child land far away and can move the section

The base rule (children of a SECTION use section-relative coordinates) is in
`references/plugin-api-anomalies.md`. These are the field details and the detector.

- **Symptom:** three cases. The setter raises no error.
  - A section was created at `y=5900` and its screens repositioned with `n.y = 6420`, meant as a
    page coordinate. Figma read 6420 as relative, put the screens at absolute y 12320 and MOVED
    the section itself from 5900 to 6819 to try to contain everything. The title stayed at the
    top and the screens ended 6,374 px below.
  - `c.x = -271; c.y = 4654` produced an `absoluteBoundingBox` at (-642, 9176), four thousand
    pixels below the section. The screenshot of the section came back as an empty dark rectangle
    with the screens loose underneath.
  - `sec.appendChild(f); f.y = 4160` on a section at y=4000 put the frame at absolute y 8,160
    instead of 4,160, inside the area of another section. All 15 frames needed `f.y -= sec.y`
    afterwards.
- **Cause:** a child of a SECTION has `x`/`y` relative to the section. A child of a PAGE has page
  coordinates. Mixing the two breaks in silence. Reads of `c.x`/`c.y` agree with each other and
  look coherent, so the verification passes. The only signal is to compare with the world:
  `absoluteBoundingBox`.
  (`references/plugin-api-anomalies.md` records that sections do not auto-grow to contain
  children. In the first case here the section's own position changed. Both observations stand.)
- **Fix:** before repositioning any child of a section, measure the offset instead of assuming.
  One call settles it:

  ```js
  const sb = sec.absoluteBoundingBox, cb = child.absoluteBoundingBox;
  // offset = cb - sb. If offset equals child.x/y, x/y are section-relative.
  // If cb equals child.x/y, they are page coordinates.
  ```

  Then position in RELATIVE coordinates (in that case a note at 88 and blocks at 452, 1562 and
  2672) and close by measuring `maxB = max(c.y + c.height)` against `sec.height`. Resize the
  section with `resizeWithoutConstraints(w, maxB + margin)`. Always check `absoluteBoundingBox`
  after positioning inside a section.

(field note, 2026-09)

## A section created through the API did not adopt the nodes underneath

- **Symptom:** `figma.createSection()` plus `resizeWithoutConstraints()` over existing nodes did
  NOT adopt any of them through the API: `children` came back empty.
- **Cause:** this note attributes the silent adoption described in
  `references/plugin-api-anomalies.md` to the user gesture of dragging or resizing a section in
  the UI. Through the API, an explicit `appendChild` is needed.
- **Fix:** append the children explicitly. This makes programmatic section creation safer than
  the themed file suggests, but `remove()` still takes with it whatever is inside the section.
  Both observations stand. Either way, create sections only on provably empty coordinates (the
  rule in `references/plugin-api-anomalies.md`) and append children explicitly.

(field note, 2026-08)

## `maxHeight` inherited from a clone blocks hug

- **Symptom:** the height does not change and no error is raised, even with
  `layoutSizingVertical = 'HUG'`.
- **Cause:** a `maxHeight` inherited from the cloned source (803.58 on a KPI container).
- **Fix:** `f.maxHeight = null`, and sweep the clone with `findAll(x => x.maxHeight != null)`.

(field note, 2026-09)

## A hug sweep shrinks cards that should fill a horizontal row

- **Symptom:** a card in a horizontal row shrinks in height (244 instead of 316).
- **Cause:** setting `primaryAxisSizingMode = 'AUTO'` on the card swaps FILL for HUG.
- **Fix:** after any hug sweep, re-apply `layoutSizingVertical = 'FILL'` on the cards that share
  a row.

(field note, 2026-09)

## Rebuilding content inside an existing auto layout frame stacks the new children

- **Symptom:** children positioned by x/y end up below the photo, outside the visible frame.
- **Cause:** the old frame still has auto layout, which stacks everything you append.
- **Fix:** when rebuilding the content inside an existing frame (done to keep the comment pins
  attached to it), set `layoutMode = 'NONE'` first.

(field note, 2026-09)

## Auto layout height read in the same call is stale

- **Symptom:** a sheet was cloned, its content replaced, and the home bar positioned with
  `body.y + body.height + 8` in the same block. The home bar landed at y=134 in a sheet 338 tall,
  across the body text. In another sheet it went to y=765 and left the screen. This burned three
  times in one session. The script reports success. It only shows in a screenshot, sometimes only
  in the sheet you did not capture.
- **Cause:** after changing the content of an auto layout frame, `frame.height` read in the SAME
  code block is the value from BEFORE the relayout.
- **Fix:** position the sibling in a SEPARATE `figma_execute` call from the one that changed the
  content, or re-read the height after any `resize`, `insertChild` or visibility change.
- **Detector:** at the end, sweep every sheet comparing `bar.y` with
  `content.y + content.height + gap` and fix what diverges. That sweep found both cases. Take a
  screenshot of EVERY sheet you built, never only the first.

(field note, 2026-08)

## Lists with interleaved separators: move or clone the separator with the item

- **Symptom:** a double hairline on one side of a reordered item and none on the other, or a new
  table row glued to the previous one.
- **Cause:** sections and rows alternate with sibling separator nodes (`Sep`, `hairline`) in the
  same auto layout. `insertChild` of the item alone leaves two separators together on one side.
  Cloning a row without cloning its hairline glues the new row to the one before.
- **Fix:** always two steps: move or clone the item, then reposition or clone the adjacent
  separator.
- **Detector:** read the sequence `children.map(n => n.name)`. It must alternate.

(field note, 2026-07)

## NAVIGATE needs a top-level frame on the same page

- **Symptom:** `setReactionsAsync` with `{type:'NODE', navigation:'NAVIGATE'}` rejects the
  destination: "Reaction at index 0 was invalid (destination ... for NAVIGATE actions,
  destinations must be a different top-level frame on the same page)".
- **Cause 1, nested destination:** a top-level frame is, in practice, a direct child of the PAGE
  or of a SECTION. A child of another FRAME is not. Screens built inside a FRAME used as a
  labeled band fail. Screens that are direct children of a section work.
- **Fix 1:** re-parent the screens to a SECTION (a section nested inside the larger section
  works). A band frame is for exploration that does not click (animation beats, alternatives).
  Anything that will become a flow is born in a section. Moving a section is cheap and preserves
  node ids, prototype links and flow starting points.
- **Cause 2, destination on another page:** NAVIGATE does not cross pages. This is not a limit of
  the Plugin API, it is the Figma prototype itself, so retrying does not help.
- **Fix 2:** clone the destination screens into an auxiliary section on your page. So the copies
  are not mistaken for the source of truth: give the section a self-explanatory name (for example
  "Existing screens the steps lead to"), suffix the frames with `(existing)`, and add one line to
  the handoff spec card (see `references/handoff-format.md`) saying they are copies for the
  prototype to navigate and must NOT become the base for implementation. Clear the reactions the
  clones inherited: they point to the source page and an audit reports them as broken links.
- **Detector:** after cloning any screen with internal navigation, sweep the whole page for
  reactions whose destination is not on the page. One sweep found 8 inherited links, from
  segmented controls, that pointed outside the page.

(field note, 2026-08)

## Re-pointing a reaction: write `actions`, not `action`

`references/plugin-api-core.md` states the rule in one line. This is the working form and the
detector.

- **Symptom:** `node.reactions` was cloned, `r.action.destinationId` changed and
  `setReactionsAsync` called. The call returned `success: true` and the next read showed the OLD
  destination. Nothing had been applied.
- **Cause:** each reaction carries TWO fields: `action` (legacy, singular) and `actions` (array,
  the one that counts). Figma reads the array. Changing only `action` is a silent no-op.
- **Fix:**

  ```js
  const built = node.reactions.map(r => ({
    trigger: JSON.parse(JSON.stringify(r.trigger)),
    actions: (r.actions && r.actions.length ? r.actions : [r.action]).map(a => {
      const c = JSON.parse(JSON.stringify(a));
      if (c.destinationId) c.destinationId = NEW_ID;
      return c;
    })
  }));
  await node.setReactionsAsync(built);
  ```

- **Detector:** `success: true` does not prove the write, and a re-read INSIDE the same call can
  be stale. After touching a prototype, re-read in a separate `figma_execute` and compare
  `(r.actions || []).map(a => a.destinationId)`.

(field note, 2026-08)

## A SECTION fill bound to a variable renders the base color you passed

- **Symptom:** new sections appeared BLACK. On regular nodes written by the same helper the
  canvas showed the token color. An independent verifier caught it.
- **Cause:** `setBoundVariableForPaint` stores the base color you pass in. The write helper
  passed `{r:0,g:0,b:0}` plus the binding. A regular node shows the token on screen, but a
  SECTION (and an export) renders the stored color.
- **Fix:** resolve the variable in its first mode, following aliases, and put that color in the
  paint before binding. It is the resolve-then-bind pattern that
  `references/plugin-api-anomalies.md` documents for boolean operations. If several agents share
  a write helper, make it resolve the variable before binding.

(field note, 2026-09)

## `setBoundVariableForPaint` drops paint opacity: bind first, set opacity after

- **Symptom:** the script wrote `f[0].opacity = 0.14` and THEN
  `f[0] = figma.variables.setBoundVariableForPaint(f[0],'color',v)`. The read-back returned
  opacity 1: a tinted chip became a solid bar and its text disappeared. No error, `success: true`.
- **Cause:** `setBoundVariableForPaint` discards `paint.opacity`.
- **Fix (as recorded in this note):** bind first, set opacity AFTER, in a second
  `node.fills = [...]` assignment. It applies to any bind with a translucent paint (the scrim of a
  white button, a tinted chip).
- **Detector:** read the property that changed (`fills[0].opacity`) and take a screenshot.
- **Differs from a themed file:** `references/plugin-api-data.md` records another working order
  (opacity in the paint literal, then bind) and failures when opacity is changed after the bind:
  spreading opacity into the paint after the bind (`{...p, opacity}`) drops the binding. This
  note does not record the code of its second assignment. Both observations stand. Apply one
  order, then read back `fills[0].opacity` and `fills[0].boundVariables.color`. If the opacity
  reads 1 or the binding is gone, use the other order, or the raw rgba fallback in
  `references/plugin-api-data.md`, and read back again.

(field note, 2026-09)

## Writes under a locked ancestor did not take through the figma-console bridge

- **Symptom:** in a large bind sweep, a handful of binds did not take. All of them were descendants of a
  GROUP with `locked: true`, while each node itself reported `locked: false`.
  `setBoundVariableForPaint` returned a paint normally, with no error.
- **Where:** one sweep through the figma-console bridge (`figma_execute`). Not reproduced since,
  and not tried on `use_figma`.
- **Figma's docs say otherwise:** `@figma/plugin-typings` 1.140.0, on `locked`: "Does not affect
  a plugin's ability to write to those properties." The same doc says a node counts as locked
  when it or any parent has `locked: true`. Both observations stand.
- **Cause:** not established. The failed binds and the locked ancestor were seen together in one
  sweep; the note does not show that the lock caused the failures.
- **Fix:** before writing, check the ancestor chain for `locked`, not only the node:
  `for (let p=n; p; p=p.parent) if (p.locked) ...`. Then read back what you wrote (the detector
  below): the read-back catches a write that did not take, whatever the cause.
- **Detector:** the post-write check must read THE THING THAT CHANGED (does
  `boundVariables[prop][i]` exist now?), never a proxy. A read-back that compared color and
  opacity passed on the 11 failures, because those values did not change precisely when nothing
  was written. Only an independent count after the sweep revealed them.

(field note, 2026-08)

## Contrast per mode: resolve both colors through their bindings

- **Symptom:** a spec gave the pressed background of a destructive button in the dark mode
  assuming a white label, at 4.98:1. The label is bound to an on-solid token that resolves to
  white in the light mode and to a near-black in the dark mode. The real pair measured 3.45:1.
  An independent read-only verifier recalculated with the real fill and failed it. The corrected
  background measured 6.22:1.
- **Cause:** contrast computed with the "obvious" text color instead of the variable resolved in
  that mode passes in the light mode and fails in the dark mode with nobody noticing.
- **Fix:** every per-mode color pair reads both sides through the binding (`boundVariables` of
  the text fill and of the background fill), resolved in that mode. Never assume white or black.
  In a spec written for an agent, give the pair per mode or tell the agent to read the binding.
  An independent verifier that recalculates on its own is worth the cost.

(field note, 2026-09)

## An uploaded image that no layer uses is discarded

- **Symptom:** hours after the upload, `getImageByHash(hash)` returns `null` and the layer that
  should carry the image shows blank. Six uploaded photos vanished this way in one session.
- **Cause:** `figma.createImage(bytes)` returns a hash, but if no layer uses the image, Figma
  discards it.
- **Fix:** send the image in the same round in which you apply it, or apply it right after.

(field note, 2026-09)

## Image bytes must not pass through the model

- **Symptom:**
  - Base64 pasted into the `code` of `figma_execute` (about 22 thousand characters going through
    the model's transcription): one wrong character and `figma.base64Decode` returns
    `Invalid base64 string`.
  - `figma_set_image_fill` takes the base64 AS A PARAMETER of the tool call. The agent has to
    emit the whole string, and transcribing about 100k characters of base64 is not reliable. It
    also costs about 1 token per 3 bytes, twice (read and resend). A delegated subagent spent 15
    minutes generating 115 KB and was killed.
- **Cause:** it is not a size problem, it is a fidelity problem. (`figma.createImageAsync(url)`
  is not a way out either: see `references/plugin-api-data.md`.)
- **Fix:** generate the JS file with a script (Python reads the PNG and embeds the base64, so the
  bytes never go through the model) and send that file with the direct stdio client that ships in
  the `figma-bridge-doctor` skill's `scripts/mcp-direct/` directory (`<mcp-direct>` below). The
  plugin pairs with that daemon without taking the bridge away from other sessions. These are
  macOS commands. `figma-status.sh` sits one level up, in the `figma-bridge-doctor` skill's
  `scripts/` directory.

  ```bash
  # 1. official source: the App Store icon through Apple's search API, checking sellerName
  curl -s "https://itunes.apple.com/search?term=<app>&entity=software&country=us&limit=5"
  # 2. download at 512, downscale to 4x the slot (a 32 slot = 128), embed into a logos.js with python
  # 3. start the daemon on a free WS port (9223-9232) and HTTP 8791; trigger the plugin from the Figma menu
  #    (the PID goes to a file in case each command runs in a fresh shell)
  WS_PORT=<free> HTTP_PORT=8791 node <mcp-direct>/daemon.mjs & echo $! > daemon.pid
  # 4. send
  python3 <mcp-direct>/fx.py logos.js 30000
  # 5. stop YOUR daemon only (pkill -f on the script path would also stop other sessions' daemons)
  #    and check the on-disk plugin for drift
  kill "$(cat daemon.pid)"; bash <mcp-direct>/../figma-status.sh | grep plugin_drift
  ```

  In the JS: `figma.createImage(figma.base64Decode(B64)).hash`, then
  `node.fills = [{type:'IMAGE', scaleMode:'FILL', imageHash}]`.
- **Other routes:** `upload_assets` on the official Figma MCP server (next note), or the
  fetch-from-localhost stack in `references/plugin-api-data.md`. The simplest fallback: the
  designer drags the asset into Figma (2 seconds, reliable). Leave the node ready (radius,
  structure) and hand over the node ids. Do not force base64.

(field note, 2026-09)

## `upload_assets` writes the fill in the cloud, and Figma Desktop stays stale until the file is reopened

- **Route:** `upload_assets` (official Figma MCP server) with `nodeIds:["<id>"]` returns a
  `submitUrl`. `curl -X POST <submitUrl> -F "file=@photo.jpg;type=image/jpeg"` applies the image
  fill on the node. A 409 KB photo went up whole, at no context cost. This is the upload contract
  as recorded in 2026-09. If the tool's current description asks for a different request shape,
  follow the description.
- **Symptom:** the open Figma Desktop keeps showing the old fill, and
  `figma.getImageByHash(hash)` returns null, until the file is reopened.
- **Cause:** the fill lands in the cloud file. REST `/v1/files/:key/nodes` shows IMAGE and a PDF
  export already carries the photo, but the open Desktop document is stale.
- **Fix:** reopen the file. Do NOT "fix" it through the bridge in that state: any write to
  `fills` on that node overwrites the image that is in the cloud.

(field note, 2026-09)

## App Store icons are square: add the corner radius on the node

- **Symptom:** an app icon downloaded from the App Store shows with square corners next to icons
  that look rounded.
- **Cause:** App Store artwork is full-bleed, because iOS masks it at display time. PNGs that
  already carry transparent corners sit on a node with `cornerRadius` 0 and still look rounded.
- **Fix:** a downloaded icon needs the radius on the node: 22.4% of the side (7 px at 32), the
  iOS icon ratio.

(field note, 2026-09)

## Plugin screenshots cap the output size

- **Symptom:**
  - `figma_take_screenshot` on a 3711 x 14500 section returns `scale` 0.11 and an image 1578 px
    tall, unreadable.
  - `figma_capture_screenshot` has a ceiling of about 2.4 MP: a 1280x1317 frame requested at
    scale 2 comes out at 1524x1568 (1568 px on the longer side). Its `scale` has a minimum of
    0.5, and the 1568 px cap takes care of the rest.
- **Cause:** the plugin export caps the scale by the size of the node. There is no export by
  region.
- **Fix, inspecting geometry on a large section:** export the overlay alone (a 1 x 1 frame with
  `clipsContent=false` includes its children), export screen by screen, and measure crossings by
  script (the segments of `vectorPaths` against bounding boxes).
- **Fix, a real 2x export:** `exportAsync` plus `figma.base64Encode`, returned from the script:

  ```js
  const bytes = await node.exportAsync({format:'PNG', constraint:{type:'SCALE', value:2}});
  return figma.base64Encode(bytes);
  ```

  This returned 628 KB in 1.1 s, measured through the direct stdio client
  (`<mcp-direct>/fx.py`, see the stdio note below). That base64 is image bytes: never print it
  into the conversation or return it through a native tool call (see "Image bytes must not pass
  through the model" above). Redirect the output of `fx.py` to a file and decode that file with a
  short script, the way screenshots are decoded to a file in the stdio recipe.
  (`references/figma-execute-atomicity.md` lists an output cap of about 20 KB per call. This note
  does not establish whether that cap applies to the direct stdio client. Both observations
  stand.)

(field note, 2026-09)

## `figma_capture_screenshot` captures the active file only

- **Symptom:** asking `figma_capture_screenshot` for a node of another connected file returns
  `Node not found`.
- **Cause:** `figma_capture_screenshot` does NOT take a `fileKey`. It captures the ACTIVE Figma
  file.
- **Fix:** the plugin capture is immune to the REST rate limit and reflects the runtime, but the
  target file has to be in focus: `open -a "Figma" "<file-url>"` (macOS), wait about 7 s, capture,
  and give the focus back afterwards.
- **Why it matters:** in the same session, REST `/v1/images` started answering
  `{"status":429,"err":"Rate limit exceeded"}` after about 10 renders and stayed at 429 for more
  than 15 minutes, with a 25 s backoff between attempts. That kills visual verification in the
  middle of the work. Do not loop on retries: change path.

(field note, 2026-08)

## A reduced-scale screenshot cannot approve alignment

- **Symptom:** a report said "visual QA complete, 24 masters approved" and the designer found 4
  bugs in minutes. A capture at 0.5x (an image 300 to 600 px wide) does not show a sheet shifted
  by 8 px, a 1 px margin, or a circle duplicated by partial overlap.
- **Cause:** a screenshot at reduced scale is blind below 10 px.
- **Fix:** before any "done" or "approved" on a canvas:
  1. Numeric gate on every delivered frame: dump absX/absY of the edges of every visible node
     against the frame (4 edges, text AND fill), with an explicit whitelist of the intentional
     bleeds.
  2. A bug with a signature calls for a sweep, not a point fix. Once the root cause is known,
     write the detector and run it over the WHOLE scope before answering. In this case the cause
     (a CENTER constraint applied by a resize) had a measurable signature (node width 350 to 376
     at absX 3 to 14) and the sweep found 3 screens at once.
  3. A defect inherited from the source screen counts as yours in the deliverable. Do not
     classify it as pre-existing and let it pass.
  4. Describe the QA exactly by what it verified. Do not claim a pixel-level comparison when the
     pixel checks covered the export (background, alpha, color leak) and not internal geometry.

(field note, 2026-07)

## Never fall back to REST when the bridge drops

- **Symptom:** the local bridge was down for about 30 minutes and a reader agent, on its own
  initiative, read parts of the file through the REST API with the personal access token (GET
  only). After 4 calls came a 429 with `x-figma-rate-limit-type: low` and `Retry-After: 396392`
  (about 4.6 days).
- **Cause:** the token belonged to an account on a View/Starter seat, whose quota for file
  endpoints is tiny. The prompt said the bridge was the only path that works but did not forbid
  REST explicitly, and the agent treated the outage as permission to use another path. The cost
  falls on every other session that depends on the same token (REST-backed tools such as
  `figma_get_comments`, and `figma_take_screenshot` when it goes through REST).
  As of figma-console-mcp v1.40.8, `figma_take_screenshot` uses the Desktop Bridge plugin when
  connected and falls back to the REST API.
- **Fix:** in every prompt for an agent that reads Figma, write it out: never REST, never the
  official Figma MCP server; if the bridge drops, stop, wait for it to come back, and report what
  could not be read. Before using REST on
  purpose, count the calls: a few per file per day. Limits depend on the seat and on the plan
  where the file lives: https://developers.figma.com/docs/rest-api/rate-limits/

(field note, 2026-09)

## The official Figma MCP server has a hard tool-call cap on a Starter plan

- **Symptom:** `get_metadata` (official Figma MCP server) succeeded ONCE. The next 2 calls failed
  with "You've reached the Figma MCP tool call limit on the Starter plan."
- **Cause:** a plan-level tool-call cap, NOT the screenshot 429 window. It does not reset
  quickly. One call can be the whole budget, so do not assume that server is a free read path.
  Limits depend on the seat and on the plan where the file lives.
- **Fix:** on a Starter-plan team, budget calls to the official server as scarce and read through
  the figma-console bridge (local plugin, no rate limit):
  - Structure, inventory and ALL copy in one call: `figma_execute` walking
    `getNodeByIdAsync(id)` plus `node.findAll(n => n.type === 'TEXT').map(t => t.characters)`.
    One call dumped the tree of a 17-screen section and every text string.
  - Visuals: `figma_capture_screenshot` (plugin `exportAsync`): no REST 429, capped at 1568 px.
    The note recorded `get_screenshot` (official server) and `figma_take_screenshot` both hitting
    the Figma REST 429 after about 6 calls.
    As of figma-console-mcp v1.40.8, `figma_take_screenshot` uses the Desktop Bridge plugin when
    connected and falls back to the REST API.
  - Large metadata (Claude Code specific): `get_metadata` on a large section can exceed the token
    cap and gets saved to a tool-results `.txt` file. Parse that file with `jq -r '.[].text'`
    instead of calling again.
- **Result:** the quota of the official server was gone in 3 calls. The bridge then carried the
  whole extraction (structure, copy and 4 screenshots).

(field note, 2026-06)

## A deleted section that carried comment pins: restore the version, do not rebuild

- **Symptom:** a section with 10 screens no longer existed, with 17 review comments waiting to
  be fixed on it. The comment pins floated over nothing. The version history had no version
  between two timestamps a day apart, and the author of the deletion could not be identified.
- **Cause of the rule:** rebuilding the screens would create new ids and the comments would stay
  detached for good. Restoring the version keeps the ids, and the pins attach again.
- **Fix:**
  1. Proof before acting: `GET /v1/files/<fileKey>/nodes?ids=<sectionId>&version=<versionId>`
     (with a version id from the file's version history) and a page by page diff against the
     current state read through the bridge. Restore only if the single difference is what
     disappeared.
  2. In Figma: File > Save to Version History, with a name ("Backup ... before restoring ..."),
     then File > Show Version History > right click the version > Restore this version.
     If an agent does these clicks on macOS: pressing a button of Figma's web-based UI through
     accessibility (`AXPress`) does NOT work (it returns 0 and nothing happens). When another
     agent is also driving the same screen, activate Figma and click (for example with
     `cliclick`) in the SAME command, take a screenshot after each click, and clear the canvas
     selection first, so a stray key from the other agent deletes nothing.
  3. The bridge drops on the restore: re-trigger the plugin and confirm with `getNodeByIdAsync`
     that the ids are back.
  4. Opening a file changes the active file of the bridge. If another session had a file pinned,
     give the pin back on EVERY live server: with the regular figma-console server and a direct
     stdio daemon both connected (port 9223 and the daemon's HTTP port 8791 in that case), run
     `figma_navigate({url, lock:true})` on each, and keep writing with `fileKey` (see the next
     note).

(field note, 2026-09)

## Restarting a shared bridge server releases another session's pin

- **Symptom:** a bridge server shared by several sessions died and an agent started a new one.
  The plugin reconnected both open files, but the active target became the other file, with no
  pin, and the file of a session that wrote without `fileKey` lost its pin. The next day the
  pinned file disconnected by itself and the pin was released again: with a single file
  connected, that file becomes the active one.
- **Cause:** tools called without `fileKey` write to the active file. A lost pin means the write
  of one session lands in the file of another.
- **Fix:**
  - Restore the pin with `figma_navigate({url, lock:true})`. In this incident it went through the
    daemon's HTTP endpoint with curl. When both the regular figma-console server and a direct
    stdio daemon are connected, restore it on each of them.
  - In multi-agent runs, read and write always with `figma_execute` plus `fileKey`.
  - Forbid agents from restarting a shared server.
  - After any drop: `figma_list_open_files`, note which file is active and which is pinned, and
    give the pin back to whoever had it.
- **Detector for a leaked write:** node count per page before and after, and ids with a new
  prefix (the part before `:`) that your inventory from before the drop did not have. That count
  proved nothing had leaked in this incident.

(field note, 2026-09)

## Lock held by another live session while your writes are on a different page

- **Symptom:** the file lock (`figma_lock.py check <fileKey>`, in the `figma-preflight` skill's
  `scripts/` directory) is held by a parallel session that is alive, and every write you need is
  on another page, on fully disjoint nodes.
- **Cause of the rule:** the lock exists because of real rival-write incidents, but contention
  between disjoint pages with the designer present is not worth an 18 minute wait. The right cost
  is one touch from the designer, not a block and not a silent bypass.
- **Fix:** a narrow exception, not a default.
  - Designer active in the conversation: ask one question that takes one touch, with a
    recommendation (override recommended, wait, or release if the other session has finished).
    Never bypass without the designer and never wait in silence.
  - Designer away and the agent working autonomously: override, and state the override in your
    reply so it stays in the transcript.
  - Override means writing without holding the lock, under the conditions of the narrow exception
    for disjoint pages in the `figma-preflight` skill. It never means `release --force` on the
    other session's lock: that flag is for the human. Leave the other session's lock untouched.
  - When overriding without the designer, write by node id, without `setCurrentPageAsync` (the
    active page of the plugin stays where the other session has it). In a large multi-page file,
    `getNodeByIdAsync` on a page that is not loaded can hang: load the target page with
    `await page.loadAsync()` and traverse from it (see `references/plugin-api-anomalies.md`).
  - In both cases, audit the section for rival nodes after the batch. Both recorded occurrences
    ended with zero rival writes.
  - What still BLOCKS: a held lock with writes on the SAME page, or no way to prove that the
    pages are disjoint.

(field note, 2026-08)

## Parallel builder agents on one bridge server work with a strict brief

- **Symptom:** none. This is a positive result: 13 screens built by 48 agents through the same
  bridge server with 0 hangs.
- **Cause:** the hangs in the notes above come from page-wide sweeps and long scripts, and one
  stuck sandbox blocks every agent.
- **Fix:** the brief forbids `findAll` outside the agent's own frame, `getRangeAllFontNames`,
  osascript and long scripts, and every agent verifies its own work by screenshot.

(field note, 2026-09)

## An example in a multi-agent brief becomes data

- **Symptom:** the brief for a run of about 110 agents, in 4 waves, all writing to one file
  through the same bridge server, carried an example date whose weekday was wrong. One agent
  corrected the brief in the middle of a wave, but several spec sheets and screens had already
  copied the wrong date. The final review found it on 4 pages.
- **Cause:** agents copy the example in the brief as if it were content.
- **Fix:** every numeric or date example in a multi-agent brief is checked by a script before the
  agents are released.

(field note, 2026-09)

## figma-console tools missing from the session: talk to the server over stdio

- **Symptom (Claude Code specific):** a tool search for Figma tools returns nothing and a direct
  call to `figma_get_status` answers `No such tool available`, while `claude mcp list` shows
  figma-console as Connected and the server process for this session is alive.
- **Cause:** Claude Code freezes the tool list at session start. If the handshake failed there,
  no in-session tool can register the server again.
- **Fix:** asking the designer for `/mcp` reconnect or a restart is the last resort, not the
  first. The server is a plain stdio MCP: start your own instance and speak JSON-RPC to it. A
  whole write session (16 screens) ran this way with no native Figma tool. The
  `figma-bridge-doctor` skill's `scripts/mcp-direct/` directory ships this client, with the npx
  entry resolved at runtime (the cache hash changes on every reinstall). The daemon dies with the
  session, and that is correct. When the designer interrupts the agent's turn, a daemon started
  in the background dies too (its HTTP port, 8791 in that case, then refuses connections): start
  it again with `WS_PORT=<free> HTTP_PORT=8791 nohup node <mcp-direct>/daemon.mjs &` and
  re-trigger the plugin from the Figma menu. The recipe, on macOS:
  1. **Daemon** (node, about 80 lines): `spawn` of
     `node "$(npm config get cache)/_npx/<hash>/node_modules/figma-console-mcp/dist/local.js"`
     with `FIGMA_ACCESS_TOKEN` in the environment and `FIGMA_WS_PORT=<free port>`. Handshake:
     `initialize`, then the notification `notifications/initialized`, then `tools/list`. A local
     `http.createServer` (for example on 8791) receives `{name, arguments}` and returns the
     `result` of `tools/call`. One message is **one line of JSON**, with no Content-Length.
  2. **Port:** the server scans 9223-9232 and `FIGMA_WS_PORT` pins one. List the ports in use
     with `lsof -nP -iTCP -sTCP:LISTEN | grep -E '922[3-9]|923[0-2]'`.
  3. **Pair:** triggering the plugin from the menu (Plugins > Development > Figma Desktop Bridge)
     makes the plugin scan again. **The plugin connects to ALL live servers in the range**, one
     WebSocket per server (stated in a comment in the plugin's `ui.html`), so starting yours does
     NOT take the bridge away from other Claude Code sessions. The rival-write audit in the
     `figma-bridge-doctor` skill records an older, opposite observation (one server at a time,
     whoever re-triggers last wins). After pairing, check `figma_get_status` from every session
     that needs the bridge.
  4. **Call:** use
     the client in [`figma-bridge-doctor/scripts/mcp-direct/`](../../figma-bridge-doctor/scripts/mcp-direct/) (`fx.py`, `shot.py`), which sends the
     bearer token the daemon writes to its state dir and `content-type: application/json`. The
     daemon refuses any request without both, and any request that carries an `Origin` header.
     A screenshot comes back as `content[].type === "image"` in base64. Decode it to a file
     instead of printing it.
- **Port collision:** if another process already owns the HTTP port, start the daemon on other
  ports (for example `HTTP_PORT=8792 WS_PORT=9227`) and make sure the client scripts point at the
  same port. The shipped `fx.py` and `shot.py` read `HTTP_PORT` as the daemon does, so export the
  same value in the shell that runs them (for example
  `HTTP_PORT=8792 python3 <mcp-direct>/fx.py script.js`).
- **Earlier observation (2026-06):** with 4 other sessions present, the gentle plugin-menu
  trigger attached the plugin to this session's server on port 9225. It was recorded then as
  winning a port race. Try it before any heavier re-attach.

(field note, 2026-08)

## Scope figma-console to design projects

- **Symptom (Claude Code specific):** with figma-console in the global MCP config, about 130
  tools load into every session, including projects that never touch design.
- **Cause:** a global MCP server registers its tools everywhere.
- **Fix:** keep figma-console project-scoped, in the `.mcp.json` of each design project. The
  first use asks for a one-time trust approval. When a session in another project is missing
  Figma, copy the same `.mcp.json` entry into that project's root. Do not move the server to the
  global config. The official Figma MCP server, when it comes through the claude.ai account
  connector (about 16 tools at the time of the note), stays account-level: that connector cannot
  be scoped per project, only toggled through `/mcp`.

(field note, 2026-06)

## Font keys in code are not Figma family names

- **Symptom:** `loadFontAsync({family:"RobotoMono",...})` FAILS.
- **Cause:** the app loads the font under a code key such as "RobotoMono-Regular", but in Figma
  the family is "Roboto Mono" with the style "Regular". Figma wants the family name plus the
  style, not the key the code uses.
- **Fix:** run `listAvailableFontsAsync()` and filter to find the exact family name before
  `loadFontAsync`. Run it in its own `figma_execute` call and return only the filtered family
  names: next to another sweep it goes past the execute ceiling (see "A script that runs past the
  execute ceiling freezes the sandbox for every session" above).

(field note, 2026-06)

## Installing fonts for Figma Desktop on macOS

- **Symptom:** fonts were declared "all registered" after running only `file` on them, without
  showing the `Family:` line of a single one.
- **Cause:** a valid font file is not a registered font, and web formats do not install.
- **Fix:**
  1. Only `.otf` and `.ttf` install. Font Book ignores or errors on `.woff` and `.woff2` (web
     formats). When preparing the folder, filter the desktop formats: `cp *.otf`, not woff.
  2. Installing is copying into `~/Library/Fonts/` (the user font directory: no sudo, CoreText
     discovers it, every app sees it). There is no need to open Font Book by hand.
  3. Verify the registration, not only the file:
     `system_profiler SPFontsDataType | grep -iE "Family:.*(<FontName>)"` shows the real
     `Family:` line. That is the name to use in Figma, and it sometimes differs from the file
     name (a trial or demo font can carry a "Trial" or "Demo" suffix). `file font.ttf` only
     proves that the file is a valid font, NOT that it registered.
  4. Figma Desktop reads fonts from CoreText, but it needs a **restart** if it was open during
     the installation. Tell the designer.

(field note, 2026-07)
