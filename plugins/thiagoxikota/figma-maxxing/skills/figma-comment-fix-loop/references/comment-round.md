# comment round

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

## Phase 0: Comments (REST, never the Plugin API)

The Plugin API cannot read comments. Comments are read through the REST API, or through `figma_get_comments`, with the personal access token in the `FIGMA_ACCESS_TOKEN` environment variable. The figma-console MCP server reads the same variable, but it takes its own copy from its MCP config, and that copy can be older than the one in your shell. Never print the token, never write it to a file, never ask for its value in the chat. If the variable is not set in the shell, ask the user to export it there.

- `figma_get_comments` tends to return 403 when the token copy in the MCP server config is stale. Canonical path: call the REST endpoint directly, `GET https://api.figma.com/v1/files/<fileKey>/comments` with the `X-Figma-Token` header, through the bundled script. It reads the token from the environment, sends it only to api.figma.com, never prints it, and keeps the raw JSON.

  ```bash
  python3 "${CLAUDE_SKILL_DIR}/scripts/fetch_comments.py" <fileKey> comments-raw.json
  ```

  Other agents: the script sits in `scripts/` next to this file. Exit codes: `1` the API answered with an HTTP error (the script prints the first 300 bytes of the body), `2` usage or no token, `3` network error or timeout, `4` the answer was not JSON. Run it again once at most; do not loop.

  `comments-raw.json` holds every commenter's handle and avatar URL. Keep it out of git: write it to a folder your `.gitignore` covers, and never commit it.

- File that belongs to ANOTHER account: a personal access token and the OAuth session of the official Figma MCP server both return 404, and the Plugin API cannot read comments. The token has no access to the file. Ask the user to paste the comments: every open one, with its author, its text and the frame it is pinned on. Pasted comments carry no `client_meta`, so the frame and the pinned element come from the user.
- A pasted comment does not automatically authorize the full open set. For a requested review round, discover all comments in scope and sibling pattern debt; for a specific fix, inspect relevant siblings and report additional requests without silently applying them.
- Filter by author through `user.handle` AND `user.id` (when in doubt, confirm the stakeholder's account with the designer). Only OPEN comments (`resolved_at` is null) become work. Open replies inside a resolved thread count too: when the raw JSON does not make it clear whether a reply in a resolved thread still needs work, list it for the designer instead of dropping it.
- `client_meta.node_id` is the target frame. `client_meta.node_offset` is the pin position RELATIVE to the top-left of that frame (it is not an absolute coordinate). The pin finds the element: the child whose box, taken as `child_abs - frame_abs`, contains the point. When more than one element contains the point, the render in Phase 1 (step 3) decides.

## Phase 1: Analysis (parallel, without touching the bridge)

- Cluster the comments by `node_id`. Run 1 agent per cluster (subagents, where the agent runtime has them), READ-ONLY through REST:
  1. Node JSON from `GET /v1/files/<fileKey>/nodes?ids=<nodeId>&depth=2`, raising the depth progressively. NEVER request a root frame without `depth`.
  2. A render from `GET /v1/images/<fileKey>?ids=<nodeId>`, saved as a PNG file.
  3. The agent LOOKS at the PNG, locates the pin and returns a fix spec with node ids and exact values, classified as `mechanical`, `design` or `ambiguous`.

  The analysis agents do not use any Figma MCP server: the bridge is a serialized channel that belongs to the main loop alone. REST calls are rate limited: see [`figma-canon/references/rate-limit-recovery.md`](../../figma-canon/references/rate-limit-recovery.md).
- Vague comment ("?", "fix this"): interpret it from the pin and propose an alternative. Request for a brainstorm or for options: the answer is a board on the canvas with 2 to 3 real VISUAL COMPS (clones with the change applied, rescaled so each one fits WHOLE inside its card). A text-only board is not decision-ready. Designer voice: zero process or AI vocabulary on the canvas.
- A global factual comment can signal file-wide debt; reconcile it with the product source and authorized scope before applying a global sweep. A stakeholder comment alone is not a new owner decision.
- The sibling sweep goes by PATTERN CLASS across the whole file, not by the family of the pinned screen. A comment about the margin under the Save button, pinned on one screen, applies to every screen with a primary action. A comment about a white background, pinned on one list, applies to every list of the same kind. (Field note, 2026-08: the designer caught the narrow reading twice on one project, where the fix had been applied on the pinned screen and not on the others. A batch in 2026-07 had already been the same failure.)
- The stakeholder cited a surface of the APP as the reference (for example "like the tags on the Stats screen")? When the app's code is in the workspace, resolve it in the CODE (grep the screen for the exact classes and tokens), then bind the Figma variables with the SAME semantic name. Never eyeball it from a screenshot: if the code is not available, ask the designer for the token names. Field note, 2026-07: a reference to the tags of another screen led to that screen's card component, with the classes `bg-tag-bg` + `text-text`, which mapped to the variables `tag-bg` / `text-primary` that already existed in the file (names changed for this example). The fix becomes 1:1 with the implementation.

## Phase 2: Fixes (serialized, idempotent)

**Fixing a comment means changing the SCREEN where the pin sits.** A parallel board of options with a recommendation does NOT close a pinned comment: if the stakeholder opens the screen and it looks the same, the comment is still open (field note, 2026-07: a stakeholder asking whether the points had been fully resolved caught exactly this). And the ANCHOR of the pin defines the concrete case: "in this case the ideal is X" pinned on one specific block applies to that block, not to whichever reading is more convenient. When the stakeholder already stated the direction in the comment, apply it directly and adjust your own recommendation (push back once, then defer). Do not re-litigate it through a contrary "my bet" option.

Use the scope authorization already given. Ask only if the target/decision remains ambiguous or would expand the task, then run `figma-preflight`. On top of `figma-canon`, these are the traps specific to this loop:

| Trap | Rule |
| --- | --- |
| `figma_execute` timeout | It may have applied EVERYTHING or only part. Re-QUERY the state, then re-run idempotently (if already applied, skip). Never retry blind. |
| `layoutMode` set after FILL | It resets the sizing to HUG. Re-assert FILL at the end of the block. |
| AUTO after a resize | After `resize()`, an auto-layout frame stays FIXED on its primary axis and does not hug its content again by itself. Call `resize` with the right value, THEN set `primaryAxisSizingMode = 'AUTO'` (see "Auto-layout frame stuck FIXED after resize()" in [`figma-canon/references/plugin-api-anomalies.md`](../../figma-canon/references/plugin-api-anomalies.md)). |
| Instance sublayer | `characters` works once the fonts are loaded: use `getRangeAllFontNames` on a text node with mixed fonts. Across many text nodes, load each `fontName` once at the top of the script and call `getRangeAllFontNames` only when `fontName === figma.mixed` (see "`getRangeAllFontNames` in a loop hangs the sandbox" in [`figma-canon/references/field-notes.md`](../../figma-canon/references/field-notes.md)). On path B (`use_figma`), Figma's figma-use skill says `getRangeAllFontNames` is not a real method and points to `getStyledTextSegments(['fontName'])`, while the typings Figma ships with that skill still list it; this repo has not tested which is right, so use `getStyledTextSegments` there. `remove()` fails: use `visible = false`. A variant or an accessory is swapped with `setProperties` on the NESTED instance, never by hiding sublayers by hand. |
| Cleanup by name regex | Never a generic substring (`/accessories/` hid the label). Use a strict predicate and verify what it matched. |
| Climbing from the leaf to the "row" | Before `remove()`, confirm the target is not the CONTAINER of the list (check the children count). |
| Stuck channel | Cause seen in the field: the machine was swapping. If it is, ask the designer to close heavy Electron apps (desktop AI chat apps, for example); never close the user's apps yourself. Wait 15 to 20 s, then re-trigger the Desktop Bridge plugin (Step T of `figma-bridge-doctor`, or the designer runs Plugins > Development > Figma Desktop Bridge). Full reset through `figma-bridge-doctor` if it persists. |
| Overlay in auto layout | `layoutPositioning = 'ABSOLUTE'`. Otherwise it enters the flow and pushes the content out. |

Take a screenshot (`figma_capture_screenshot`, the live state) and LOOK at it after each screen. The canvas can change under you (the designer may be editing the file live): re-dump before each batch and null-guard everything.

## Phase 3: Review package

Folder `<project>/<stakeholder>-review-<date>/`, where `<project>` is the folder where you keep this project's files: `screens/` (1x PNGs of the FINAL state), `comments/<name>-comments.md` (every comment, with status, pin and action taken) + the raw JSON, `context/PROJECT_CONTEXT.md` (what a reviewer needs to know about the project and this round) + `FIX_LEDGER.md` (table: request -> done -> screenshot), `README.md` (how to read the package).

- Export: a local save server (on a free port in the 9223 to 9232 range) OR REST `/v1/images` with a freshness PROBE before the batch. The cloud lags behind the canvas, and a stale export has already produced a false "still broken" twice.
  - Freshness probe: export one node you just changed, read the PNG and confirm the change is visible before you export the batch. If it is stale, wait about 20 s and probe again. Do not re-edit a canvas that is already correct. The stale render behavior, and how to validate an exported file before trusting it, is in [`figma-canon/references/plugin-api-anomalies.md`](../../figma-canon/references/plugin-api-anomalies.md) ("REST /v1/images renders stale cloud state after plugin edits").
  - Save server: this repo does not ship it, so start the short one in [`figma-canon/references/plugin-api-data.md`](../../figma-canon/references/plugin-api-data.md) ("Export-to-disk server (POST)"). Inside `figma_execute`, export each node with `node.exportAsync` and POST the bytes to `http://localhost:<port>/?name=<file>.png`. The server sends `Access-Control-Allow-Origin: *` (plugin iframes have a `null` origin), binds the loopback address only (`::1`, or `127.0.0.1` where `localhost` resolves only there; never `::` or `0.0.0.0`), keeps only the basename of `name` and accepts only `.png` names and PNG bytes. The plugin must fetch `localhost`: `127.0.0.1` in the URL fails with "Failed to fetch". Pick a port in 9223 to 9232 that nothing is listening on, and stop the server when the export is done. The pipeline is in [`figma-canon/references/plugin-api-anomalies.md`](../../figma-canon/references/plugin-api-anomalies.md) ("Plugin export as REST 429 bypass").
- Evidence of position or of a section title: only a `screencapture` of the real canvas works (a section export does not include the label). This part is macOS only. Bringing Figma to the front steals focus from the designer, so tell them before you do it.
  1. If another window (the code editor, for example) is on top of Figma, activate Figma and raise its window 1: `osascript -e 'tell application "Figma" to activate' -e 'tell application "System Events" to perform action "AXRaise" of window 1 of process "Figma"'`. The System Events call needs the Accessibility permission described in `figma-bridge-doctor`.
  2. Confirm Figma is frontmost: `osascript -e 'tell application "System Events" to get name of first process whose frontmost is true'` must print `Figma`.
  3. Call `figma.viewport.scrollAndZoomIntoView([node])` through `figma_execute` and capture immediately after it: the viewport drifts while people are live in the file. With only the official Figma MCP server, use its screenshot tool on the node instead.
  4. Crop every capture to the Figma canvas region (for example `screencapture -x -R<x,y,w,h> <file>.png`). Never ship a capture that shows other windows, the menu bar, notifications or anything else from the user's desktop.
- Presence of an item under a 30% backdrop (the semi-transparent scrim behind a modal): prove it with the NODE TREE (scan the subtree and write it as a Markdown table). Pixels only prove style.
- Do not reply to or resolve comments in Figma on the designer's behalf. Questions from the stakeholder become a list for the designer to answer. Nothing can resolve a comment through the API anyway: the package is the evidence, and the human resolves each thread in Figma. Reply in a thread (`figma_post_comment` or the REST API) only when the designer asks for it, and remember that `@mentions` post as plain text.
