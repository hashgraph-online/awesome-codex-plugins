---
name: ui-design-canvas
description: 'An infinite, Figma-like canvas for UI/UX design work such as mobile apps and web interfaces. It renders images and HTML/CSS/JS pages side by side so designers can review, compare and iterate on designs. Use when the user wants to design screens, build UI prototypes or mockups, or put generated images or HTML pages on a canvas to view them.'
---

# UI design canvas

Codex Design is a canvas that the user and you edit together. You add and change nodes with this plugin's tools and by editing files. Every change shows up live in any open canvas.

Complete the whole flow: **get a canvas (`open_canvas` / `create_canvas`) → open it in the Codex in-app browser and give the user its link → add or update nodes**. Open the canvas before updating nodes, so the user watches them appear.

## Where the canvas lives

Each canvas is a project stored in its own directory, `<defaultProjectDataDir>/<projectId>/`. `defaultProjectDataDir` is a user setting: read it with `cat ~/.codex-design-plugin/config.json`. The `projectPath` returned by `open_canvas`, `create_canvas` and `list_canvas_projects` is the exact directory and takes precedence.

Below, `<projectPath>` means that directory.

- **How to get projectId**: if the in-app browser has a canvas open, its URL looks like `http://127.0.0.1:<port>/?project=<projectId>`; that `project` value is the project the user is working on. Otherwise, reuse a projectId already mentioned in this conversation. If the user refers to an existing canvas by name, call `list_canvas_projects` and match it. If there is no current canvas at all, call `create_canvas` with a short descriptive name, then show it as described in _Show the canvas_.
- **Current state**: `<projectPath>/canvas.json` holds every node as JSON. Read it to see what is on the canvas, but never write it: change nodes only through `add_node` and `edit_node`.
- **Files**: node content lives in `<projectPath>/asset/`. Paths in node JSON are relative to `<projectPath>`, e.g. `asset/home.html`. If the sandbox blocks writing there, request permission for that directory.
- **Plan limit**: the free plan allows one project. When `create_canvas` fails because of it, tell the user what the error says, including the pricing link, and offer to keep working in an existing canvas. If the user gives you a license key (it starts with `cdp_sub_`), activate it with `activate_pro`, then retry `create_canvas`.

## Node JSON

Both node types share one shape. Only `type` and `data.path` are required; the daemon fills in everything else, so leave out what you do not care about.

```jsonc
{
  "id": "home-screen",            // optional, unique in the project; generated when omitted
  "type": "image" | "html",       // required
  "position": { "x": 0, "y": 0 }, // optional, top-left in canvas pixels; placed on a grid when omitted
  "data": {
    "path": "asset/home.html",    // required, see each node type below
    "title": "Home",              // optional, label on the canvas; defaults to the file name
    "width": 390,                 // optional, size on the canvas in CSS pixels
    "height": 844                 // optional
  }
}
```

`edit_node` takes a patch in the same shape, minus `id` and `type`, and merges it into the node: `{ "position": { "x": 480 } }` moves a node right and keeps its `y`.

When placing several nodes, read `canvas.json` first and choose positions that do not overlap what is there, e.g. screens of one flow in a row with a gap of about 80px.

## Image nodes

An image node shows a picture: PNG, JPEG, WebP, etc.

- `data.path`: either an absolute path anywhere on disk, such as a generated image, or a path relative to `<projectPath>` for an image already in `asset/`. An absolute path is copied into `<projectPath>/asset/` and the node stores the copy's relative path.
- Size: omit `width` and `height` to fit the image within 480×440 at its own aspect ratio; give one to scale by aspect ratio.

### Add an image node

Call `add_node` with `{ "type": "image", "data": { "path": "/absolute/path/to/image.png" } }`. For a newly generated image, pass the file the image tool produced; do not generate it again. Add every requested output, not just the first.

### Change an image node

Call `edit_node` with a patch, e.g. a new `position`, `title` or size, or a new `data.path` to swap the picture.

## HTML nodes

An HTML node renders an editable web page in an iframe with scripts enabled. Use it for app and web UI mockups, because a page is quick to revise. Only the one HTML file is loaded as the page, so keep it self-contained: inline CSS and JS, and use data: URIs or public CDN URLs for images, fonts and libraries. Set `width` and `height` to the design's viewport, e.g. 390×844 for a phone screen or 1440×900 for a desktop page; the default is 800×600.

### Add an HTML node

1. Write the page to `<projectPath>/asset/<some-name>.html`: create the file directly, or copy an existing file there. Pick a descriptive, unique name such as `plant-care-home.html`.
2. Call `add_node` with `data.path` set to its path relative to `<projectPath>`, e.g. `{ "type": "html", "data": { "path": "asset/plant-care-home.html", "title": "Home", "width": 390, "height": 844 } }`.

### Change an HTML node

- **The page itself**: edit the HTML file at the node's `data.path` directly. Open canvases reload it automatically; no tool call is needed.
- **The node's properties** (title, position, size): call `edit_node`.

## Show the canvas

Right after `open_canvas` or `create_canvas`, and before you start working on a canvas, do both of these.

1. **Open `canvasUrl` in the current Codex task's in-app browser**, unless that canvas (`?project=<projectId>`) is already open there. Use `open_in_codex` with `target: { type: "browser", url: canvasUrl }`;
2. **Give the user a bold Markdown link to `canvasUrl` on its own line of your reply**, so they can reopen the canvas with one click after closing the browser:

   ```markdown
   **[🎨 打开画布 →](http://127.0.0.1:61974/?project=feb5e2ed-426a-434b-b92d-fb92bb52b599)**
   ```

## Runtime errors

The plugin requires Node.js available in the MCP launch environment. If it is missing, use the user's installation authorization and normal execution permissions to install/upgrade Node.js
