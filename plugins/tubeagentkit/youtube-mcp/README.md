<p align="center">
  <a href="https://getyoutubetranscript.com">
    <img src="public/brand/logo.png" width="140" height="140" alt="GetYouTubeTranscript" />
  </a>
</p>

<h1 align="center">YouTube MCP Server: Transcripts, Search, Channels & Playlists</h1>

<p align="center">
  A remote MCP server for YouTube: transcripts, video and channel search, channel browsing, in-channel search, and playlist extraction.<br/>
  API key <b>or</b> OAuth 2.1 sign-in. Free tier, no card required.
</p>

<p align="center">
  <a href="https://cursor.com/en/install-mcp?name=youtube-transcript&config=eyJ1cmwiOiJodHRwczovL2dldHlvdXR1YmV0cmFuc2NyaXB0LmNvbS9hcGkvbWNwIn0="><img alt="Install in Cursor" src="https://img.shields.io/badge/Cursor-Install_MCP-000000?style=for-the-badge&logo=cursor&logoColor=white"/></a>
  <a href="https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%7B%22name%22%3A%22youtube-transcript%22%2C%22url%22%3A%22https%3A%2F%2Fgetyoutubetranscript.com%2Fapi%2Fmcp%22%7D"><img alt="Install in VS Code" src="https://img.shields.io/badge/VS_Code-Install_MCP-0098FF?style=for-the-badge&logo=visualstudiocode&logoColor=white"/></a>
</p>

<p align="center">
  <a href="https://getyoutubetranscript.com"><img src="https://img.shields.io/badge/Website-getyoutubetranscript.com-FF3B00?style=for-the-badge" alt="Website"/></a>
  <a href="https://getyoutubetranscript.com/docs"><img src="https://img.shields.io/badge/Docs-API_Reference-06B6D4?style=for-the-badge&logo=readthedocs&logoColor=white" alt="Docs"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-4CAF50?style=for-the-badge" alt="MIT License"/></a>
</p>

Thirteen tools, one hosted endpoint, no local install, for Claude, ChatGPT, Cursor, VS Code, Windsurf, and 15+ other MCP-compatible clients.

```
https://getyoutubetranscript.com/api/mcp
```

**Quick taste:**

```txt
Search @veritasium for videos about black holes, pull the transcript of the
two best matches, and tell me where they disagree.
```

The agent chains `search_channel_videos` and `get_youtube_transcript` on its own. No code on your side.

---

## Why this MCP

|  | This MCP | Typical single-purpose YouTube MCP |
|---|---|---|
| Hosting | ✅ Remote (no local install, no build step) | ❌ Local stdio process to manage |
| Tools | ✅ 7 (transcript, search, channel latest/search/videos, playlist, credits) | ❌ Usually 1 (transcript only) |
| YouTube search (video *and* channel) | ✅ Yes | ❌ No |
| Full channel upload history, paginated | ✅ Yes | ❌ No |
| In-channel search | ✅ Yes | ❌ No |
| Auth | ✅ API key **and** OAuth 2.1 (DCR + CIMD) | ❌ Usually neither |
| Agent-friendly errors | ✅ Stable error codes, human-readable messages | ❌ Bare HTTP codes |

---

## Install as an Agent Plugin

This repo root is also an [Agent Plugins 1.0.0](https://agent-plugins.org/specification) package. It bundles the MCP server with a `youtube` skill that tells the agent which tool to use when, what each one costs, and how to avoid wasting credits.

```text
plugin.json                # plugin manifest
mcp.json                   # hosted MCP server (streamable-http, OAuth, no key in the file)
skills/youtube/SKILL.md    # when and how to use the 13 tools
```

In VS Code, run **Chat: Install Plugin From Source** and paste `https://github.com/tubeagentkit/youtube-mcp`. Other clients that support Agent Plugins can point at this repo or a local clone. For Cursor there is a separate [plugin repo](https://github.com/tubeagentkit/youtube-transcript-cursor-plugin).

The package holds no credentials. Check the manifests against the published schemas yourself:

```sh
curl -sO https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
curl -sO https://agent-plugins.org/schemas/1.0.0/mcp.schema.json
npx ajv-cli@5 validate --spec=draft2020 -s plugin.schema.json -d plugin.json
npx ajv-cli@5 validate --spec=draft2020 -s mcp.schema.json -d mcp.json
```

### ChatGPT and Codex

The same `plugin.json` carries the ChatGPT/Codex plugin directory listing under `extensions.com.openai` (other clients ignore it). `scripts/build-openai-zip.sh` checks it against OpenAI's field limits and builds the upload ZIP in `dist/`, with only `plugin.json`, `mcp.json`, `skills/` and `assets/`.

---

## Quick Install

> **Requirements:** a free [getyoutubetranscript.com](https://getyoutubetranscript.com/?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp) account ([sign up](https://getyoutubetranscript.com/?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp) — 100 credits, no card) and an API key from your [dashboard](https://getyoutubetranscript.com/dashboard?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp) — **or** just connect via OAuth and skip the key entirely (see [Authentication](#authentication) below).

> **Tip:** clients that support MCP OAuth can skip the `headers` block in the snippets below and sign in through the browser instead.

> **Tip:** to stop repeating "use the transcript tool", add a standing instruction to your client's rules or custom instructions, for example: *"When I share a YouTube link, fetch its transcript with the youtube-transcript MCP before answering."*

<details>
<summary><b>Claude Code (CLI)</b></summary>

```sh
claude mcp add --transport http youtube-transcript https://getyoutubetranscript.com/api/mcp --header "Authorization: Bearer YOUR_API_KEY"
```

</details>

<details>
<summary><b>Claude Desktop / Claude Web (OAuth)</b></summary>

1. Settings → **Connectors** → **Add custom connector**
2. Name: `YouTube Transcript` · URL: `https://getyoutubetranscript.com/api/mcp`
3. Click **Add**, then **Connect** and sign in via browser — no API key needed.

</details>

<details>
<summary><b>Cursor</b></summary>

`Settings` → `Features` → `MCP` → `Add New MCP Server` — Type: `SSE`/`HTTP`, URL: `https://getyoutubetranscript.com/api/mcp`.

Or edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "url": "https://getyoutubetranscript.com/api/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

</details>

<details>
<summary><b>VS Code</b></summary>

```json
"mcp.servers": {
  "youtube-transcript": {
    "type": "http",
    "url": "https://getyoutubetranscript.com/api/mcp",
    "headers": { "Authorization": "Bearer YOUR_API_KEY" }
  }
}
```

</details>

<details>
<summary><b>ChatGPT</b></summary>

Enable Developer Mode, then `Settings` → `Connected Apps` → `Add` → URL `https://getyoutubetranscript.com/api/mcp`. Leave Client ID/Secret blank for Dynamic Client Registration, or use OAuth sign-in directly.

</details>

<details>
<summary><b>Windsurf</b></summary>

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "serverUrl": "https://getyoutubetranscript.com/api/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

</details>

<details>
<summary><b>Cline</b></summary>

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "url": "https://getyoutubetranscript.com/api/mcp",
      "type": "streamableHttp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

</details>

<details>
<summary><b>Zed</b></summary>

```json
{
  "context_servers": {
    "youtube-transcript": {
      "source": "remote",
      "url": "https://getyoutubetranscript.com/api/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

</details>

<details>
<summary><b>Roo Code</b></summary>

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "type": "streamable-http",
      "url": "https://getyoutubetranscript.com/api/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

</details>

<details>
<summary><b>Amp</b></summary>

```sh
amp mcp add youtube-transcript https://getyoutubetranscript.com/api/mcp --header "Authorization: Bearer YOUR_API_KEY"
```

</details>

<details>
<summary><b>Augment Code</b></summary>

```json
"augment.advanced": {
  "mcpServers": [
    {
      "name": "youtube-transcript",
      "url": "https://getyoutubetranscript.com/api/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  ]
}
```

</details>

<details>
<summary><b>Kilo Code</b></summary>

In `.kilocode/mcp.json`:

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "type": "streamable-http",
      "url": "https://getyoutubetranscript.com/api/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

</details>

<details>
<summary><b>JetBrains AI Assistant</b></summary>

`Settings` → `Tools` → `AI Assistant` → `MCP`:

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "url": "https://getyoutubetranscript.com/api/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

</details>

### 30-second example

```txt
Summarize this video for me: https://youtu.be/dQw4w9WgXcQ
```

The agent calls `get_youtube_transcript` and summarizes the result. If you connected via OAuth, there's no key to configure at all — just approve the connection once.

---

## Run locally (stdio)

Prefer a local process? [`server/`](./server) is an open-source stdio MCP server with the same 13 tools, built on the official MCP TypeScript SDK. It calls the public [REST API](https://getyoutubetranscript.com/docs?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp) with your API key.

```sh
git clone https://github.com/tubeagentkit/youtube-mcp
npm install --prefix youtube-mcp/server
```

Then point your client at it, e.g. Claude Desktop / Cursor:

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "node",
      "args": ["/absolute/path/to/youtube-mcp/server/index.js"],
      "env": { "GYT_API_KEY": "sk_live_your_key_here" }
    }
  }
}
```

Live integration test (uses only free tools): `GYT_API_KEY=sk_live_... npm test --prefix server`

---

## Authentication

### API Key

Universal, works with every MCP client. Get one free (100 credits, no card) at the [dashboard](https://getyoutubetranscript.com/dashboard?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp), then send it as a Bearer token:

```json
"headers": { "Authorization": "Bearer sk_live_your_key_here" }
```

### OAuth 2.1

No manual key management — sign in via browser, the server handles the rest.

- **Dynamic Client Registration (DCR):** supported for clients that self-register at connect time (Claude Desktop/Web, ChatGPT, and most others).
- **Client ID Metadata Documents (CIMD):** supported per the current MCP spec (2026-07-28) for clients that host their own metadata document — the more modern alternative to DCR, no shared secret required.
- First connection opens a consent screen showing exactly what access is being granted; approve once and you're connected.

Both methods issue a token scoped and audience-bound to this specific MCP server — it can't be replayed against any other API.

---

## Available Tools

All thirteen tools are exposed automatically once you connect. **1 credit = 1 successful request.** Failed or rate-limited calls never consume credits.

### 1. `get_youtube_transcript`

Fetch the full transcript for a YouTube video, plus its title/author/thumbnail metadata.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `video_url` | string | **required** | YouTube URL (full or short) or an 11-character video ID |
| `language` | string | optional | Language code, e.g. `en`, `es`. Defaults to `en` |
| `send_metadata` | boolean | optional | Include title/author/thumbnail. Defaults to `true` |
| `timestamps` | boolean | optional | One line per caption, each starting with its `[m:ss]` start time (`[h:mm:ss]` past an hour). Defaults to `false` (one block of text) |

**Cost:** 1 credit, with or without `timestamps`.

### 2. `get_transcript_languages`

List the caption languages a video offers, creator-uploaded or auto-generated, and which one a default request returns.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `video_url` | string | **required** | YouTube URL (full or short) or an 11-character video ID |

An empty list means the video has captions turned off. Not needed for an ordinary transcript request: `get_youtube_transcript` already reports the language it returned.

**Cost:** 1 credit.

### 3. `search_youtube`

Search YouTube for videos or channels, paginated.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `query` | string | required unless `continuation` set | Search query |
| `search_type` | `"video"` \| `"channel"` | optional | Defaults to `"video"` |
| `continuation` | string | optional | Opaque token from a previous response — fetches the next page |

**Cost:** 1 credit/page.

### 4. `get_channel_latest_videos`

Get a channel's metadata plus its most recent uploads.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | **required** | `@handle`, channel URL, or `UC…` channel ID |

**Cost:** 1 credit.

### 5. `search_channel_videos`

Search within one specific channel's videos.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | required unless `continuation` set | `@handle`, channel URL, or `UC…` ID |
| `query` | string | required unless `continuation` set | Query to search within the channel |
| `continuation` | string | optional | Opaque token — fetches the next page |

**Cost:** 1 credit/page.

### 6. `list_channel_videos`

List a channel's uploads beyond its latest videos: older episodes, its most popular videos, its Shorts, or its past live streams.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | required unless `continuation` set | `@handle`, channel URL, or `UC…` ID |
| `tab` | string | optional | `videos` (default), `shorts`, or `streams` (the Live tab). First page only |
| `sort` | string | optional | `latest` (default), `popular`, or `oldest`. First page only |
| `continuation` | string | optional | Opaque token — fetches the next page |

**Cost:** 1 credit/page.

### 7. `list_channel_playlists`

List the playlists a channel has published. Pass a playlist's `id` to `list_playlist_videos` to see its videos.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | required unless `continuation` set | `@handle`, channel URL, or `UC…` ID |
| `continuation` | string | optional | Opaque token — fetches the next page |

**Cost:** 1 credit/page.

### 8. `list_channel_posts`

List a channel's community posts: text, links, likes, comments and any attached image.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | required unless `continuation` set | `@handle`, channel URL, or `UC…` ID |
| `continuation` | string | optional | Opaque token — fetches the next page |

**Cost:** 1 credit/page.

### 9. `get_related_videos`

The videos YouTube suggests next to a video, each with title, video ID, link, channel, views, age and length.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `video_url` | string | **required** | YouTube URL (full or short) or an 11-character video ID |

**Cost:** 1 credit.

### 10. `get_channel_banner`

A channel's uncropped banner, every crop size YouTube serves, and its avatar. `has_banner` is `false` when the channel has none.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | **required** | `@handle`, channel URL, or `UC…` ID |

**Cost:** 1 credit.

### 11. `get_video_dislikes`

A video's likes, dislikes, star rating and view count. YouTube no longer publishes dislikes, so these are estimates.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `video_url` | string | **required** | YouTube URL (full or short) or an 11-character video ID |

**Cost:** 1 credit.

### 12. `list_playlist_videos`

Get every video in a YouTube playlist.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `playlist` | string | required unless `continuation` set | Playlist URL or ID |
| `continuation` | string | optional | Opaque token — fetches the next page |

**Cost:** 1 credit/page.

### 13. `get_credits` <sub>· **FREE**</sub>

Check the remaining credit balance for your key/account. No parameters.

**Cost:** Free.

---

## Use Cases & Prompts

| Use Case | Example Prompt |
|---|---|
| 📝 **Summarize a video** | "Summarize the key points from this video: [URL]" |
| 🔍 **Research a topic** | "Search YouTube for the 5 most-watched videos on neural radiance fields; summarize each." |
| 🧠 **Study notes** | "Create study notes from this MIT lecture series playlist: [PLAYLIST URL]" |
| 📡 **Monitor a creator** | "Each morning, list new uploads from @hubermanlab and tell me which to watch." |
| 🏛️ **Build a content database** | "Pull every video from @veritasium and store title + transcript." |
| 🎯 **Channel research** | "Search inside @MKBHD for any video about [topic] and summarize the takeaways." |
| ✍️ **Repurpose content** | "Turn this video into a 1,500-word blog post: [URL]" |

---

## Pricing & Rate Limits

| Plan | Price | Credits | Rate Limit |
|---|---|---|---|
| **Free** | $0 | 100 credits on signup | 60 req/min |
| **Monthly** | $5/month | 1,000 credits/month | 200 req/min |
| **Annual** | $4.50/mo ($54/yr) | 1,000 credits/month | 300 req/min |
| **Starter** | $19/month | 7,500 credits/month | 300 req/min |
| **Pro** | $49/month | 25,000 credits/month | 400 req/min |
| **Scale** | $99/month | 60,000 credits/month | 600 req/min |

- **1 credit** = 1 successful request. Failed/rate-limited requests don't consume credits.
- `get_credits` is the only free tool.
- [Manage billing →](https://getyoutubetranscript.com/dashboard?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp)

---

## Troubleshooting

<details>
<summary><b>Authentication errors (401)</b></summary>

- If using an API key: confirm it starts with `sk_live_` and has no extra whitespace
- If using OAuth: try disconnecting and reconnecting the connector
- Confirm the key/connection is still active in your [dashboard](https://getyoutubetranscript.com/dashboard?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp)
</details>

<details>
<summary><b>No credits (402)</b></summary>

Check your balance and top up or upgrade at the [dashboard](https://getyoutubetranscript.com/dashboard?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp).
</details>

<details>
<summary><b>Video not available (404)</b></summary>

- The video may not have captions enabled
- It may be private, age-restricted, or region-locked
- Confirm it plays in a real browser first
</details>

<details>
<summary><b>Rate limiting (429)</b></summary>

Back off and retry after a short delay — don't hammer it in a tight loop.
</details>

<details>
<summary><b>OAuth connection issues</b></summary>

- Clear cookies for getyoutubetranscript.com and retry
- Ensure popup/redirect blockers aren't interfering with the consent screen
- If your client supports both DCR and CIMD, try the other registration method
</details>

---

## Verification

This repo contains the MIT-licensed source of the local stdio MCP server in [`server/`](./server)
(tool definitions, input validation, API calls, error mapping), plus the manifests for the
hosted endpoint. The hosted endpoint and the REST API behind both are run by
getyoutubetranscript.com and are not open source. To check either one yourself:

- **Run the local server's live test** — `GYT_API_KEY=sk_live_... npm test --prefix server`
  starts `server/index.js` over stdio, lists all 13 tools, and calls the free ones.
- **Run [`verify.js`](./verify.js) against the hosted endpoint** — zero dependencies, zero auth required:
  ```sh
  node verify.js
  ```
  It performs the real MCP handshake (`initialize` then `tools/list`) against the live
  endpoint and prints the server's actual response, including all 13 real tool schemas.
  Tool *discovery* is public; only tool *calls* require an API key or OAuth token (see
  [Authentication](#authentication)).
- **Independently verified by four third-party MCP directories**, each of which connected
  to the live endpoint and confirmed the tools themselves (not just took our word for it):
  - [Official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=getyoutubetranscript) — `com.getyoutubetranscript/youtube-transcript-and-youtube-search`, published via domain-ownership-verified HTTP `mcp-publisher`
  - [Smithery](https://smithery.ai/server/@tubeagentkit/youtube-transcript) — its own scanner connected and discovered all 6 tools
  - [Glama](https://glama.ai/mcp/servers/tubeagentkit/youtube-mcp)
  - [LobeHub](https://market.lobehub.com/s/plugins/tubeagentkit-youtube-transcript)
- **Live since 2026-09-12** — the OAuth 2.1 (DCR + CIMD) flow has also been exercised
  end-to-end by a real third-party client (Smithery) connecting via CIMD, which surfaced
  and got a real interop fix along the way (see commit history).

---

## Also available as a REST API

Building an app instead of an agent? The same backend is a plain JSON REST API — see the [Agent Skill repo](https://github.com/tubeagentkit/youtube-transcript-skills) for the full endpoint reference, or the [dashboard](https://getyoutubetranscript.com/dashboard?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp) to get a key directly.

Base URL: `https://getyoutubetranscript.com/api/v1`

---

## Connect

- 🌐 **Website:** [getyoutubetranscript.com](https://getyoutubetranscript.com/?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp)
- 🔑 **Dashboard:** [getyoutubetranscript.com/dashboard](https://getyoutubetranscript.com/dashboard?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp)
- 🧩 **Agent Skill version:** [tubeagentkit/youtube-transcript-skills](https://github.com/tubeagentkit/youtube-transcript-skills)

## Disclosure

getyoutubetranscript.com is an independent product and is not affiliated with or endorsed by YouTube or Google.

## Related projects

Other ways to use the [GetYouTubeTranscript API](https://getyoutubetranscript.com/?utm_source=github&utm_medium=readme&utm_campaign=youtube-mcp):

- [youtube-transcript-api](https://github.com/tubeagentkit/youtube-transcript-api): YouTube Transcript API docs, endpoint reference, OpenAPI spec and examples in curl, Python, JavaScript, Go and PHP
- [youtube-transcript-api-python](https://github.com/tubeagentkit/youtube-transcript-api-python): YouTube Transcript API SDK for Python
- [youtube-transcript-api-node](https://github.com/tubeagentkit/youtube-transcript-api-node): YouTube Transcript API SDK for Node.js / TypeScript
- [youtube-transcript-skills](https://github.com/tubeagentkit/youtube-transcript-skills): YouTube transcript Agent Skill for Claude Code, Cursor, Codex and OpenClaw
- [youtube-transcript-cursor-plugin](https://github.com/tubeagentkit/youtube-transcript-cursor-plugin): YouTube Transcript Cursor plugin bundling the MCP server, skills, commands and a research agent
- [n8n-nodes-getyoutubetranscript](https://github.com/tubeagentkit/n8n-nodes-getyoutubetranscript): YouTube transcript n8n community node, also usable as an AI Agent tool

Comparing options, including other tools: [awesome-youtube-transcripts](https://github.com/tubeagentkit/awesome-youtube-transcripts) lists libraries, hosted APIs, MCP servers and speech-to-text tools for YouTube transcripts.

## License

MIT — see [LICENSE](./LICENSE).
