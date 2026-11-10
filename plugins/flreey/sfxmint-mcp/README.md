# SFXMint MCP Server

Free CC0 sound effects — [describe a sound to find it](https://sfxmint.com), preview, and download MP3 (WAV comes with the download pack). **Free to try with no signup or API key, no attribution.** Agents can [ask by role](https://sfxmint.com/roles), [take one of 18 sets](https://sfxmint.com/sets), or search the library, and get permanent hotlinkable URLs. When nothing in the library fits, the agent tells the user which sound is missing; SFXMint no longer makes new sounds, and new ones join the library from what people search for.

Free use has a daily allowance: without a key, 20 lookups and tool calls and 5 different sound downloads a day per network (a second format or a retry of the same sound is not counted again); a free account's [API key](https://sfxmint.com/dashboard/keys) gives 100 calls and 20 downloads a day (300 a month); a [download pack](https://sfxmint.com/pricing) removes the limits and adds WAV for 30 days, and file URLs returned to its keyed requests carry a signed `g=` good for 48 hours. Past a limit the answer is `429 download_limit` or `call_limit` with a message to pass on to the user. Listening in a browser is never counted. Keep `page_url` in SOUNDS.md, never a URL with `g=`.

- **Endpoint (Streamable HTTP):** `https://sfxmint.com/mcp`
- **Docs:** https://sfxmint.com/api/docs
- **Registry:** published as [`com.sfxmint/sounds`](https://registry.modelcontextprotocol.io/v0/servers?search=sfxmint) on the official MCP Registry
- **License of all audio:** [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) — public domain, commercial use welcome, no attribution required

Sounds are AI-generated or procedurally synthesized and offered under CC0. Audio URLs are immutable, CORS-enabled and free to hotlink. Download files into the project when offline playback is required; preview suitability in the actual app or game.

## Quick start

Claude Code, as a plugin (the MCP server plus the skill below):

```text
/plugin install sfxmint --marketplace sfxmint/sfxmint-mcp
```

On Claude Code before 2.1.275, run `/plugin marketplace add sfxmint/sfxmint-mcp`, then `/plugin install sfxmint@sfxmint`. Or add only the MCP server:

```bash
claude mcp add --transport http sfxmint "https://sfxmint.com/mcp?ref=github-readme"
```

Gemini CLI, as an extension (the MCP server, a context file and the skill):

```bash
gemini extensions install https://github.com/sfxmint/sfxmint-mcp
```

Codex CLI, as a plugin (the MCP server plus the skill):

```bash
codex plugin marketplace add sfxmint/sfxmint-mcp
codex plugin add sfxmint@sfxmint
```

Cursor / generic `mcpServers` config:

```json
{ "mcpServers": { "sfxmint": { "url": "https://sfxmint.com/mcp?ref=github-readme" } } }
```

With a free account's API key (higher daily limits; a download pack lifts them for the key's account):

```bash
claude mcp add --transport http sfxmint "https://sfxmint.com/mcp?ref=github-readme" --header "Authorization: Bearer $SFXMINT_API_KEY"
```

```json
{ "mcpServers": { "sfxmint": { "url": "https://sfxmint.com/mcp?ref=github-readme", "headers": { "Authorization": "Bearer sfx_live_…" } } } }
```

Prefer a skill over a server? This repo also ships an Agent Skill that uses the plain HTTP API — no MCP server required:

```bash
npx skills add sfxmint/sfxmint-mcp -y
```

The agent chooses a role for one event, a set for several events, or structured search for a description or gap. These are task branches, not a required sequence. Library files, other permitted sources and local synthesis can be mixed. The skill includes React / Phaser / plain-HTML integration examples. Source: [`skills/sfxmint/SKILL.md`](skills/sfxmint/SKILL.md).

No agent involved? The [`sfxmint`](https://www.npmjs.com/package/sfxmint) CLI puts the same files in a project directly:

```bash
npx sfxmint add coin jump hit
```

It writes the audio plus a `sounds.json` manifest recording each file's source URL, SHA-256 and license, and a `SOUNDS.md` table linking each sound's page, and ships a small Web Audio runtime (`createSoundboard`) for first-gesture unlock, overlapping cues and a persisted mute. Source: [sfxmint/sfxmint-npm](https://github.com/sfxmint/sfxmint-npm).

## Tutorials

- **[Add sound effects to a Remotion video with SFXMint MCP](examples/remotion/README.md)** — an 18-second runnable example with four timed cues, a finished video, a copy-and-paste agent prompt, and a read-only MCP check. [中文教程](examples/remotion/README.zh-CN.md).

## Tools

| Tool | What it does |
|---|---|
| `get_role_sound` | Ask by event — `button-click`, `purchase-success`, `error`, `coin`, `notification`. Returns a file-checked candidate plus alternates; plain-English aliases work |
| `get_sound_set` | Candidates grouped by event and style (18 sets: `ui-crisp`, `retro-game`, `checkout`, `platformer`, `ai-coding-tool`, …) |
| `search_sounds` | Free-text retrieval with explicit duration, loop and format requirements; hard constraints can produce no candidates. When nothing fits, `user_message` is one line for the user saying which sound the library lacks |
| `get_sound` | Full metadata for one sound (incl. a short description, measured acoustics, license) |

When nothing fits, pass `user_message` on to the user and list the sound under a Missing heading in `SOUNDS.md`. The four library tools are all there is for new users: SFXMint no longer makes new sounds. An account that already has credits or a plan still sees `generate_sound` and `get_generation` with its API key. Game kits (projects of many sounds) closed on 2026-10-20; their tools answer `tool_retired`. `get_job` and `POST /api/v1/generate` stay retired.

## Requirements, processing and acceptance

Use REST structured search (`response=structured&limit=3`) or the matching MCP parameters to pass required duration, loop and format explicitly. Check returned requirements; do not substitute `near_matches`. When nothing matches every word, `closest` lists the nearest sounds that meet every hard requirement, each with `missing_terms`, and `library_fit` says how well the library covers the request. Scores and match types describe ranking, not listening confidence. Legacy `loopable` does not prove a seamless loop.

Sets accept `format=wav|mp3`: `download_urls` follows the requested format, legacy `urls` stays MP3, and `missing_roles` identifies incomplete sets. File decoding and hashes do not certify scene suitability.

Task-permitted trimming, filtering and level changes are allowed. Retain originals, source URLs, license, processing recipes and new file hashes; re-measure requirements and preview the result. Changed bytes and new scenes do not inherit the original acceptance. Other sources and local synthesis remain separate, task-authorized choices.

Use URLs returned by the live API, without inventing or rewriting them. See the [API docs](https://sfxmint.com/api/docs), [Phaser guide](https://sfxmint.com/guides/phaser-web-game-sounds), [React guide](https://sfxmint.com/guides/react-app-sounds), and [download example](https://sfxmint.com/examples/download-sounds.mjs).

## Rate limits & fair use

- Without a key: 20 lookups and tool calls and 5 sound downloads a day per network; a free account's API key: 100 calls and 20 downloads a day
- Hotlinking is allowed and encouraged; files are served with long-lived immutable caching

## Contact

hello@sfxmint.com · https://sfxmint.com
