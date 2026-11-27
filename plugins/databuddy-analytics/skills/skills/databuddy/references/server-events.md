# Databuddy Server Events And Attribution

Use this file for Node/server tracking, raw event ingestion, browser helper utilities, and client-to-server attribution.

## Browser Helpers

Import browser helpers from `@databuddy/sdk` after installing the browser tracker.

| Helper | Use |
| --- | --- |
| `track(name, properties?)` | Send a browser custom event; queued until the tracker loads |
| `trackError(error, properties?)` | Manually send an error event from an `Error` or message; automatic errors use `autocapture: { errors: true }` |
| `identify(userId, traits?)` | Link this browser to your user ID; call again with traits to update them |
| `reset()` | Forget the user and start new anonymous/session IDs after logout; `reset({ keepVisitor: true })` forgets the user but keeps the anonymous visit |
| `setGlobalProperties(properties)` | Attach properties to every later event |
| `flush()` | Force queued browser events to send before navigation |
| `getIds(urlParams?)` | Get `{ anonymousId, sessionId, profileId }` for server attribution; IDs in URL params win |
| `getStatus()` / `ready()` | Whether the tracker is loading, tracking, or disabled and why (`consent`, `bot`, `gpc`, ...); `ready()` resolves once it loads and never rejects |
| `getTrackingParams(urlParams?)` | Build `databuddy_anonymous_id=...&databuddy_session_id=...` for cross-domain links |
| `getRevenueMetadata()` | IDs to put in Stripe payment metadata for revenue attribution |
| `optOut()` / `optIn()` | Stop or resume tracking this visitor, e.g. for consent; `optOut()` forgets them at once, while an opt-out key the page writes to `localStorage` itself counts only from the tracker's next observation. Visitors with Global Privacy Control or Do Not Track stay untracked |

For links and forms to another domain you own, set `linkDomains: ["shop.example.com"]` and the tracker adds the IDs as they are used. Use `getTrackingParams()` for redirects and URLs built in code. The destination tracker adopts them from the URL (an existing visitor or session there wins), then removes them from its address bar; set `cleanUrl` to a function that calls the router's replace in Next.js's App Router or TanStack Router. The query is still visible to the destination's server and to anything it loads before the tracker, so keep its default referrer policy, and redirect server-side when the IDs must never stay in the URL.

## Node Events

```ts
import { Databuddy } from "@databuddy/sdk/node";

const client = new Databuddy({
  apiKey: process.env.DATABUDDY_API_KEY!,
  websiteId: process.env.DATABUDDY_WEBSITE_ID,
});

await client.track({
  name: "webhook_processed",
  properties: { provider: "github", status: "success" },
  source: "server",
});

await client.flush();
```

Serverless and short-lived runtimes must call `flush()` before returning.

## Server-Side Attribution

For a browser action that completes on the server, pass browser IDs to the server and map them onto the Node SDK event. API keys stay server-side; anonymous/session IDs can cross the wire.

| Flow | Pattern |
| --- | --- |
| Browser `fetch` to API route | send `anonymousId` and `sessionId` from `getIds()` in the JSON body |
| Form post or server action | populate hidden fields from `getIds()` before submit |
| Redirect to another owned domain | append `getTrackingParams()` to the URL and install Databuddy on the destination |
| Async job started by a user | persist `anonymousId` and `sessionId` with the job record; reuse them on completion/failure |
| External webhook after user setup | persist Databuddy IDs during setup and reuse them if the webhook can be tied back |
| Pure server event | omit session IDs; include `source`, `namespace`, `status`, and operational properties |

```tsx
// client
import { getIds } from "@databuddy/sdk";

async function createProject(projectType: string) {
  const { anonymousId, sessionId } = getIds();

  await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      anonymousId,
      sessionId,
      projectType,
    }),
  });
}
```

```ts
// server
import { Databuddy } from "@databuddy/sdk/node";

const databuddy = new Databuddy({
  apiKey: process.env.DATABUDDY_API_KEY!,
  websiteId: process.env.DATABUDDY_WEBSITE_ID!,
});

export async function POST(request: Request) {
  const { anonymousId, sessionId, projectType } = await request.json();

  await databuddy.track({
    name: "project_created",
    anonymousId,
    sessionId,
    properties: { project_type: projectType },
    source: "server",
  });

  await databuddy.flush();

  return Response.json({ ok: true });
}
```

For form posts, put the same IDs into hidden inputs before submit:

```tsx
import { getIds } from "@databuddy/sdk";

function addTrackingFields(form: HTMLFormElement) {
  const { anonymousId, sessionId } = getIds();

  for (const [name, value] of Object.entries({ anonymousId, sessionId })) {
    if (!value) {
      continue;
    }

    let input = form.elements.namedItem(name);
    if (!(input instanceof HTMLInputElement)) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.append(input);
    }

    input.value = value;
  }
}
```

Attribution can still work partially when one ID is missing, but both IDs give the strongest session continuity. The server event also needs website scoping through `websiteId`, `DATABUDDY_WEBSITE_ID`, or API key resource scoping.

To link a backend user, call `client.identify({ profileId, anonymousId, traits })` with a `track:events` key, passing the browser's `getIds().anonymousId` value to attach that device's earlier activity. Server events for a known user can also carry `profileId` alongside `anonymousId` and `sessionId`.

## Raw Event Tracking

Prefer SDKs unless the user explicitly wants HTTP.

```bash
curl -X POST https://basket.databuddy.cc/track \
  -H "Authorization: Bearer dbdy_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"name":"signup_completed","websiteId":"your-client-id"}'
```

Raw `/track` payload fields mirror the Node SDK shape: `name`, `properties`, `anonymousId`, `sessionId`, `timestamp`, `namespace`, `source`, and `websiteId`.
