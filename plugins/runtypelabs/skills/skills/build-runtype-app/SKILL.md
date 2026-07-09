---
name: build-runtype-app
description: >-
  Use when building or deploying a Runtype App: a static web app hosted at
  {slug}-{shortId}.runtype.run, backed by Runtype AI APIs through an
  auto-provisioned client token. Covers the runtype.app.json manifest format,
  bundle rules, the window.__RUNTYPE_APP__ boot config, and deploying end to
  end with the deploy_app_version MCP tool, the REST API, or the CLI.
user-invocable: true
argument-hint: '[app to build or deploy]'
---

# Build a Runtype App

A Runtype App is a static bundle (HTML/CSS/JS) deployed to a real URL in seconds. No keys in the browser, no backend, no DevOps: everything dynamic (AI chat, agents) comes from Runtype APIs through a client token that Runtype injects at serve time. Deploys are instant pointer flips; rollback is activating an older version.

## The deploy loop (MCP, preferred)

1. `create_app` with a slug (lowercase, must start with a letter, max 40 chars), a name, and visibility (`unlisted` by default; `public` needs a paid plan). The response includes the app id and the final URL.
2. Build the app as a set of files. Include `index.html` and `runtype.app.json` at the root.
3. `deploy_app_version` with the app id and the files (`files` for text, `filesBase64` for binary assets). It uploads and activates in one call and returns the live URL. Pass `activate: false` to stage without serving.
4. Iterate: every `deploy_app_version` call creates a new version. Roll back anytime with `activate_app_version` and an older version id (`get_app` with `includeVersions: true` lists them).

REST equivalent: `POST /v1/apps`, then `POST /v1/apps/:id/versions` (raw `application/zip` body, or JSON `{ files, filesBase64 }`), then `POST /v1/apps/:id/activate`. CLI equivalent: `runtype apps create`, then `runtype apps deploy ./dist --app <id>`.

## The manifest (`runtype.app.json`)

Ship it at the bundle root. It declares everything the app may touch:

```json
{
  "name": "Retro Board",
  "capabilities": {
    "flows": ["flow_..."],
    "agents": ["agent_..."]
  },
  "data": [],
  "auth": "none"
}
```

- `capabilities.flows` / `capabilities.agents`: the flows and agents the app's browser sessions may dispatch (via `/v1/client/*`). Every id must exist and belong to the app owner; upload fails otherwise. Activation scopes the app's client token to exactly this set.
- `data`: reserved for the app records data plane (namespace grants). Leave `[]` for now.
- `auth`: must be `"none"`. `"optional"` / `"required"` are reserved for Log in with Runtype and are rejected at upload (422).

## Bundle rules

- `index.html` and `runtype.app.json` required at the root (a single wrapper directory like `dist/` is tolerated and stripped).
- Dotfiles (`.env`, `.git`, `.well-known`, ...) are never stored or served.
- Max 500 files; bundle size is plan-gated (10 MB on free plans, 50 MB hard cap).
- Content types are inferred from file extensions. Unmatched extension-less paths fall back to `index.html`, so client-side routing works by default.

## Use the boot config, never hard-code credentials

At serve time Runtype injects a script into every HTML entrypoint:

```js
window.__RUNTYPE_APP__ = { appId, versionId, apiUrl, clientToken }
```

Generated apps must read this object instead of embedding tokens:

```js
const { apiUrl, clientToken } = window.__RUNTYPE_APP__
const init = await fetch(`${apiUrl}/v1/client/init`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ token: clientToken }),
}).then((r) => r.json())
// then chat via /v1/client/chat with the session from init
```

The client token is origin-locked to the app's own URL and scoped to the manifest's flows/agents. Rotating it never requires a redeploy.

## Constraints to design around

- The page's CSP allows the app's own origin and the Runtype API (`connect-src 'self' {apiUrl}`). Direct `fetch` calls to third-party APIs are blocked; route dynamic behavior through Runtype flows/agents instead.
- No server-side code in v1: the bundle is static. Anything dynamic is a flow or agent dispatch.
- `unlisted` apps are served with `X-Robots-Tag: noindex`; suspended apps serve 410.
- One version is live at a time; uploads do not change what is served until activated.
