---
name: figma-click-flow
description: >-
  Draws a click-flow overlay on a section of laid-out Figma screens for static handoff: a dot on
  each clickable element, an elbow line with rounded corners and an open arrow at the destination
  screen. figma.createConnector is not a function in Figma Design files, so each connector is
  emulated with one SVG import (hardened recipe in references/draw-overlay.js). Use when the
  user asks for a "click flow", "flow arrows", "wire screens", "turn this into a flow", or in
  Portuguese "vira em fluxo", "setas do fluxo".
license: MIT
compatibility: >-
  Writes to a Figma Design file through figma-console-mcp (figma_execute, Desktop Bridge plugin
  in Figma Desktop) or through the official Figma MCP server (use_figma, Full seat, not
  validated by this repo; the recipe guards figma.loadAllPagesAsync, which Figma lists as not
  implemented there). Requires the figma-canon and figma-preflight skills.
metadata:
  author: Thiago Xikota
  version: "1.2.0"
---

# figma-click-flow: Click-flow handoff overlay

Draws a printed user-flow overlay on a section of laid-out screens. Each connection: a red dot at the click target on screen A, an elbow line with rounded corners ending in an open arrow at screen B's nearest edge. Reference look: a flow section of one production file.

**REQUIRED PREREQUISITE:** load `figma-canon` + pass `figma-preflight` before any `figma_execute` write (the write path is the figma-console MCP server through its Desktop Bridge plugin). With only the official Figma MCP server connected, the write goes through `use_figma` on path B of `figma-preflight` Check 0 (not validated by this repo: keep writes small, read back every change), and Phase 4 validates with `get_screenshot` within the budget in [`figma-canon/references/rate-limit-recovery.md`](../figma-canon/references/rate-limit-recovery.md).

## Why a separate skill (not createConnector)

`figma.createConnector` throws `not a function` in Figma Design files (verified via `figma_execute`, field note 2026-05). `CONNECTOR` nodes that already exist in design files were created via the UI (Shift+L shortcut) and **cannot be cloned**: `node.clone()` errors with `Cloning CONNECTOR nodes is not supported in the current editor`. This skill therefore emulates the connector look by importing one SVG per connection through `figma.createNodeFromSvg`.

## When to use

- A section of screens is already laid out and the user wants the printed click-flow overlay on top.
- The designer wired the prototype (`reactions` on nodes) and wants the same connections visible in static handoff.
- The user provides explicit `(from-element-id -> to-screen-id)` pairs.

## When NOT to use

- File is FigJam: use `figma.createConnector` directly.
- User wants to design layout: use your project's own build skill or workflow, if any, or ad-hoc `figma_execute` after `figma-preflight`.
- User wants Dev Mode component documentation: out of scope for this skill. Use your project's own handoff documentation workflow, if any.
- Section has > 40 connections: output becomes spaghetti. Split into smaller sub-sections first.

## Visual canon

Verified against a reference node in one production file. `refConn` in the right column is the reference connector.

| Property | Value | Source of truth |
| --- | --- | --- |
| Stroke color | `#E5484D` | Neutral default, configurable. The reference used one dominant red in 20+ instances; that value was project-specific |
| Stroke weight | 4 px | `refConn.strokeWeight === 4` |
| Path | Elbow with **rounded corners**, R = 12 px | `connectorLineType: 'ELBOWED'` + visual radius pixel-picked |
| Origin marker | Filled circle, r = 5 px (10 px diameter) | `connectorStartStrokeCap: 'CIRCLE_FILLED'` |
| End cap | Open arrow, two strokes back from tip at ±28°, length 12 px | `connectorEndStrokeCap: 'ARROW_LINES'` |
| Layer name | `flow-overlay · click-connectors` (kebab-case with a middle-dot separator, from one project's own layer canon; keep this exact name, because the rerun and the cleanup snippet find the overlay by it) | [`figma-canon/references/naming-canon.md`](../figma-canon/references/naming-canon.md) |

The stroke color `#E5484D` is a neutral default and is configurable: override it through the `strokeColor` input (`STROKE_COLOR` in the recipe) when the file has a brand-specific accent.

## Inputs

```yaml
sectionId: "123:456"            # required
mode: from-prototype            # default; OR "explicit" OR "auto-layout"
pairs:                          # used when mode === "explicit"
  - from: "123:789"             # element that gets tapped
    to:   "123:790"             # destination screen
triggerFilter: ["ON_CLICK", "ON_PRESS"]   # default; ignores hover/drag
includeOverlayActions: true     # default; sheets count as navigation
strokeColor: "#E5484D"          # default; see Visual canon
cornerRadius: 12                # default
strokeWeight: 4                 # default
originAnchor: "auto"            # default; "center" | "edge-toward-dest" | "auto"
```

Each input is a constant in the CONFIG block of `references/draw-overlay.js`: `sectionId` is `SECTION_ID`, `mode` is `MODE`, `pairs` is `EXPLICIT_PAIRS`, `triggerFilter` is `TRIGGER_FILTER`, `includeOverlayActions` is `INCLUDE_OVERLAY_ACTIONS`, `strokeColor` is `STROKE_COLOR`, `cornerRadius` is `CORNER_RADIUS`, `strokeWeight` is `STROKE_WEIGHT`, `originAnchor` is `ORIGIN_ANCHOR`. The recipe also has `DOT_RADIUS`, `ARROW_LEN`, `AUTO_LAYOUT_MIN_AR` and `AUTO_LAYOUT_ROW_GAP`, which have no input above.

**`mode` reference:**

- `from-prototype` (default): walks `reactions[]` on every descendant. Best when designer wired the prototype.
- `explicit`: uses `pairs`. Best when the caller has a known list (from a PRD, a spec that lists screen transitions, or a hand-curated list).
- `auto-layout`: groups top-level FRAMEs in the section into rows by Y, sorts each row by X, builds intra-row left-to-right pairs. Best when prototype isn't wired and screens are sequentially laid out (like a numbered catalog). Heuristic: verify visually before trusting; rows mixing scenarios may produce wrong connectors.
  - The name means pairs inferred automatically from the layout. It has nothing to do with Figma's Auto Layout feature.
  - Only portrait children count as screens: FRAME, COMPONENT or INSTANCE with height/width >= 1.3 (`AUTO_LAYOUT_MIN_AR`). This filters out labels and dividers. For desktop or landscape screens, lower that constant, or the run returns `drawn: 0`.
  - A screen whose Y is more than 100 px (`AUTO_LAYOUT_ROW_GAP`) below the previous one starts a new row.

**`originAnchor` reference:**

- `auto` (default): bbox center for small nodes (<200×200 = buttons, list rows), edge-toward-dest for screen-sized nodes (any node at least 200 px in both dimensions). Right behavior for both prototype-driven mode and screen-level adjacency.
- `center`: always bbox center. Use when prototype reactions are wired on small interactive elements and you want the dot ON the button.
- `edge-toward-dest`: nearest-edge midpoint. Use for screen-to-screen adjacency where center would put the dot deep inside the screen body.

If user just says "wire it up" with no detail, default to `mode: from-prototype`.

## Workflow (4 phases + cleanup)

### Phase 0: Sanity

Walk up to the page ancestor (sections may be nested inside sections), call `figma.loadAllPagesAsync()`, then `await figma.setCurrentPageAsync(pageNode)`. Use `figma.getNodeByIdAsync` exclusively: sync `getNodeById` errors under `documentAccess: dynamic-page`.

Server note for `use_figma` (official Figma MCP server): Figma's figma-use skill lists `figma.loadAllPagesAsync()` as not implemented in that runtime, and says a read of a member the node type does not have throws `TypeError: node.X: no such property 'X' on Y node`, optional chaining included ([figma/mcp-server-guide](https://github.com/figma/mcp-server-guide), read 2026-10). So the recipe calls `figma.loadAllPagesAsync()` inside `try`/`catch` and carries on without it (`setCurrentPageAsync` loads the page anyway), and it checks `"reactions" in n` before reading `reactions`, because SECTION, SLICE and COMPONENT_SET nodes do not declare it. In `figma_execute` both guards change nothing. This repo has not run the recipe on `use_figma`.

### Phase 1: Discover pairs

Walk descendants of the section. For each node, inspect `reactions[]`, and in each reaction read `actions[]` (the recipe falls back to the singular `action` field when `actions` is absent). Collect a pair when:

- `action.type === 'NODE'` (navigate to frame), OR
- `action.type === 'OVERLAY'` (open sheet/modal, counts as flow), AND
- `reaction.trigger.type` is in the `triggerFilter` (default: `ON_CLICK`, `ON_PRESS`, `ON_TAP`).

The recipe keeps a reaction that has no trigger.

Drop pairs where `from` or `to` cannot be resolved or lies outside the section's bounding box (likely external/cross-page links). Dropped pairs come back in the `dropped` array of the return value with a reason (`node not found` or `outside section`): report them instead of losing them silently.

If 0 pairs found, **return early** with a warning so the caller can switch to `mode: explicit` and supply pairs manually.

### Phase 2: Plan elbow geometry

For each pair compute (all in absolute page space):

- `origin` = anchor on `from` node's `absoluteBoundingBox`, picked by `originAnchor`: bbox center for small interactive nodes, nearest-edge-toward-dest for screen-sized FRAMEs (`auto` default), or as overridden.
- `dest` = nearest-edge midpoint of `to` frame's `absoluteBoundingBox` (left / right / top / bottom).
- Routing: a single L-shape through `(midX, origin.y)` then `(midX, dest.y)` where `midX = (origin.x + dest.x) / 2`. Same right-angle topology as `connectorLineType: 'ELBOWED'`.
- Corner radius = `cornerRadius` (default 12), inserted as Q-curves.

If `|origin.y - dest.y| < 2 * cornerRadius`, drop the elbow and draw a straight line (avoids degenerate corners).

### Phase 3: Draw

Per pair, build an SVG string with:

- `<circle>` at origin (origin marker).
- `<path>` with the elbow + Q-corners (the trunk).
- `<polyline>` arrowhead at dest.

Import via `figma.createNodeFromSvg(svgString)`, which returns a FRAME with vector children. Position the imported frame at `(minX, minY)` (the SVG's top-left in page space).

Coord-space rule (verified): SECTION children use **section-local** coords. After `section.appendChild(overlay)`, set `overlay.x = 0; overlay.y = 0` so overlay aligns with section's top-left. Then position each imported SVG frame as a child of `overlay` using overlay-local coords (subtract section absolute origin).

`vectorPaths.windingRule: 'NONE'` is accepted by the API (verified). Auto-fit moves a vector to its path's leftmost coord after `vectorPaths` is set; trust this rather than fighting it.

See [`references/draw-overlay.js`](references/draw-overlay.js) for the complete hardened snippet. The same snippet is written to run in `use_figma` of the official Figma MCP server too, with the guards described in Phase 0 (not validated on that server by this repo); the timeout figures below are for `figma_execute` only.

`figma_execute` has a default timeout of 5000 ms and accepts up to 30000 ms. After a timeout or an error, do not rerun at once: this recipe removes the prior overlay and then draws a new one, so first read [`figma-canon/references/figma-execute-atomicity.md`](../figma-canon/references/figma-execute-atomicity.md) and the section "figma_execute timeout on bulk clone and font loads" in [`figma-canon/references/plugin-api-anomalies.md`](../figma-canon/references/plugin-api-anomalies.md).

### Phase 4: Validate

Use `figma_capture_screenshot` (plugin export). REST-backed screenshots return HTTP 429 (rate limited) after a handful of calls in a batch; see [`figma-canon/references/rate-limit-recovery.md`](../figma-canon/references/rate-limit-recovery.md). **Do not** use `figma_take_screenshot` for large sections.

As of figma-console-mcp v1.40.8, `figma_take_screenshot` uses the Desktop Bridge plugin when connected and falls back to the REST API, while `figma_capture_screenshot` always uses the plugin runtime and needs the bridge. The rule above still holds: `figma_capture_screenshot` is the call that always stays on the plugin runtime.

Check:
- Every line starts on a real interactive element, not whitespace.
- Lines do not cut through unrelated screens (if so, raise corner radius or split into sub-sections).
- Origin dots sit on the correct element.
- Color, stroke weight, dot size match the visual canon table.

### Cleanup / remove overlay

Idempotent rerun: skill auto-removes any prior `flow-overlay · click-connectors` frame inside the section before drawing. To remove without redrawing (here `section` is the section node, from `await figma.getNodeByIdAsync(sectionId)`):

```js
const overlay = section.findOne(n => n.name === 'flow-overlay · click-connectors');
if (overlay) overlay.remove();
```

## Common mistakes

| Mistake | Fix |
| --- | --- |
| `figma.createConnector(...)` | Not a function in design files; emulate via SVG import |
| `node.clone()` on existing CONNECTOR | Throws "Cloning CONNECTOR nodes is not supported" |
| `figma.getNodeById` | Use `getNodeByIdAsync`; sync version errors under dynamic-page |
| Set `overlay.x = section.x` before append | Section children use LOCAL coords, produces double offset; set `x=0; y=0` AFTER append |
| Validate with a REST-backed screenshot | `figma_take_screenshot` returned 429 on the large sections of one production file; use `figma_capture_screenshot` |
| Filter only `action.type === 'NODE'` | Misses `OVERLAY` (sheet open), common in mobile flows; include both |
| Ignore `reaction.trigger.type` | Hover/drag triggers pollute the overlay; filter to ON_CLICK/ON_PRESS/ON_TAP |
| Draw nothing when prototype unwired | Detect 0 pairs and return early with a warning, not a silent empty overlay |
| Sharp 90° corners | Use Q-curves with R=12 to match reference rounded look |
| Passing `section.parent` to `figma.setCurrentPageAsync` | Walk up `parent` chain until `type === 'PAGE'`; nested sections break naive `section.parent` |

## Quick reference

| Need | Call |
| --- | --- |
| Discover prototype reactions | `node.reactions[].action.{type:'NODE'\|'OVERLAY', destinationId}` (the recipe reads `actions[]` and falls back to `action`) |
| Filter by trigger | `['ON_CLICK','ON_PRESS','ON_TAP'].includes(reaction.trigger?.type)` |
| Build connector SVG | `<circle>` + `<path>` (elbow w/ Q-corners) + `<polyline>` arrow |
| Import SVG | `figma.createNodeFromSvg(svgString)` returns a FRAME with VECTOR children |
| Default red | `#E5484D` (rgb 0.898, 0.282, 0.302) |
| Cleanup | `section.findOne(n => n.name === 'flow-overlay · click-connectors')?.remove()` |

## Cross-references

- `figma-canon` + `figma-preflight`: required before any `figma_execute` write.
- `figma-orient`: only run if file is unfamiliar this session; skip otherwise.
- `references/draw-overlay.js`: full hardened snippet, copy + parameterize for use. It is a `figma_execute` body (top-level `await` and `return`), not a standalone Node script.
- [`figma-canon/references/figma-execute-atomicity.md`](../figma-canon/references/figma-execute-atomicity.md): what to do after a `figma_execute` timeout or error before retrying.
