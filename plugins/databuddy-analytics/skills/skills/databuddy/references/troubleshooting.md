# Databuddy Troubleshooting

Use this file for CSP, blockers, auth, host confusion, missing events, missing attribution, and feature flag debugging.

## Checks

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Script blocked by CSP | Missing CDN in `script-src` | Add `https://cdn.databuddy.cc` to `script-src` |
| Events fail under strict CSP | Missing basket in `connect-src` | Add `https://basket.databuddy.cc` to `connect-src` |
| Flags fail under strict CSP | Missing API host in `connect-src` | Add `https://api.databuddy.cc` to `connect-src` |
| Pixel mode fails | Missing basket in `img-src` | Add `https://basket.databuddy.cc` to `img-src` when `usePixel` is enabled |
| Script never appears | Component mounted too low or only on one route | Mount once near the root layout, `RouterView`, or `NuxtPage` |
| No browser events | Wrong or missing `clientId` | Check env var and rendered `data-client-id` |
| `getIds()` returns nulls, or no events | Tracker still loading, or off for this visitor | `await ready()` or read `getStatus()`: `disabled` names the reason (`consent`, `opt_out`, `gpc`, `dnt`, `bot`, `localhost`, `storage`, `config`, `stopped`, or `unsupported_script` when `consent`/`beforeSend` meet a script too old for them; an older script already running may still retry requests it had started, so reload with a current script), `unavailable` says the script failed or never loaded |
| Requests blocked before network | Ad/tracker blocker or privacy extension | Test in a clean profile and document expected blockers |
| 401 from API | Missing or invalid API key | Use `x-api-key: dbdy_...` or Bearer server-side only |
| 403 from API or `/track` | API key lacks scope | Use `read:data` for queries, `track:events` for server events, `manage:flags` for flag management |
| Query API works but events do not | Wrong host | Queries use `api.databuddy.cc`; events use `basket.databuddy.cc` |
| Server events sent but not visible for a site | No website scope | Provide `websiteId`, `DATABUDDY_WEBSITE_ID`, or a resource-scoped key |
| Server event visible but unattributed | Browser IDs not passed through | Send `getIds()` output (`anonymousId`, `sessionId`) to the server and pass both on the event |
| Events lost in serverless | Queue not flushed | Call `await client.flush()` before the function exits |
| Flags always return defaults | Read before init, wrong client id, or blocked API host | Call `waitForInit()` on server; verify `clientId`, user context, and CSP |
| Browser requests rejected by Databuddy | Domain/origin not allowed for the website | Verify the website domain and allowed origins in Databuddy settings |
| DevTools flag override changes behavior | Local override is active | Clear the override before validating real flag results |

## CSP Baseline

```http
Content-Security-Policy:
  script-src 'self' https://cdn.databuddy.cc;
  connect-src 'self' https://basket.databuddy.cc https://api.databuddy.cc;
```

Add `img-src https://basket.databuddy.cc` if `usePixel` is enabled.
