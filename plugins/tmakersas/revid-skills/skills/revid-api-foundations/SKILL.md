---
name: revid-api-foundations
description: Foundation knowledge for every Revid skill — MCP server install, the render_video / get_project_status / export_video tools, the workflow discriminator, and the response envelope. Load this once at session start; specific skills build on it.
metadata: {"openclaw":{"requires":{"config":["REVID_API_KEY"]}}}
---

# Revid foundations

Everything every other skill in this library depends on. **Read this once.**

> **What changed:** Skills now talk to Revid through the **Revid MCP server**
> (`https://www.revid.ai/api/mcp`) instead of constructing raw HTTPS requests.
> The JSON shape is identical to the public API — only the transport changed.
> The HTTPS endpoints still exist as a fallback (see [§ Direct HTTPS fallback](#direct-https-fallback)).

## When to use

Always — but transparently. Other skills assume the agent already knows:

- how to authenticate to the MCP
- which MCP tool to call for a render
- how to wait for the result
- the response envelope shape

## Install the Revid MCP server

Add this once to your agent's MCP config (Claude Code, Cursor, OpenClaw, Codex,
Gemini CLI — any MCP-capable client):

```json
{
  "mcpServers": {
    "revid": {
      "url": "https://www.revid.ai/api/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_REVID_API_KEY"
      }
    }
  }
}
```

Get a key at <https://www.revid.ai/account>. Any of these headers also works:
`x-revid-api-key`, `x-api-key`, `key`.

That's the entire setup. No SDK, no per-skill env var, no polling glue.

## The shape of every Revid call

```
tool: render_video
args: { workflow: "<one-of-10>", source: { … }, … }
   ↓
{ ok: true, data: { pid: "p_…", … } }
   ↓
tool: get_project_status
args: { pid: "p_…" }
   ↓ (call again every ~5–8 s until status === "ready")
{ ok: true, data: { status: "ready", videoUrl: "https://cdn.revid.ai/v/…mp4" } }
   ↓ (optional, to force a fresh export)
tool: export_video
args: { pid: "p_…", fileName: "demo.mp4" }
```

That's the entire contract. Skills only differ in the body of `render_video`.

## The 13 MCP tools

| Tool | Purpose |
|---|---|
| `render_video` | Start a render. Returns `pid`. |
| `get_project_status` | Poll a `pid` until `status === "ready"`. |
| `export_video` | Force a fresh mp4 export from an existing `pid`. |
| `calculate_credits` | Estimate credit cost without rendering. *No API key required.* |
| `list_projects` | List the user's recent renders. |
| `rename_project` | Rename an existing project. |
| `clone_voice` | Clone a custom voice from a sample URL (Elite plan). |
| `list_characters` / `create_character` / `delete_character` | Manage saved consistent characters / avatars. |
| `schedule_publish` | Queue the rendered mp4 into the next publishing slot. |
| `publish_now` | Publish the rendered mp4 immediately to a connected channel. |
| `buy_credit_pack` | Trigger an auto-top-up purchase. |

The 11 content-skill `SKILL.md` files in this catalog wrap **only**
`render_video` + `get_project_status` (+ `export_video` when needed).

## The 10 workflows

| Workflow | Use when input is… |
|---|---|
| `script-to-video` | Already-written script (text). |
| `prompt-to-video` | A one-liner idea — the API writes the script. |
| `article-to-video` | Any URL with text content (blog/product/news). |
| `avatar-to-video` | A script + an avatar image (talking-head). |
| `ad-generator` | A product description — AI writes ad hooks. |
| `audio-to-video` | A voice/music recording you want visualized. |
| `music-to-video` | A music URL + visuals. |
| `motion-transfer` | A reference image animated with motion from a clip. |
| `caption-video` | An existing video that needs captions. |
| `static-background-video` | A voiceover over a fixed background. |

Pick the workflow that matches the *input shape*, not the *output you want*.
The same `script-to-video` workflow can produce a Reel, a YouTube short, or a
LinkedIn square — that's just `aspectRatio`.

## Source mapping

Each workflow expects one of these `source.*` fields:

| Workflow | Field |
|---|---|
| `script-to-video` | `source.text` |
| `prompt-to-video` | `source.prompt` (+ optional `source.stylePrompt`, `source.durationSeconds`) |
| `article-to-video` | `source.url` (+ optional `source.scrapingPrompt`) |
| `ad-generator` | `source.prompt` (the product description) |
| `avatar-to-video` | `source.text` (script) + top-level `avatar.url` |
| `music-to-video` / `caption-video` / `motion-transfer` | `source.url` |
| `static-background-video` | `source.text` + `media.backgroundVideo` |

If you put text in the wrong field, `render_video` returns `ok: false` with a
schema error.

## Common knobs every skill should set

1. **`aspectRatio`** — pick from the consumer surface:
   - Reels / TikTok / Shorts → `"9:16"`
   - LinkedIn / Instagram feed → `"1:1"`
   - YouTube long-form → `"16:9"`

2. **`voice.enabled`** — `true` for narrated content; `false` for music-only or
   caption-only outputs.

3. **`captions.enabled`** — keep `true` by default. Most short-form watches happen
   on mute.

4. **`music.enabled`** — `true` for promo / ad / story content; `false` for
   talking-head where the avatar voice should breathe.

5. **`render.resolution`** — `"1080p"` is the right default. Use `"720p"` for
   cheap previews; `"4k"` only when downstream needs it.

6. **`media.quality` / `media.videoModel`** — start at `"pro"`. Bump to
   `"ultra"` / `"veo3"` / `"sora2"` only when the cost is justified. Call
   **`calculate_credits`** first with the same payload to get a price estimate
   without spending.

7. **`webhookUrl`** — pass it whenever the caller can receive webhooks. Skips
   polling entirely.

## Reading the response envelope

Every MCP tool returns:

```json
{
  "ok": true,
  "status": 200,
  "endpoint": "/api/public/v3/render",
  "method": "POST",
  "data": { /* the public-API response body */ }
}
```

For `render_video`, success looks like:

```json
{ "ok": true, "data": { "success": 1, "pid": "p_…", "workflow": "…" } }
```

Failure:

```json
{ "ok": false, "status": 422, "error": "human-readable string" }
```

Skills should always check `ok === true` *and* `data.success === 1` before
proceeding.

## Polling

After `render_video`, call `get_project_status` until `data.status === "ready"`:

```pseudo
function waitForRevid(pid, opts = { timeoutMs: 600_000 }):
  deadline = now() + opts.timeoutMs
  delay    = 5_000   # ms

  loop while now() < deadline:
    res = mcp.call("get_project_status", { pid })

    if not res.ok:
      throw Error(res.error or "status check failed")

    body = res.data
    if body.status == "ready":
      return body                     # body.videoUrl present
    if body.status == "failed":
      throw Error(body.error or "render failed")

    sleep(delay)
    if body.progress > 30: delay = 8_000

  throw TimeoutError("pid $pid not ready after $opts.timeoutMs ms")
```

In production prefer setting `webhookUrl` in `render_video` and skip polling.

## Failure modes

The two most common errors every skill must handle:

- **`scrape failed` / `403` from source URL** — the page is JS-only or blocks
  bots. Either pre-scrape it yourself and switch to `script-to-video`, or pass
  `source.scrapingPrompt` with the manual title + body.
- **`insufficient_credits`** — drop `media.quality` / `videoModel` /
  `render.resolution` and retry, or call `buy_credit_pack`.

## Direct HTTPS fallback

The MCP server is a thin wrapper around the public API. If your agent runtime
can't load MCP servers, the same payload works as a raw POST:

```http
POST https://www.revid.ai/api/public/v3/render
Content-Type: application/json
key: <REVID_API_KEY>

<the render_video payload>
```

It returns `{ "success": 1, "pid": "p_…" }`. Poll
`GET https://www.revid.ai/api/public/v3/status?pid=p_…` with the same `key` header.

Each `examples/run.sh` in this repo uses this fallback path so you can smoke-test
without an MCP-capable client.

## See also

- Revid MCP guide: <https://www.revid.ai/mcp>
- Full Revid Public API v3 spec: <https://documenter.getpostman.com/view/36975521/2sBXcGEfaB>
- The other Revid skills in this catalog apply this foundation to specific
  content types (article, product page, blog, tweet, PDF, etc.).
