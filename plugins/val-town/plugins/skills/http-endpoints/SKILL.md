---
name: http-endpoints
description: Use when building an HTTP val — a web endpoint, API route, webhook receiver, or any val that responds to HTTP requests. Covers the handler signature, Hono usage, the endpoint URL, CORS behavior, redirects, and Val Town-specific limitations.
triggers: [http, endpoint, webhook, api, request, response, hono, web, route, fetch, cors, redirect]
---

# HTTP Endpoints

HTTP vals (`fileType: "http"`) export a request handler and run on every incoming HTTP request. Each HTTP file is assigned a public live URL — never construct it yourself; read `links.endpoint` from `list_files` or `create_file` responses, or call `fetch_val_endpoint`.

## Basic handler

```ts
// Learn more: https://docs.val.town/vals/http/
export default async function (req: Request): Promise<Response> {
  return Response.json({ ok: true });
}
```

The file must have an `export` — `export default` for the handler.

## Hono

When using Hono, export `app.fetch` (not `app`):

```ts
import { Hono } from "npm:hono";

const app = new Hono();

app.get("/", (c) => c.text("hello"));

// Always add this for full stack traces on errors:
app.onError((err) => Promise.reject(err));

export default app.fetch;
```

`serveStatic` and `cors` middleware from Hono do **not** work on Val Town. Use `serveFile` / `staticHTTPServer` from `std/utils` for static files, and rely on Val Town's default CORS (see below).

## CORS

Val Town adds permissive CORS headers by default (`Access-Control-Allow-Origin: *`). If you set **any** CORS header yourself, Val Town stops adding **all** default headers — so either handle CORS completely yourself or don't touch it at all.

## Redirects

`Response.redirect` is broken on Val Town. Use one of:

```ts
return new Response(null, { status: 302, headers: { Location: "/path" } });
// or, with Hono:
return c.redirect("/path");
```

## What's not available

- **WebSockets**: Val Town does not accept incoming WebSocket connections. Use polling, long polling, or server-sent events instead.
- **Filesystem access**: see the platform constraints. For persistent state, use `std/sqlite` or `std/blob`.

## Surfacing client-side errors

For HTML responses, add this script tag to send browser errors back to val logs (visible via `get_logs`):

```html
<script src="https://esm.town/v/std/catch"></script>
```

## Verifying changes

After editing an HTTP val, always call `fetch_val_endpoint` to confirm it returns the expected status and body. Do not report a change as done without this step.
