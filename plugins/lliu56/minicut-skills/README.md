# MiniCut skills

Agent skills for Claude Code, Codex, Cursor and any agent that reads SKILL.md.

| Skill | What it does | Install |
|---|---|---|
| `miniapi-video` | Video, image and audio models on one MiniAPI key. Quotes the price first, free. | `npx skills add lliu56/minicut-skills --skill miniapi-video` |
| `minicut-film-studio` | Installs the MiniCut CLI and makes a short film from an idea: story, shots, takes, voice, music, edit. | `npx skills add lliu56/minicut-skills --skill minicut-film-studio` |

## Install as a plugin

Claude Code:

```
claude plugin marketplace add lliu56/minicut-skills
claude plugin install minicut@minicut
```

Codex:

```
codex plugin marketplace add lliu56/minicut-skills
codex plugin add minicut@minicut
```

Cursor: the plugin manifest is in `.cursor-plugin/plugin.json`.

Gemini CLI:

```
gemini extensions install https://github.com/lliu56/minicut-skills
```

## MCP server

`@minicut/mcp` lets any MCP client check setup, start a project and get the next step. Source in [`mcp/`](mcp/).

```
claude mcp add minicut -- npx -y @minicut/mcp
```

## CLI

Mac or Linux:

```
curl -fsSL https://minicut.ai/install.sh | bash -s -- --region global
```

Windows:

```
curl -fsSL https://minicut.ai/install.cmd -o install.cmd && install.cmd
```

Seedance 2.5 on MiniAPI: $0.16 / s at 480p, $0.35 / s at 720p. A job that fails is not charged.
Prices for every model: https://api.minicut.ai/pricing

## Data

`minicut-film-studio` and the MiniCut CLI send your prompts and uploads to minicut.ai to make your video. `miniapi-video` sends requests to api.minicut.ai. Privacy policy: https://www.minicut.ai/legal/privacy

MIT license.
