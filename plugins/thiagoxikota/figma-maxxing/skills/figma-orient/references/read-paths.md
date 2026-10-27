# read paths

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

## Read paths (the part that matters)

Tool names are written as base names. The prefix depends on the client.

**PRIMARY: the figma-console MCP server through its Desktop Bridge (local plugin, no rate limit).**

1. `figma_get_status`: confirms the Bridge and which file it is paired with. Every primary read below goes through the Bridge.
   - Disconnected and a write comes next: invoke the `figma-bridge-doctor` skill. Disconnected on a read-only orientation: the FALLBACK below covers only a trivial read, and anything larger needs the Bridge back, so invoke `figma-bridge-doctor` then too.
   - Paired with a file other than the `fileKey` of the pasted URL: have `figma-bridge-doctor` switch the Bridge to that file before reading (see "The active file DRIFTS on its own in the middle of a write" in that skill). Passing `fileKey` to `figma_execute` covers step 2 only; for the screenshot, that skill pins the active file with `figma_navigate` and `lock: true`. Otherwise the map gets built from the wrong file.
2. `figma_execute` with `getNodeByIdAsync` + `findAll`: the structure plus all the text content (the UI copy) of a whole page or section in ONE call. The script must `return` the data it collected (`console.log` is not an output channel). Return names, ids, sizes and text, and trim long strings.
3. `figma_capture_screenshot`: plugin `exportAsync`, the visual anchor.
4. `figma_get_variables`: the design system variables.

Rules for the step 2 dump:

- **Output cap.** Keep each return under about 20 KB (see `## Output protocol` in [`figma-canon/references/figma-execute-atomicity.md`](../../figma-canon/references/figma-execute-atomicity.md)). Past that cap the call fails silently or truncates, and the map comes out incomplete without any warning. When a page is too large for one return, dump one section or top-level frame per call.
- **Timeout.** As of figma-console-mcp v1.40.8, the default timeout of `figma_execute` is 5000 ms and the maximum is 30000 ms. For a page or section dump, pass `timeout: 30000`. If it still times out, split the dump by section.
- **No `node-id` in the URL.** List the pages first (names and ids from `figma.root.children`). Then walk only the pages you need, one page per call: resolve the page object, `await page.loadAsync()`, and traverse from it. Anchor on that page object, not on `figma.currentPage`, which follows the designer's live navigation. On a large multi-page file, resolving an id on a page that is not loaded can hang until the timeout: see "getNodeByIdAsync hangs (does not throw) in large multi-page files" in [`figma-canon/references/plugin-api-anomalies.md`](../../figma-canon/references/plugin-api-anomalies.md).
- Syntax rules for `figma_execute` live in [`figma-canon/references/plugin-api-core.md`](../../figma-canon/references/plugin-api-core.md).

The map also records the design system source: the variables from step 4, and whether the components come from this file or from a library, as the step 2 dump shows. Record only what you actually read.

**FALLBACK: the official Figma MCP server (remote, run by Figma).** It is a valid read path, second here only because of its budget: it is NOT a free path. On a Starter plan, `get_metadata` and `get_design_context` lasted about 1 call in one field case (field note, 2026-06) before returning a plan-level cap that does not reset quickly. Budget it as scarce. Use it only when the Bridge is down and the read is trivial: what that budget covers, for example one `get_metadata` on the node of the URL. Say in the reply that you used it. This is a deliberate, counted exception, not an automatic switch: for anything larger, an agent that loses the Bridge stops, reports the limit and waits (see "Never fall back to REST when the bridge drops" in [`figma-canon/references/field-notes.md`](../../figma-canon/references/field-notes.md)). Limits depend on the seat and on the plan where the file lives: see https://developers.figma.com/docs/rest-api/rate-limits/ .

When the official server is the only one installed (no figma-console), it is the read path rather than a fallback. Spend it in the cost order of [`figma-canon/references/inspect-protocol.md`](../../figma-canon/references/inspect-protocol.md) (`get_metadata` first, `get_design_context` only on a node, never on a whole page), walk only the pages the task needs, and record in the map under `Scope walked` what you did not read.

**Screenshots.** During orientation, take 1 to 2 anchor screenshots at most, with `figma_capture_screenshot` (plugin runtime): it sidesteps the REST 429. Mass capture goes in batches of 3 to 4 with a delay between batches.

**REST screenshot rate limit (field note).** `figma_take_screenshot` (figma-console MCP server) and `get_screenshot` (official Figma MCP server) hit HTTP 429 after about 6 calls in a batch, with a lockout of 30+ minutes. Limits vary with the seat and the plan (rate-limits page above). As of figma-console-mcp v1.40.8, `figma_take_screenshot` uses the Desktop Bridge plugin when it is connected and falls back to the REST API, and `figma_capture_screenshot` always uses the plugin runtime and needs the Bridge. Keep the budget above for any screenshot that goes through REST.

**URL parsing.**

| URL shape | What to do |
| --- | --- |
| Any figma.com file URL, for example `figma.com/design/:fileKey/:fileName?node-id=123-456` | Extract `fileKey` and `nodeId`. Convert `-` to `:` in the node id (`123-456` becomes `123:456`). |
| `.../branch/:branchKey/...` | Use the `branchKey` as the `fileKey`. |
| `.../board/...` | FigJam file. The read shape is different from a Design file: do not assume the page and frame structure described here, and record the file type in the map. |
| `.../slides/...` and `.../make/...` | Figma Slides and Figma Make. Same as FigJam: the read shape is different, so record the file type in the map. |
