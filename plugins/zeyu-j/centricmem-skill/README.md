# CentricMem

**One library. Every agent. Every desk.**

A hosted librarian for AI agents. Capture stays in the agent you already use. CentricMem organises and retrieves — Cursor, Claude Code, Codex, Copilot, Kiro, Kilo, CodeBuddy, Kimi Code, and the next one share the same shelf.

This repository is **one package**: [Agent Skills](https://agentskills.io) `SKILL.md` plus an [Agent Plugins 1.0](https://agent-plugins.org) bundle (`plugin.json` + `skills/` + `mcp.json`). Install it once from GitHub; each client uses its own command. Do not paste keys or marketplace JSON into chat.

## Install

Paste this to the agent (one line):

```
Install CentricMem from zeyu-j/centricmem-skill. If CLI is blocked, send https://centricmem.com/login?signup=1 — never paste keys.
```

If the shell works, a terminal in the project can run:

```bash
npx --yes skills add zeyu-j/centricmem-skill --skill centricmem-agent -y
```

(omit `-g` — some agents, including PromptScript, have no user-wide skills dir.)

Same GitHub repo as a plugin marketplace:

| Client | Add this repo, then install |
| --- | --- |
| Cursor | Plugins → Team Marketplaces → Import from Repo `zeyu-j/centricmem-skill`, or `npx skills add` above |
| Claude Code | `/plugin marketplace add zeyu-j/centricmem-skill` then `/plugin install centricmem-skill@centricmem` |
| CodeBuddy / WorkBuddy | `codebuddy plugin marketplace add zeyu-j/centricmem-skill` then `/plugin install centricmem-skill@centricmem` |
| Kimi Code | `/plugins install https://github.com/zeyu-j/centricmem-skill` (Custom). Catalog: `/plugins marketplace https://raw.githubusercontent.com/zeyu-j/centricmem-skill/main/.kimi-plugin/marketplace.json`. Set `CENTRICMEM_API_KEY` for host MCP. |
| Dify | Marketplace listing pending review. Source: `zeyu-j/centricmem-dify`. Or attach MCP `https://mem.centricmem.com/mcp` with the same agent key. |
| Codex | `codex plugin marketplace add https://github.com/zeyu-j/centricmem-skill.git` then install **centricmem-skill** in Plugins |
| Copilot CLI | `copilot plugin marketplace add zeyu-j/centricmem-skill` then `copilot plugin install centricmem-skill` |
| Kiro | Powers → Add Custom Power → GitHub `https://github.com/zeyu-j/centricmem-skill` |
| Grok Bot | Paste the one-liner. If CLI is blocked, add `https://mem.centricmem.com/mcp` in that bot’s MCP settings (key from Keys, never in chat). |
| SkillKit | `skillkit add https://centricmem.com` or `skillkit add zeyu-j/centricmem-skill` |
| skills.sh / SkillMD | `npx skills add` above, or `skillmd add zeyu-j/centricmem-skill` |

Then keep talking. After install, if `cm_*` tools are missing the agent sends signup or a `/connect?device=` link. You do not paste chats, tokens, or CLI.

Hosted librarian: [centricmem.com](https://centricmem.com). Sign up is open. Host MCP: `https://mem.centricmem.com/mcp`. CLI agents send a `/connect?device=` link. Agents that cannot run a CLI send https://centricmem.com/login?signup=1 and the human adds MCP in that agent’s settings. Never paste keys in chat.

## How you use it

1. Keep talking where you already work. The agent’s own memories stay on. It says **once** which key this chat is using. Extra grants: tick shelves on **Keys**. Default opens every shelf.
2. If the library looks empty, the agent offers **once** to file notes you already have as cards. Capture stays. You may skip. It is not a dump of every chat.
3. When work is real, the agent files a Markdown card and keeps this chat’s transcript in object storage — you do not have to say wrap up. Closing the tab does not file; it files before it stops. Ask it to keep a file and write a card; a folder of originals is one import. Archive zip on the website is optional if you already packed one. If your Skill is behind this repo, the agent refreshes it with `npx skills add` (the current chat still uses the old copy). Plugin installs update via that client’s plugin UI.
4. Later, ask the agent — or log in to search and download originals. There is no Inbox: file into a named shelf. Leftover shelves (including leftover `unclassified`): the agent copies onto another shelf (`cm_copy`) then **deletes** the old one (`cm_delete`) — it does not download originals to this computer, and there is no restore warehouse. To move a **subset** of cards, the agent uses `cm_move` (default key). Extra keys cannot.

You do not run a librarian on this machine. You do not `setup --bootstrap`.

## What this repo is

This repository is the **Skill**: how agents talk to the hosted librarian.

- [`skills/centricmem-agent/SKILL.md`](./skills/centricmem-agent/SKILL.md) — session loop ([Agent Skills](https://agentskills.io/specification) frontmatter)
- [`skills/centricmem-agent/REFERENCE.md`](./skills/centricmem-agent/REFERENCE.md) — search, show, sweep, copy, move selected cards, delete leftover shelves
- [`plugin.json`](./plugin.json) + [`mcp.json`](./mcp.json) — portable Agent Plugins 1.0 package
- [`.cursor-plugin/marketplace.json`](./.cursor-plugin/marketplace.json) — Cursor team marketplace
- [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) — Claude Code marketplace
- [`.codebuddy-plugin/marketplace.json`](./.codebuddy-plugin/marketplace.json) — CodeBuddy / WorkBuddy marketplace (`codebuddy plugin marketplace add zeyu-j/centricmem-skill`)
- [`.kimi-plugin/plugin.json`](./.kimi-plugin/plugin.json) — Kimi Code Custom install from this GitHub URL
- Dify is a separate tool plugin: [zeyu-j/centricmem-dify](https://github.com/zeyu-j/centricmem-dify) (not this Skill repo)
- [`.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json) — Codex marketplace
- [`.github/plugin/marketplace.json`](./.github/plugin/marketplace.json) — Copilot CLI marketplace
- [`.kiro/plugins/marketplace.json`](./.kiro/plugins/marketplace.json) — Kiro pin-sync catalog

It is not the librarian, not the CLI source, and not a self-hosted kit. One public skill: `centricmem-agent`.

## License

[PolyForm Noncommercial 1.0.0](./LICENSE) — attribution required; no commercial use.
