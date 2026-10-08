# Plugin API: data and token rules

Load alongside `references/plugin-api-core.md` for any write. How to read and write values, tokens, annotations, plugin-stored data and image bytes correctly. Covered here: the console.log channel, structured returns, the ALL_SCOPES anti-default, the setSharedPluginData substitution, annotation read and write, image bytes via `figma.createImage` or `upload_assets`, and the mutual exclusion between Variables and styleId.

Pairs with `references/plugin-api-core.md` (always-on write rules) and `references/plugin-api-anomalies.md` (non-obvious bugs).

Two execution contexts appear below. `figma_execute` is the figma-console MCP tool that runs through the Desktop Bridge plugin. `use_figma` is the tool of the official Figma MCP server. Where a limit was observed in only one of them, the section says which.

## console.log: not the output channel

- `console.log(...)` does NOT surface to the agent. The code must `return` structured data.
- Using `console.log({foo})` for debugging silently drops the payload.
- Pattern: build a result object and `return { ...debug, createdNodeIds: [...] }`.
- As of figma-console-mcp v1.40.8, the server ships a separate `figma_get_console_logs` tool. It does not change the rule: treat `return` as the only output channel of a script.
- The optional precheck hook (`hooks/figma-canon-precheck.py` at the root of this repository, opt-in, see the repository README) flags `console.log(`.

## figma.notify(): not implemented in use_figma

- In the `use_figma` context (official Figma MCP server), `figma.notify('message')` throws "not implemented".
- Use the `return` value for output, not notify.
- Never call `figma.notify()` in a script. The optional precheck hook flags this pattern.

## getPluginData and setPluginData: not supported in use_figma

- Standard `setPluginData(key, value)` and `getPluginData(key)` are NOT supported in the `use_figma` context (official Figma MCP server).
- Use `setSharedPluginData(namespace, key, value)` and `getSharedPluginData(namespace, key)` instead.
- Pick a stable namespace string (e.g. `"my-project"`, `"figma-canon"`).
- The limit was observed in `use_figma`. The `figma_execute` discipline in `references/figma-execute-atomicity.md` lists the same substitution as a rule, so write the shared variant on both paths.
- Never use the unsupported pair. The optional precheck hook flags `setPluginData(`.

## Variable scopes: never default to ALL_SCOPES

- When creating Variables programmatically via `figma.variables.createVariable()` or assigning `variable.scopes`, **never** pass `['ALL_SCOPES']` as the default.
- `ALL_SCOPES` floods the human property picker (every variable shows for every property) and disrupts downstream design-system token mapping.
- Pick the narrowest scope set that matches the variable's intent:
  - Color vars for backgrounds: `['FRAME_FILL', 'SHAPE_FILL']`
  - Color vars for text: `['TEXT_FILL']`
  - Color vars for borders: `['STROKE_COLOR']`
  - Spacing vars: `['GAP', 'WIDTH_HEIGHT']`
  - Corner radius: `['CORNER_RADIUS']`
- See the Plugin API `VariableScope` enum for the full list.
- The optional precheck hook flags the `ALL_SCOPES` literal.

## Variables and styleId: mutually exclusive on the same property

On a single paint/stroke/effect property, a Variable binding (`boundVariables.fills` / `.strokes` / `.effects` / `.layoutGrids`) and a Style ID (`fillStyleId` / `strokeStyleId` / `effectStyleId` / `gridStyleId`) **cannot coexist**. Setting one auto-clears the other: last write wins.

**Empirical verification (field note, 2026-05, one production file):**

| Sequence | `fillStyleId` after | `fills[0].boundVariables` after | Resolved color |
| --- | --- | --- | --- |
| `setFillStyleIdAsync(red)` then bind Variable(blue) | `""` (cleared) | `{color: VARIABLE_ALIAS}` | blue |
| Bind Variable(blue) then `setFillStyleIdAsync(red)` | red style id | `{}` (cleared) | red |

**Implications:**

- Do not trust a single read: when verifying what is applied, inspect BOTH `node.fillStyleId` AND `node.fills[i].boundVariables.color`. Exactly one will be non-empty per property.
- The claim that the Variable always wins is **wrong**. The truth is "last set wins", and applying one un-applies the other.
- For design system sweeps that migrate from Styles to Variables: bind the Variable and the styleId clears as a side effect. You do not need a separate `setFillStyleIdAsync("")` call.
- For design system sweeps that go the other way (rare): set the styleId and the variable binding clears.

## setBoundVariableForPaint pattern

Bind a Variable to a paint's color without losing other paint properties:

```javascript
const fills = JSON.parse(JSON.stringify(node.fills));
fills[0] = figma.variables.setBoundVariableForPaint(fills[0], "color", variable);
node.fills = fills;
```

`setBoundVariableForPaint` returns a NEW paint object: assign it back into the cloned array, then reassign `node.fills`.

### Opacity stomp warning

Field note, 2026-05. `setBoundVariableForPaint` does **NOT** reliably preserve `paint.opacity`:

1. **Variable has intrinsic alpha.** Some tokens (for example a grey token meant for strokes) carry alpha 0.10 in their resolved value. Binding overrides whatever opacity you passed: the result paint has the variable's alpha, not your input. Do not use a token meant for strokes as the fill of secondary text.

2. **API can rewrite opacity even for alpha-1 variables.** Passing an input paint with `opacity: 0.08` and binding a clean white variable can return a paint where `opacity = 1`. The API discards the explicit opacity field during reconstruction.

**Rule:** for translucent surfaces (intended alpha below 1), do **NOT** bind a variable, use raw rgba directly:

```javascript
// CORRECT for translucent: no bind, raw rgba
node.fills = [{ type:'SOLID', color:{r:1,g:1,b:1}, opacity: 0.08 }];
```

Reserve variable binding for **opaque** surfaces where the canonical token color is the point (iOS Blue button background, iOS Green toggle on, brand dark background). Translucent overlays and glass tints stay raw rgba.

#### Counter-evidence and working order

Field note, 2026-06. When a design system spec REQUIRES the translucent fill to be token-bound (a no-raw-hex rule), binding CAN be made to work: order is everything. Verified: a callout fill using the brand color at 10% kept `opacity:0.10` AND the binding (read back `fills[0].opacity === 0.1` and `fills[0].boundVariables.color` present).

- **WORKS:** put `opacity` in the paint LITERAL, then bind:
  ```javascript
  let p = { type:'SOLID', color:{r:0,g:0,b:0}, opacity:0.1 };
  p = figma.variables.setBoundVariableForPaint(p, 'color', v);  // keeps opacity 0.1 + binding
  node.fills = [p];
  ```
- **BREAKS: spread AFTER bind breaks the binding** (the color reverts to the literal `{0,0,0}`, black at that alpha): `p = {...p, opacity:0.1}` renders gray, not the token. The spread drops the bound-variable linkage.
- **BREAKS: in-place mutate after bind does not stick** (the paint is read-only): `p.opacity = 0.1` silently no-ops and the fill renders at full opacity.
- **ALWAYS VERIFY, then fall back:** after assigning, read `node.fills[0].opacity` and `.boundVariables.color`. If the API stomped opacity to 1 (the 2026-05 case above still happens with some token alphas), fall back to raw rgba. So: bind with literal opacity, verify, raw rgba fallback. Use raw rgba freely when the project spec tolerates it; use bind-then-verify when the spec demands no raw hex.

## Annotations: read and write the `annotations` property

The `get_design_context` tool (official Figma MCP server) MAY omit a node's annotations to save tokens. For handoff-grade extraction (accessibility labels, validation specs, analytics events, behavior contracts), read them from the node itself.

There is no `getAnnotations()` or `setAnnotations()` method. Annotations live in the `node.annotations` property, and the file's categories live in `figma.annotations`. Checked against `@figma/plugin-typings` 1.140.0 (2026-10).

```javascript
// In figma_execute: read
const node = await figma.getNodeByIdAsync('123:456');
if (!node || !('annotations' in node)) return { error: 'node not found or not annotatable' };
const categories = await figma.annotations.getAnnotationCategoriesAsync();
return {
  annotations: node.annotations, // [{ label | labelMarkdown, properties: [{ type }], categoryId }]
  categories: categories.map(c => ({ id: c.id, label: c.label })),
};
```

Writing replaces the whole array, like `fills`. Each annotation carries text (`label` or `labelMarkdown`, use one), optional pinned measurements (`properties: [{ type: 'width' }]`, where `type` is an `AnnotationPropertyType` such as `width`, `height`, `fills`, `cornerRadius`, `padding` or `itemSpacing`) and an optional `categoryId` from the file's categories. There is no free-form JSON field: if you need machine-readable keys, put them in the text (for example `a11y: role=button`).

```javascript
// In figma_execute: append one annotation in a category, then read back
let cat = (await figma.annotations.getAnnotationCategoriesAsync()).find(c => c.label === 'Accessibility');
if (!cat) cat = await figma.annotations.addAnnotationCategoryAsync({ label: 'Accessibility', color: 'teal' });
node.annotations = [
  ...node.annotations,
  { labelMarkdown: '**a11y:** role=button, label "Save draft"', categoryId: cat.id, properties: [{ type: 'width' }] },
];
return { count: node.annotations.length, last: node.annotations[node.annotations.length - 1] };
```

Category colors are limited to `yellow`, `orange`, `red`, `pink`, `violet`, `blue`, `teal` and `green`. A category's name is `label`, not `name`.

Density cap: at most 10 to 15 annotations per node, to stay under the 20 KB output ceiling when reading them back (see `references/figma-execute-atomicity.md`).

As of figma-console-mcp v1.40.8, the server also ships the tools `figma_get_annotations` and `figma_set_annotations`, an alternative to the raw Plugin API calls above.

## Image bytes: plugin path

The `upload_assets` tool of the official Figma MCP server exists (verified in a Claude Code session through ToolSearch, which is a Claude Code specific mechanism) and uploads bytes that can be applied as `imageHash` on a node's fill. Any claim that image write is not supported is wrong. Note that `use_figma` itself is documented as having no image asset support as of 2026-10; `upload_assets` is a separate tool of the same server.

**Plugin-side alternative (preferred when on the Starter plan or already inside `figma_execute`):**

```javascript
// Inside figma_execute: uses Plugin API directly, no Remote MCP call
const pngBytes = new Uint8Array([/* PNG bytes */]);
const img = figma.createImage(pngBytes);
const fills = JSON.parse(JSON.stringify(node.fills));
fills[0] = {type: "IMAGE", scaleMode: "FILL", imageHash: img.hash};
node.fills = fills;
return { imageHash: img.hash };
```

**Empirical verification (field note, 2026-05):** a 1x1 red PNG passed to `figma.createImage` returned a hash, the IMAGE fill rendered, and `node.exportAsync` produced a valid PNG. All of it happened in a single `figma_execute` block, bypassing the tool-call cap that the official Figma MCP server applies on the Starter plan.

**Official Figma MCP server path (when you need to round-trip from local files):**

1. Call `upload_assets` with `fileKey` (and optionally `nodeId`, see step 3). It returns upload URL(s).
2. POST raw bytes to each URL with the right `Content-Type`.
3. If you also pass `nodeId`, the tool sets the image as fill in one step.

Check the tool's current schema for the exact parameter names before calling.

Do not fall back to gray placeholders when the agent needs to embed real imagery. Custom fonts ARE still unsupported via plugin. This field note does not say in which execution context that font limit was observed.

Separately, `use_figma` (official Figma MCP server) is documented as having no custom font support as of 2026-10.

## `createImageAsync(url)`: stricter than `allowedDomains`

Field note, verified 2026-05, in `figma_execute` through the figma-console Desktop Bridge plugin. Three independent validation layers gate image loading. Each fails with a different error, and the surface error misleads about which layer rejected.

1. **Manifest `networkAccess.allowedDomains`**: controls `fetch` + WebSocket. Listed = pass.
2. **`figma.createImageAsync(url)` URL validator**: STRICTER. Rejects URLs that ARE in `allowedDomains`. Empirically rejects `http://localhost:*` even when explicitly listed. Returns `Image URL <url> does not satisfy the allowedDomains specified in the manifest.json`: a misleading error.
3. **CORS on the response**: `fetch` requires `Access-Control-Allow-Origin: *`. Figma's [network requests page](https://developers.figma.com/docs/plugins/making-network-requests/) says plugin iframes have a `null` origin, so there is no specific origin to list. Plain `python3 -m http.server` returns no CORS headers and fails with a bare `"Failed to fetch"` (no stack).

**Working stack for arbitrary bytes from a local source.** Pick any free port inside the bridge plugin's localhost range, 9223 to 9232 (the figma-console-mcp plugin manifest lists that range). The bridge WebSocket itself listens inside the same range, starting at 9223, so use a port that nothing is listening on. `<PORT>` below stands for the port you picked: set the same number in the `PORT` constant of the server and in the script URL.

```javascript
// 1. Run a CORS-enabled HTTP server on a free port in the manifest's localhost range
//    (figma-console-mcp manifest lists 9223-9232)
// 2. fetch(): passes layer 1 (manifest) + layer 3 (CORS)
//    Replace <PORT> with the free port you picked inside 9223-9232.
const resp = await fetch("http://localhost:<PORT>/avatar.png");
const bytes = new Uint8Array(await resp.arrayBuffer());

// 3. figma.createImage(bytes): no URL validation, no layer 2
const img = figma.createImage(bytes);
node.fills = node.fills.map(f =>
  f.type === "IMAGE" ? { ...f, imageHash: img.hash, scaleMode: "FILL" } : f
);
```

**CORS-enabled python server (inline helper: save it to a scratch file, point `os.chdir` at the folder that holds the images, and run it with `python3`):**

```python
import http.server, socketserver, os
PORT = 9232  # any free port inside 9223-9232
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()
    def do_OPTIONS(self):
        self.send_response(204); self.end_headers()
os.chdir("/path/to/image/dir")
with socketserver.TCPServer(("127.0.0.1", PORT), H) as s:
    s.serve_forever()
```

**If the fetch still fails with "Failed to fetch" while the CORS headers are in place, bind on IPv6 loopback.** A later field note (2026-08, the createNodeFromSvg corollary in `references/plugin-api-anomalies.md`) found that the plugin manifest allows `localhost`, `localhost` resolved to `::1`, and a server bound only to `127.0.0.1` returned "Failed to fetch". The fix recorded there was an IPv6 socket (`address_family = AF_INET6`) bound on `::`. Bind `::1` instead: `::` is the unspecified address and listens on every interface, while `::1` is the loopback address `localhost` resolved to. Replace the last two lines of the server above with:

```python
import socket
class Server6(socketserver.TCPServer):
    address_family = socket.AF_INET6
with Server6(("::1", PORT), H) as s:  # IPv6 loopback only; never "::" or "0.0.0.0"
    s.serve_forever()
```

Which address to bind: `python3 -c "import socket; print({a[4][0] for a in socket.getaddrinfo('localhost', 9232)})"`. If it prints only `127.0.0.1`, keep the IPv4 server above, bound to `127.0.0.1`. The `::1` bind was checked with `curl http://localhost:<PORT>` on macOS (2026-10), not inside Figma; the field runs bound `::`.

Both servers send `Access-Control-Allow-Origin: *` and listen on loopback, so a web page open in your browser can also reach them. Start the server for the task and stop it when the task is done.

**Export-to-disk server (POST).** The export pipeline in `references/plugin-api-anomalies.md` ("Plugin export as REST 429 bypass") POSTs PNG bytes from `figma_execute` to `http://localhost:<PORT>/?name=<file>.png`. The `name` comes from a script, so the server keeps only its basename, accepts only `.png` names made of letters, digits, dot, dash and underscore, and refuses a body that does not start with the PNG signature:

```python
import http.server, os, re, socket, socketserver, urllib.parse
PORT = 9232                       # any free port inside 9223-9232
OUT = "/path/to/export/dir"       # the folder that receives the PNGs
SAFE = re.compile(r"[A-Za-z0-9._-]{1,120}\.png")
PNG = b"\x89PNG\r\n\x1a\n"
class H(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")  # plugin iframes have a null origin
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()
    def do_OPTIONS(self):
        self.send_response(204); self.end_headers()
    def do_POST(self):
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        name = os.path.basename(query.get("name", [""])[0])
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if not SAFE.fullmatch(name) or not body.startswith(PNG):
            self.send_response(400); self.end_headers(); return
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(body)
        self.send_response(204); self.end_headers()
class Server6(socketserver.TCPServer):
    address_family = socket.AF_INET6
with Server6(("::1", PORT), H) as s:  # or socketserver.TCPServer(("127.0.0.1", PORT), H)
    s.serve_forever()
```

**Why `createImageAsync` keeps coming up:** people see `figma.createImage(bytes)` documented and reach for the async URL variant when they have a URL. The async variant is the wrong abstraction for the plugin sandbox plus non-CDN sources: its URL validator is stricter than the manifest. **Do not waste cycles editing the user's installed plugin manifest** when this fails. Use the fetch + CORS + `createImage(bytes)` stack.

## Caveats on image fills

- The `figma_set_image_fill` tool (figma-console MCP) returns a valid hash but reports "applied to 0 node(s)" and does NOT write the fill. Use the hash via `figma_execute` instead: see `references/plugin-api-anomalies.md`.
- Asset URLs from `localhost:3845/assets/*` (port 3845 is the local MCP server of Figma Desktop, see `references/security-canon.md`) are ephemeral. For repo persistence, export the bytes with `node.exportAsync(...)` inside `figma_execute`, or capture with `figma_capture_screenshot`, and store them locally. The export-to-disk pipeline is in `references/plugin-api-anomalies.md`, section Plugin export as REST 429 bypass.

## Anti-patterns to flag (data)

Each line is something NOT to do, followed by the fix or the reason.

- Using `setPluginData`: use `setSharedPluginData` instead.
- Using `console.log(...)` for output: use `return { ... }` instead.
- Calling `figma.notify()`: not implemented (observed in `use_figma`). Never use it for output on any path; use `return`.
- Defaulting variable scopes to `['ALL_SCOPES']`: pick the narrowest scope set.
- Reading only `fillStyleId` OR only `boundVariables` to determine what is applied: read both; exactly one is set per property.
- Assuming `get_design_context` returns annotations: read `node.annotations` for handoff-grade extraction.
- Gray-placeholder fallback when image fills are needed: `figma.createImage(bytes)` works inside `figma_execute`.
