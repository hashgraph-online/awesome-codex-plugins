---
name: client-side-js
description: Use when a val needs to ship JavaScript that runs in the browser — React apps, vanilla DOM scripts, canvas/games, htmx/Alpine, or any client-side module beyond a single inline snippet. Explains how Val Town serves transpiled .ts/.tsx/.jsx modules with no build step, how the browser resolves their imports, and how to load third-party deps.
triggers: [client, browser, frontend, script, module, esm, bundle, build, hydrate, react-dom, mount, interactive, canvas, alpine, htmx, serveFile, type=module]
---

# Client-side JavaScript

Val Town has **no build step and no bundler**. A client-side module is just a file
in your val that you serve over HTTP; Val Town transpiles it per request. You point
a `<script type="module">` at a route that returns the file, and the browser runs
it. There is nothing to configure (no webpack/vite/esbuild).

## Serving a module

`serveFile` from `std/utils` reads a file and serves it with the correct
`Content-Type`. For `.ts`, `.tsx`, and `.jsx` it **transpiles to JavaScript** —
strips types, compiles JSX — and serves `text/javascript`. You serve the source
file; the browser receives runnable JS.

```ts
import { serveFile } from "https://esm.town/v/std/utils/index.ts";

// in any HTTP handler — serve a client module at some URL path
app.get("/app.tsx", (c) => serveFile("/app.tsx"));
```

Then load it from your HTML:

```html
<script type="module" src="/app.tsx"></script>
```

The path you serve at and the file's location are up to you. A common shortcut is a
wildcard that serves a whole directory of modules and assets:

```ts
app.get("/client/**/*", (c) => serveFile(c.req.path));
```

`serveFile` defaults to the current val. If you call it from a non-entrypoint file
and paths don't resolve, pass `import.meta.url` as the second argument.

### Alternative: serve directly from esm.town

Every val file already has a public esm.town URL that transpiles on demand, so you
can skip `serveFile` and point a script straight at it:

```html
<script type="module" src="https://esm.town/v/youruser/yourval/app.tsx"></script>
```

`serveFile` is usually preferred because the module is served same-origin from a
path you control, and you don't have to hardcode your own val URL.

## How imports resolve in the browser

The transpiler does not bundle or rewrite imports — it only strips types and JSX.
So every import in a client module must be something the **browser** can fetch as a
URL:

- **Local imports need explicit extensions.** `import { x } from "./util.ts"`
  resolves to `/util.ts` (or relative to the served path) and must be served too —
  by the same route or a wildcard. Omitting the extension (`./util`) 404s.
- **Third-party deps need full ESM URLs.** Bare specifiers like `import React from
  "react"` don't resolve in the browser. Import from a CDN such as esm.sh, with
  versions pinned:

  ```ts
  import { createRoot } from "https://esm.sh/react-dom@18.2.0/client";
  ```

  An [import map](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script/type/importmap)
  in the HTML is an option if you want bare specifiers in client code.

The same model works for any client code — React, vanilla DOM scripts, a canvas
game loop, Alpine, htmx. Only the imports differ; for a plain `.ts` module with no
dependencies there's nothing to load from a CDN at all.

## React specifics

Pin all React-family imports to the same version (18.2.0) and pass
`?deps=react@18.2.0,react-dom@18.2.0` on libraries that depend on React. Mismatched
copies cause `Cannot read properties of null (reading 'useState')`. See the
`react-ui` skill for JSX and styling conventions.

## What not to do

- **No app logic in inline `<script>` blobs or template-string HTML.** Put client
  code in real `.ts`/`.tsx` files so it's typed, linted, and reviewable. A few lines
  of inline bootstrap are fine; the app is not.
- **No bundler / build command.** There is no build step to add.
- **`serveStatic` from Hono does not work** on Val Town — use `serveFile`.

## Verifying changes

Fetch the module's URL (e.g. `/app.tsx`) and confirm it returns `text/javascript`,
not HTML or an error. Add `https://esm.town/v/std/catch` to the HTML shell to pipe
browser errors into `get_logs`, then load the page and check the logs. Don't report
the change as done without both.
