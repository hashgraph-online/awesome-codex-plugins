# BulkTranscripts MCP server

YouTube transcripts for AI agents — one video, a whole channel, or a playlist —
plus YouTube search and free new-upload tracking, through one hosted
[MCP](https://modelcontextprotocol.io) server. No local process, no `yt-dlp`
to keep fresh, no IP blocks to fight: extraction, proxy rotation and PO-token
handling all happen server-side.

- **Endpoint:** `https://bulktranscripts.co/mcp` (Streamable HTTP)
- **Auth:** OAuth (sign in with Google, 30 free credits, no card) or an API key as a Bearer token
- **Registry:** [`co.bulktranscripts/youtube`](https://registry.modelcontextprotocol.io/v0/servers?search=co.bulktranscripts) · [Glama connector](https://glama.ai/mcp/connectors/co.bulktranscripts/youtube)
- **Setup docs:** https://bulktranscripts.co/docs#mcp · **REST API:** https://bulktranscripts.co/docs

## Install

### Claude Code

```bash
claude mcp add --transport http bulktranscripts https://bulktranscripts.co/mcp
```

Run `/mcp` and pick **bulktranscripts** to sign in. This repo is also a Claude Code
plugin (server + skill):

```bash
/plugin marketplace add pratie/bulktranscripts-mcp
/plugin install bulktranscripts@bulktranscripts
```

### Claude (web and desktop)

Settings → Connectors → **Add custom connector** → URL `https://bulktranscripts.co/mcp`.
Claude opens the Google sign-in; credits then follow your account.

### ChatGPT

Settings → Apps & Connectors → Developer mode → **Create** → URL
`https://bulktranscripts.co/mcp`, authentication **OAuth**.

### Gemini CLI

```bash
gemini extensions install https://github.com/pratie/bulktranscripts-mcp
```

Sign in with Google when Gemini CLI opens the OAuth page on first use.

### Cursor, VS Code, Windsurf, any client with a JSON config

```json
{
  "mcpServers": {
    "bulktranscripts": {
      "type": "http",
      "url": "https://bulktranscripts.co/mcp"
    }
  }
}
```

OAuth-capable clients start the sign-in on the first request. Clients that cannot
do OAuth send an API key instead — create one free at
https://bulktranscripts.co/app?tab=mcp (Google sign-in, 30 free credits) or use
the license key from a credit pack:

```json
{
  "mcpServers": {
    "bulktranscripts": {
      "type": "http",
      "url": "https://bulktranscripts.co/mcp",
      "headers": { "Authorization": "Bearer ${BULKTRANSCRIPTS_API_KEY}" }
    }
  }
}
```

Clients that cannot send headers can append `?key=YOUR_KEY` to the URL.

## What the agent can do

| Tool | What it does | Cost |
| --- | --- | --- |
| `get_transcript` | Full transcript of one YouTube (or TikTok) video as clean text with metadata; timestamped segments on request. | 1 credit, free on repeat reads from your library |
| `get_transcripts` | Up to 20 videos in one call; videos without captions are reported per item and never fail the batch. | 1 credit per new transcript |
| `search_youtube` | Search YouTube for videos, channels or playlists by keyword. | 1 credit |
| `search_channel` | Search inside one channel's uploads for a topic. | 1 credit |
| `get_channel_videos` | List up to 1,000 of a channel's videos (id, title, duration, URL). | 1 credit |
| `get_playlist_videos` | List up to 1,000 videos of a public or unlisted playlist, in order. | 1 credit |
| `get_latest_videos` | A channel's newest uploads with publish dates, from RSS. | **Always free** |
| `start_bulk_extract` | Fetch every transcript of a channel, playlist or video URL (up to 1,000) as a background job; returns a `run_id` at once. | Listing free, 1 credit per new transcript |
| `get_bulk_status` | Progress of a bulk job with `check_again_in_seconds`, so agents poll at the right pace. | Free |
| `list_bulk_results` | Paged per-video outcomes of a bulk job (id, title, channel, duration, word count, status). Text stays behind `get_transcript`, free once in the library. | Free |

Every tool is read-only: nothing on YouTube or in your account is modified or
deleted. Transcripts land in your library once and are free to re-read forever, in
any format, so agents that revisit the same videos do not burn credits.
`get_latest_videos` is free on purpose: poll it to detect new uploads, then spend a
credit only on what is actually new. For anything larger than about 20 videos,
`start_bulk_extract` runs the whole channel or playlist on the server while the
agent polls `get_bulk_status`.

### Example prompts

> Summarise the last 10 videos from @veritasium and tell me which ones cover quantum mechanics.

> Find talks about founder mode on the Y Combinator channel and pull the transcripts.

> Watch @simonwillison for new uploads and transcribe anything about local models.

## How auth works

An unauthenticated request to `/mcp` answers `401` with a `WWW-Authenticate` challenge
pointing at `/.well-known/oauth-protected-resource/mcp`, which is how MCP clients
know to start the OAuth flow (dynamic client registration is supported). The same
`Authorization` header accepts an API key (`bt_ak_…`) or a license key, with or
without the `Bearer ` prefix.

## Pricing

Signing in includes 30 free credits. After that, one-time packs: $4.99 / 200
credits, $14.99 / 1,200, $29 / 5,000. No subscription; credits never expire.
Details at https://bulktranscripts.co/#pricing.

## Repo layout

| File | Used by |
| --- | --- |
| `.mcp.json` | Claude Code plugin config (hosted endpoint, OAuth) |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Claude Code plugin marketplace |
| `plugin.json`, `mcp.json` | Cursor / agent-plugins.org |
| `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, `assets/icon.png` | Codex plugin |
| `skills/youtube-transcripts/` | Agent skill for the MCP tools (the REST API version is at [pratie/youtube-transcript-skill](https://github.com/pratie/youtube-transcript-skill)) |
| `gemini-extension.json` | Gemini CLI extension (hosted endpoint, OAuth) |
| `server.json` | Official MCP registry manifest |

## Links

- Product: https://bulktranscripts.co
- MCP page: https://bulktranscripts.co/youtube-mcp-server
- API docs: https://bulktranscripts.co/docs · OpenAPI: https://bulktranscripts.co/openapi.json
- Privacy: https://bulktranscripts.co/privacy · Terms: https://bulktranscripts.co/terms
- Contact: hello@bulktranscripts.co

## License

MIT — see [LICENSE](LICENSE). This repo holds the manifests, plugin and skill for the
hosted server; the extraction service itself is operated at bulktranscripts.co.
